"""DEV_SMOKE técnico da Gemini API nativa — NÃO é execução científica.

Prova, com UMA chamada real por papel (técnico, risco, portfólio), que o
contrato implementado em ``GeminiLLMClient`` funciona contra a API real:
transporte nativo, opções de geração, saída estruturada e proveniência.

Regras que este script obedece por construção:

- entrada é só o estado sintético ``H_SYN_VERSION = 1`` (nenhuma data real,
  nenhum H_real, nenhuma barra futura, nenhum retorno);
- ``thinking_level=low`` é valor de **transporte**, não escolha científica;
- o conteúdo da decisão (COMPRA/VENDA/MANTER) não é avaliado;
- a credencial vem só de ``GEMINI_API_KEY`` (ambiente ou ``.env`` local,
  ignorado pelo git) e nunca é impressa nem gravada; cabeçalhos HTTP nunca
  entram na evidência;
- a evidência guarda proveniência e hashes, não o texto das respostas.

Uso: ``python scripts/dev_smoke_gemini.py`` — grava
``docs/evidence/provider_runtime/gemini-3.8-flash_dev_smoke_<UTC>.json``.
"""

import asyncio
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agents.features import canonical_prompt_json  # noqa: E402
from src.agents.llm_client import (  # noqa: E402
    GeminiLLMClient,
    MockLLMClient,
    RetryingLLMClient,
    _http_json_transport,
)
from src.agents.llm_trace import RecordingLLMClient, schema_digest  # noqa: E402
from src.agents.participant import LLMParticipant, classify_decision  # noqa: E402
from src.agents.portfolio_manager import (  # noqa: E402
    SIZING_MODE_QUALITATIVE,
    PortfolioConfig,
    create_portfolio_manager_node,
)
from src.agents.risk_manager import RiskConfig, create_risk_manager_node  # noqa: E402
from src.agents.state import (  # noqa: E402
    PortfolioAction,
    RiskVerdict,
    TechnicalSignal,
)
from src.agents.technical_analyst import (  # noqa: E402
    AnalystEnsembleConfig,
    create_technical_analyst_ensemble_node,
)
from src.experiments.hardening import (  # noqa: E402
    H_SYN_PAYLOAD_DIGESTS,
    H_SYN_VERSION,
    frozen_observation,
    synthetic_states,
)

PROVIDER = "gemini"
MODEL = "gemini-3.8-flash"
#: Valores de TRANSPORTE do smoke. ``low`` não é o nível científico do H2.
OPTIONS = {"temperature": 1.0, "thinking_level": "low", "max_output_tokens": 8192}
STATE_NAME = "steady_uptrend"
CAPITAL = 100_000.0
EVIDENCE_DIR = ROOT / "docs" / "evidence" / "provider_runtime"


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_key() -> None:
    """Só ``GEMINI_API_KEY``, só para este processo, nunca impressa."""
    if not os.environ.get("GEMINI_API_KEY"):
        value = dotenv_values(ROOT / ".env").get("GEMINI_API_KEY")
        if value:
            os.environ["GEMINI_API_KEY"] = value
    if not os.environ.get("GEMINI_API_KEY"):
        sys.exit("BLOCKED — NO API KEY")


class SanitizedTransport:
    """Transporte real que guarda só o ``generationConfig`` enviado.

    Cabeçalhos (onde vive a credencial) nunca são lidos nem guardados; o
    JSON Schema enviado entra só como hash.
    """

    def __init__(self, timeout: float) -> None:
        self.timeout = timeout
        self.sent: list[dict[str, Any]] = []

    def __call__(self, method: str, url: str, headers: dict[str, str], body: dict[str, Any]):
        config = dict(body.get("generationConfig", {}))
        schema = config.pop("responseJsonSchema", None)
        config["responseJsonSchema_sha256"] = (
            None if schema is None else sha256(canonical_prompt_json(schema))
        )
        attempt: dict[str, Any] = {"generation_config": config}
        self.sent.append(attempt)
        try:
            raw = _http_json_transport(method, url, headers, body, self.timeout)
        except Exception as exc:
            # Tipo, status e começo da mensagem do provedor: o corpo de erro
            # da Gemini não carrega credencial, e cabeçalhos nunca são lidos.
            attempt["outcome"] = {
                "type": type(exc).__name__,
                "status": getattr(exc, "status", None),
                "retry_after": getattr(exc, "retry_after", None),
                "message": str(exc)[:300],
            }
            raise
        try:
            payload = json.loads(raw)
        except ValueError:
            attempt["outcome"] = {"type": "http_200", "body_json": False}
        else:
            usage = payload.get("usageMetadata") if isinstance(payload, dict) else None
            attempt["outcome"] = {
                "type": "http_200",
                "body_json": True,
                "candidate_count": len(payload.get("candidates") or [])
                if isinstance(payload, dict)
                else None,
                "usage_keys": sorted(usage) if isinstance(usage, dict) else None,
            }
        return raw


def frozen_state():
    state = next(s for s in synthetic_states() if s.state_id.endswith(f":{STATE_NAME}"))
    history = state.history
    observation = frozen_observation(state, CAPITAL)
    builder = LLMParticipant(state.ticker, llm_client=MockLLMClient())  # sem rede
    close = float(history["fechamento"].iloc[-1])
    agent_state = builder._agent_state(observation, history, CAPITAL, close)
    payload = canonical_prompt_json(
        {
            "features": agent_state["features"],
            "recent_volatility": agent_state["recent_volatility"],
        }
    )
    digest = sha256(payload)
    if digest != H_SYN_PAYLOAD_DIGESTS[STATE_NAME]:
        sys.exit("H_syn payload digest mismatch: refusing to smoke an unfrozen state")
    return state, agent_state, digest


#: Fixtures sintéticas que forçam o ramo LLM de risco e de portfólio. Não
#: vêm do modelo: o objetivo é exercitar cada papel, não encadear decisões.
FIXTURE_SIGNAL = TechnicalSignal(
    signal="COMPRA", justification="fixture sintética do DEV_SMOKE", confidence=0.6
)
FIXTURE_APPROVAL = RiskVerdict(
    verdict="APROVADO", analysis="fixture sintética do DEV_SMOKE", risk_metrics={}
)


async def run_role(role: str, node, state: dict[str, Any]) -> dict[str, Any]:
    try:
        output = await node(state)
        return {"output": output, "exception": None}
    except Exception as exc:  # registrado como evidência, nunca engolido em silêncio
        return {"output": None, "exception": exc}


def git_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def main() -> None:
    load_key()
    started = datetime.now(timezone.utc)
    state, agent_state, digest = frozen_state()

    transport = SanitizedTransport(timeout=120.0)
    gemini = GeminiLLMClient(model=MODEL, transport=transport)
    recorder = RecordingLLMClient(
        RetryingLLMClient(gemini, max_attempts=3, base_delay=0.5),
        provider=PROVIDER,
        requested_model=MODEL,
    )
    recorder.begin_session(state.history.index[-1])

    technical = create_technical_analyst_ensemble_node(
        recorder,
        AnalystEnsembleConfig(
            analyst_count=1,
            consensus_threshold=0.6,
            require_all_votes=True,
            temperature_min=OPTIONS["temperature"],
            temperature_max=OPTIONS["temperature"],
        ),
        OPTIONS,
    )
    # Volatilidade 0.069, drawdown 0, concentração 0: nenhuma regra dura veta,
    # e o sinal é COMPRA — o único caminho que consulta o LLM de risco.
    risk = create_risk_manager_node(recorder, RiskConfig(), OPTIONS)
    portfolio = create_portfolio_manager_node(
        recorder, PortfolioConfig(sizing_mode=SIZING_MODE_QUALITATIVE), OPTIONS
    )

    roles = {
        "technical_analyst": (technical, dict(agent_state), TechnicalSignal),
        "risk_manager": (
            risk,
            {**agent_state, "technical_signal": FIXTURE_SIGNAL},
            RiskVerdict,
        ),
        "portfolio_manager": (
            portfolio,
            {**agent_state, "technical_signal": FIXTURE_SIGNAL, "risk_verdict": FIXTURE_APPROVAL},
            PortfolioAction,
        ),
    }

    results: dict[str, Any] = {}
    for role, (node, role_state, schema) in roles.items():
        before = len(recorder.records)
        sent_before = len(transport.sent)
        outcome = asyncio.run(run_role(role, node, role_state))
        records = recorder.records[before:]
        exc = outcome["exception"]
        output = outcome["output"] or {}
        record = records[0] if len(records) == 1 else None
        cause = None
        if exc is not None:
            cause = classify_decision(
                consensus=None, risk_verdict=None, risk_source=None, risk_rule=None,
                portfolio_action=None, portfolio_rule=None, observed_weight=0.0,
                long_target_weight=1.0, failures=(exc,),
            )
        sent = transport.sent[sent_before:]
        entry: dict[str, Any] = {
            "llm_call_count": len(records),
            "http_attempts": len(sent),
            "schema": schema.__qualname__,
            "schema_sha256": schema_digest(schema),
            "sent_generation_config": sent[-1]["generation_config"] if sent else None,
            "http_attempt_outcomes": [attempt.get("outcome") for attempt in sent],
            "exception": None if exc is None else {"type": type(exc).__name__, "cause": cause},
        }
        if record is not None:
            entry.update(
                {
                    "status": record.status,
                    "attempt_count": record.attempt_count,
                    "error_type": record.error_type,
                    "error_message": record.error_message,
                    "requested_options": dict(record.request.requested_options),
                    "transport_options": dict(record.transport_options),
                    "provider_endpoint": record.provider_endpoint,
                    "provider_response_id": record.provider_response_id,
                    "resolved_model": record.resolved_model,
                    "finish_reason": record.finish_reason,
                    "token_usage": None if record.token_usage is None else dict(record.token_usage),
                    "raw_response_sha256": (
                        None if record.raw_response is None else sha256(record.raw_response)
                    ),
                    "validated": record.status == "ok" and record.validated_response is not None,
                    "duration_ms": round(record.duration_ms, 1),
                    "user_prompt_sha256": record.request.user_prompt_sha256,
                    "system_prompt_sha256": record.request.system_prompt_sha256,
                }
            )
        # Prova de ramo e contrato, sem julgar o conteúdo.
        if role == "technical_analyst":
            consensus = output.get("technical_consensus")
            entry["branch"] = {"valid_votes": None if consensus is None else consensus.valid_votes}
        elif role == "risk_manager":
            entry["branch"] = {
                "risk_source": output.get("risk_source"),
                "risk_rule": output.get("risk_rule"),
            }
        else:
            action = output.get("portfolio_action")
            entry["branch"] = {
                "portfolio_source": output.get("portfolio_source"),
                "portfolio_rule": output.get("portfolio_rule"),
                # Contrato de direção: decisão ∈ {sinal aprovado, MANTER}.
                "decision": None if action is None else action.decision,
                "direction_respected": None
                if action is None
                else output.get("portfolio_rule") is None,
            }
        results[role] = entry

    evidence = {
        "kind": "DEV_SMOKE",
        "scientific": False,
        "statement": (
            "Technical smoke of the native Gemini runtime. Not a scientific run, "
            "not B0, no thinking_level selection, no financial performance used."
        ),
        "timestamp_utc": started.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "git_commit": git_commit(),
        "python": platform.python_version(),
        "provider": PROVIDER,
        "requested_model": MODEL,
        "runtime": "gemini-native models.generateContent",
        "api_version": gemini.base_url.rsplit("/", 1)[-1],
        "provider_endpoint": gemini.provider_endpoint(),
        "requested_generation_options": OPTIONS,
        "seed": None,
        "input": {
            "H_SYN_VERSION": H_SYN_VERSION,
            "state_id": state.state_id,
            "payload_sha256": digest,
            "fixtures": {
                "risk_and_portfolio_technical_signal": FIXTURE_SIGNAL.signal,
                "portfolio_risk_verdict": FIXTURE_APPROVAL.verdict,
            },
        },
        "roles": results,
    }
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    stamp = started.strftime("%Y%m%dT%H%M%SZ")
    path = EVIDENCE_DIR / f"{MODEL}_dev_smoke_{stamp}.json"
    path.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(path.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
