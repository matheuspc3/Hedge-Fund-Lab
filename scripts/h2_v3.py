"""H2 v3 (Amendment 10): replay do componente congelado e auditoria do Risk.

``FROZEN_COMPONENT_REPLAY = TECHNICAL_V2``: o Technical da v3 é byte-idêntico ao
da v2, então toda resposta Technical v2 já observada é reaproveitada quando a
requisição v3 tem a MESMA ``LLMCallRequest.identity()`` (sessão, analista,
prompts, modelo, opções, schema) na evidência v2 da mesma fase e repetição.
Portfolio: o mesmo, só por identidade exata (ex.: VENDA auto-aprovada). Risk:
nunca vem da v2 — o system prompt mudou, a identidade nunca casa.

Dois encaixes, um por família de runner:

- ``FrozenReplayClient`` embrulha o cliente do participante (Hardening, B0,
  hardening dirigido);
- ``seed_bank`` pré-carrega o ``CallBank`` de ``run_cal_a`` (CAL-A, Sequential,
  Stress), que já casa por (repetição, identity_digest).
"""

import hashlib
import json
import subprocess
import sys
from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agents.feature_semantics import TECHNICAL_SYSTEM_PROMPT_V2_SHA256  # noqa: E402
from src.agents.llm_client import (  # noqa: E402
    LLMCallMetadata,
    LLMClient,
    current_call_telemetry,
)
from src.agents.llm_trace import (  # noqa: E402
    STAGE_PORTFOLIO_MANAGER,
    STAGE_RISK_MANAGER,
    STAGE_TECHNICAL_ANALYST,
    STAGE_UNDECLARED,
    LLMCallRecord,
    LLMCallRequest,
    _jsonable_options,
    load_trace,
    schema_digest,
    schema_name,
    session_key,
)
from src.agents.risk_contract import (  # noqa: E402
    RISK_SYSTEM_PROMPT_V2_SHA256,
    audit_risk_rationale,
    gate_counts,
)
from src.artifacts import canonical_json  # noqa: E402

FROZEN_STAGES = frozenset({STAGE_TECHNICAL_ANALYST, STAGE_PORTFOLIO_MANAGER})
#: Arquivos do checker do Risk, congelados por blob antes da primeira chamada v3.
CHECKER_FILES = ("src/agents/risk_contract.py", "scripts/h2_v3.py")


def git_blob(path: str) -> str:
    return subprocess.run(["git", "rev-parse", f"HEAD:{path}"], cwd=ROOT, capture_output=True, text=True,
                          check=True).stdout.strip()


def frozen_index(paths: Iterable[Path]) -> dict[str, LLMCallRecord]:
    """identity_digest -> registro v2 (Technical/Portfolio, status ok)."""
    index: dict[str, LLMCallRecord] = {}
    for path in paths:
        for record in load_trace(Path(path).read_bytes()):
            if record.status != "ok" or record.request.stage not in FROZEN_STAGES:
                continue
            prior = index.setdefault(record.request.identity_digest, record)
            if prior.validated_response != record.validated_response:
                raise ValueError(f"v2 evidence has two responses for one request: {record.call_id}")
    return index


def by_replicate(summary: str, key: str) -> dict[int, dict[str, LLMCallRecord]]:
    """Runners com banco: {repetição: índice} a partir do summary v2 da fase."""
    items = json.loads((ROOT / summary).read_text(encoding="utf-8"))[key]
    paths: dict[int, list[Path]] = {}
    for item in items:
        paths.setdefault(int(item["replicate"]), []).append(ROOT / item["runs_root"] / item["run_dir"] / "llm_calls.jsonl")
    return {rep: frozen_index(p) for rep, p in sorted(paths.items())}


def by_state(evidence: str) -> dict[tuple[str, int], dict[str, LLMCallRecord]]:
    """Hardening/B0 v2: {(state_id, repetição): índice}."""
    root = ROOT / evidence
    rows = [json.loads(x) for x in (root / "decisions.jsonl").read_text(encoding="utf-8").splitlines() if x]
    return {(r["state_id"], r["repetition"]): frozen_index([root / r["trace_file"]]) for r in rows}


def _evidence(record: LLMCallRecord) -> dict[str, Any]:
    # ponytail: usage fica None de propósito: tokens de replay não foram gastos na v3.
    return {"provider_response_id": record.provider_response_id, "resolved_model": record.resolved_model,
            "finish_reason": record.finish_reason, "raw_response": record.raw_response}


def seed_bank(bank: Any, frozen: Mapping[int, Mapping[str, LLMCallRecord]]) -> int:
    """Pré-carrega o ``CallBank`` com as respostas v2 por (repetição, identity_digest)."""
    for replicate, index in frozen.items():
        for digest, record in index.items():
            bank.entries[(replicate, digest)] = {"response": record.validated_response, "evidence": _evidence(record),
                                                 "first_use": {"frozen_v2_call_id": record.call_id}, "frozen": True}
    return sum(len(i) for i in frozen.values())


class FrozenReplayClient(LLMClient):
    """Responde do componente congelado por identidade exata; o resto vai ao cliente embrulhado.

    ``required`` lista estágios que NÃO podem ir ao provedor (hardening dirigido:
    nenhuma chamada Technical nova); requisição sem par v2 nesses estágios falha.
    """

    def __init__(self, client: LLMClient, frozen: Mapping[str, LLMCallRecord], *, provider: str, model: str,
                 uses: list[dict[str, Any]], context: Mapping[str, Any], required: frozenset[str] = frozenset()):
        super().__init__()
        self.client, self.frozen, self.provider, self.model = client, frozen, provider, model
        self.uses, self.context, self.required = uses, dict(context), required
        self._session: str | None = None

    def begin_session(self, session: Any) -> None:
        self._session = session_key(session)
        super().begin_session(session)

    async def generate(self, system_prompt: str, user_prompt: str, response_schema: type[BaseModel] | None = None,
                       options: dict[str, Any] | None = None, *, metadata: LLMCallMetadata | None = None):
        declared = metadata or LLMCallMetadata(stage=STAGE_UNDECLARED)
        request = LLMCallRequest(
            stage=declared.stage, analyst_id=declared.analyst_id, decision_session=str(self._session),
            provider=self.provider, requested_model=self.model, system_prompt=system_prompt,
            user_prompt=user_prompt, response_schema=schema_name(response_schema),
            response_schema_sha256=schema_digest(response_schema), requested_options=_jsonable_options(options))
        use = {**self.context, "decision_session": self._session, "stage": request.stage,
               "analyst_id": request.analyst_id, "identity_digest": request.identity_digest}
        hit = self.frozen.get(request.identity_digest)
        if hit is not None:
            slot = current_call_telemetry()
            if slot is not None:
                for name, value in _evidence(hit).items():
                    setattr(slot, name, value)
            self.uses.append({**use, "source": "frozen_v2", "frozen_v2_call_id": hit.call_id})
            payload = hit.validated_response
            return payload if response_schema is None else response_schema.model_validate(payload)
        if request.stage in self.required:
            raise RuntimeError(f"no identical v2 {request.stage} request for {self._session}; live call refused")
        response = await self.client.generate(system_prompt, user_prompt, response_schema, options, metadata=metadata)
        self.uses.append({**use, "source": "live"})
        return response


# ── Auditorias (a partir dos traces publicados) ──────────────────


def _sha(value: Any) -> str:
    return hashlib.sha256((value if isinstance(value, str) else canonical_json(value)).encode("utf-8")).hexdigest()


def replay_audit(pairs: Iterable[tuple[LLMCallRecord, Mapping[str, LLMCallRecord]]]) -> dict[str, Any]:
    """Prova de igualdade: cada chamada v3 Technical/Portfolio contra o índice v2 da sua repetição.

    ``replayed`` = identidade v2 idêntica E mesma resposta (provider_response_id,
    raw e validada). ``live`` = sem par v2. ``mismatch`` = par v2 com resposta
    diferente (não deveria existir).
    """
    out: dict[str, Counter] = {"replayed": Counter(), "live": Counter(), "mismatch": Counter()}
    prompts = Counter()
    for record, index in pairs:
        stage = record.request.stage
        if stage == STAGE_TECHNICAL_ANALYST:
            prompts[record.request.system_prompt_sha256] += 1
        if stage not in FROZEN_STAGES or record.status != "ok":
            continue
        v2 = index.get(record.request.identity_digest)
        if v2 is None:
            out["live"][stage] += 1
        elif (v2.provider_response_id, _sha(v2.raw_response or ""), _sha(v2.validated_response)) == (
                record.provider_response_id, _sha(record.raw_response or ""), _sha(record.validated_response)):
            out["replayed"][stage] += 1
        else:
            out["mismatch"][stage] += 1
    return {**{k: dict(v) for k, v in out.items()},
            "technical_system_prompts": dict(prompts),
            "technical_prompt_v2_byte_identical": set(prompts) <= {TECHNICAL_SYSTEM_PROMPT_V2_SHA256},
            "proof": "identity_digest + provider_response_id + sha256(raw_response) + sha256(validated_response)"}


def risk_audit(records: Iterable[LLMCallRecord]) -> dict[str, Any]:
    """Checker do Risk sobre cada resposta LLM ÚNICA (identidade + resposta do provedor)."""
    seen: dict[tuple[str, str | None], LLMCallRecord] = {}
    for r in records:
        if r.request.stage == STAGE_RISK_MANAGER and r.status == "ok":
            seen.setdefault((r.request.identity_digest, r.provider_response_id), r)
    counts, verdicts, flagged = Counter(), Counter(), []
    prompts = Counter(r.request.system_prompt_sha256 for r in seen.values())
    for r in seen.values():
        v = r.validated_response
        audit = audit_risk_rationale(v["analysis"], v["verdict"], json.loads(r.request.user_prompt))
        verdicts[v["verdict"]] += 1
        for gate, hit in gate_counts(audit).items():
            counts[gate] += hit
        if audit:
            flagged.append({"call_id": r.call_id, "decision_session": r.request.decision_session,
                            "verdict": v["verdict"], "analysis": v["analysis"], "findings": audit})
    n = len(seen)
    return {"risk_llm_responses": n, "verdicts": dict(verdicts), "risk_system_prompts": dict(prompts),
            "risk_prompt_v2_only": set(prompts) <= {RISK_SYSTEM_PROMPT_V2_SHA256},
            **{gate: counts[gate] for gate in ("V3-R1", "V3-R2", "V3-R3")},
            "rates": {gate: (counts[gate] / n if n else None) for gate in ("V3-R1", "V3-R2", "V3-R3")},
            "flagged": flagged}
