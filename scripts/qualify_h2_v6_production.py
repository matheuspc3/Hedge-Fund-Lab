"""Assert-based production-path qualification: generated prices, fake HTTP, no keys.

No real phase authorization, approval, freeze, Gemini or reserved prices.
"""

# ruff: noqa: E402 -- standalone imports.
import argparse
import asyncio
import json
import sqlite3
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack, closing
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from qualify_h2_v6_evaluation import Factory, metrics_and_benchmarks, rejected

from src.agents.llm_client import (
    LLMCallMetadata,
    ProviderRequestRejected,
    ProviderTransportError,
)
from src.agents.participant import LLMDecisionError
from src.agents.state import PortfolioAction, RiskVerdict, TechnicalEvidenceResponse
from src.experiments.h2_evaluation import (
    BENCHMARK_SPECS,
    PARTICIPANT_SHA256,
    RESERVED_SNAPSHOT,
)
from src.experiments.h2_evaluation_manifest import (
    CANDIDATE,
    read,
    sha_file,
    verify_manifest,
    verify_preservation,
)
from src.experiments.h2_evaluation_offline import no_network, synthetic_fixture
from src.experiments.h2_evaluation_production import (
    QUALIFIED_STATUS,
    CallBank,
    DurableGeminiClient,
    EvaluationBatch,
    JournalIntegrityError,
    SyntheticTransport,
)
from src.experiments.participants import PARTICIPANT_REGISTRY, build_participant
from src.experiments.runner import ExperimentRunner

CHECKS = []


def passed(name):
    CHECKS.append(name)
    print("PASS", name, flush=True)


class NativeFactory:
    def __init__(self, signal="MANTER", *, block=False):
        self.factory = Factory(signal)
        self.calls, self.lock, self.transports = 0, threading.Lock(), []
        self.bank = None
        self.started, self.proceed = threading.Event(), threading.Event()
        self.block = block

    def __call__(self, slot):
        mock = self.factory(slot)

        def respond(method, url, headers, body):
            if self.bank is not None:
                from src.experiments.h2_evaluation_production import _PENDING_CALL

                pending = _PENDING_CALL.get()
                # A separate connection observes the reservation committed before HTTP.
                with closing(sqlite3.connect(self.bank)) as db:
                    assert db.execute(
                        "SELECT identity FROM calls WHERE slot=? AND sequence=?", pending
                    ).fetchone()
            with self.lock:
                self.calls += 1
                count = self.calls
                blocked = self.block and count == 1
            if blocked:
                self.started.set()
                assert self.proceed.wait(
                    30
                ), "qualification caller failed to release fake transport"
            schemas = {
                s.__name__: s
                for s in (TechnicalEvidenceResponse, RiskVerdict, PortfolioAction)
            }
            schema = schemas[body["generationConfig"]["responseJsonSchema"]["title"]]
            assert body["generationConfig"]["thinkingConfig"] == {"thinkingLevel": "LOW"}
            assert body["generationConfig"]["temperature"] == 1.0
            assert body["generationConfig"]["maxOutputTokens"] == 8192
            assert "seed" not in body["generationConfig"]
            with self.lock:
                response = asyncio.run(
                    mock.generate(
                        body["systemInstruction"]["parts"][0]["text"],
                        body["contents"][0]["parts"][0]["text"],
                        schema,
                    )
                )
            envelope = {
                "responseId": f"fake-{slot}-{count}",
                "modelVersion": "gemini-3.8-flash",
                "candidates": [
                    {
                        "finishReason": "STOP",
                        "content": {"parts": [{"text": response.model_dump_json()}]},
                    }
                ],
                "usageMetadata": {
                    "promptTokenCount": 1,
                    "candidatesTokenCount": 1,
                    "totalTokenCount": 2,
                },
            }
            return json.dumps(envelope).encode()

        transport = SyntheticTransport(respond)
        self.transports.append(transport)
        return transport


def authorization(root, phase, document, sha, *, checkpoint=None):
    value = {
        "kind": "H2_V6_SYNTHETIC_PHASE_AUTHORIZATION",
        "phase": phase,
        "manifest_sha256": sha,
        "participant_sha256": PARTICIPANT_SHA256,
        "R": 3,
        "run_identities": document["protocol"]["run_identities"][phase],
        "window": document["protocol"]["windows"][phase],
        "authorized": True,
        "host": "generativelanguage.googleapis.com",
        "synthetic_only": True,
    }
    if checkpoint:
        value["validation_checkpoint_sha256"] = sha_file(checkpoint)
    path = root / f"synthetic-{phase}-{len(list(root.glob('synthetic-*.json')))}.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def journal_checks(root, params):
    async def call(client, text="{}"):
        return await client.generate(
            "synthetic frozen-runtime test",
            text,
            RiskVerdict,
            {"temperature": 1.0, "thinking_level": "low", "max_output_tokens": 8192},
            metadata=LLMCallMetadata(stage="risk_manager"),
        )

    def setup(name, fresh=True, factory=None):
        bank = CallBank(
            root / f"{name}.sqlite", "synthetic-journal-identity", "VALIDATION"
        )
        factory = factory or NativeFactory()
        client = DurableGeminiClient(
            bank,
            "L01",
            params,
            fresh=fresh,
            gate=lambda: None,
            transport=factory("L01") if fresh else None,
            synthetic=True,
        )
        client.begin_session("2024-09-02")
        return bank, client, factory

    for name, boundary in (
        ("before_reservation", "INSERT INTO calls"),
        ("response_before_raw_commit", "UPDATE calls SET raw="),
        ("raw_before_validated_commit", "UPDATE calls SET record="),
    ):
        bank, client, factory = setup(name)
        original = bank._commit

        def interrupted(sql, args, *, boundary=boundary, original=original, **kwargs):
            if sql.startswith(boundary):
                raise JournalIntegrityError("synthetic interrupted persistence")
            return original(sql, args, **kwargs)

        with patch.object(bank, "_commit", interrupted):
            rejected(
                lambda client=client: asyncio.run(call(client)), JournalIntegrityError
            )
        count = factory.calls
        assert count == (0 if name == "before_reservation" else 1)
        bank.close()
        bank, client, _ = setup(name, fresh=False, factory=factory)
        if name == "raw_before_validated_commit":
            assert asyncio.run(call(client)).verdict == "APROVADO"
        else:
            rejected(lambda client=client: asyncio.run(call(client)))
        assert factory.calls == count
        bank.close()
    passed(
        "durable reservation/raw/validated response crash boundaries; reopen; no extra inference"
    )

    bank, client, factory = setup("commit_rollback")
    real_db = bank.db
    proxy = Mock(wraps=real_db)
    proxy.commit.side_effect = sqlite3.OperationalError("synthetic commit failure")
    with patch.object(bank, "db", proxy):
        rejected(lambda client=client: asyncio.run(call(client)), JournalIntegrityError)
    assert (
        bank.row("L01", 0) is None and bank.never_reserved("L01") and factory.calls == 0
    )
    proxy.rollback.side_effect = OSError("synthetic rollback failure")
    with patch.object(bank, "db", proxy):
        rejected(lambda client=client: asyncio.run(call(client)), JournalIntegrityError)
    real_db.rollback()
    assert factory.calls == 0
    bank.close()
    bank, client, _ = setup("commit_rollback", factory=factory)
    assert bank.never_reserved("L01")
    assert asyncio.run(call(client)).verdict == "APROVADO" and factory.calls == 1
    bank.db.execute("DROP TABLE calls")
    bank.db.commit()
    bank.close()
    rejected(lambda: setup("commit_rollback"), JournalIntegrityError)
    passed(
        "real SQLite commit rollback proves never-reserved recovery; lost bank schema cannot recreate calls"
    )

    bank, client, factory = setup("reserved_no_transport")
    # Reserve then fail before dispatch, leaving an uncertain durable identity.
    with patch.object(
        client.native, "generate", side_effect=JournalIntegrityError("before dispatch")
    ):
        rejected(lambda client=client: asyncio.run(call(client)), JournalIntegrityError)
    assert factory.calls == 0
    bank.close()
    bank, client, _ = setup("reserved_no_transport", fresh=False, factory=factory)
    rejected(lambda client=client: asyncio.run(call(client)), JournalIntegrityError)
    assert factory.calls == 0
    bank.envelope("L01", 0, b"truncated-json")
    bank.close()
    bank, client, _ = setup("reserved_no_transport", fresh=False, factory=factory)
    rejected(lambda client=client: asyncio.run(call(client)), JournalIntegrityError)
    assert factory.calls == 0
    bank.close()
    passed("reserved-before-send and transport-invalid envelope recovery fail closed")

    for name, error in (
        ("provider_error", ProviderRequestRejected("synthetic refusal")),
        (
            "transient_retry",
            ProviderTransportError("synthetic 429", status=429, retry_after=0),
        ),
    ):
        bank, client, factory = setup(name)
        delegate, attempts = client.delegate, []

        def flaky(*args, error=error, attempts=attempts, delegate=delegate):
            attempts.append(1)
            if len(attempts) == 1:
                raise error
            return delegate(*args)

        client.delegate = flaky
        if name == "provider_error":
            rejected(
                lambda client=client: asyncio.run(call(client)), ProviderRequestRejected
            )
            assert len(attempts) == 1
        else:
            assert asyncio.run(call(client)).verdict == "APROVADO"
            record = json.loads(bank.row("L01", 0)[4])
            assert record["attempt_count"] == 2 and len(attempts) == 2
        bank.close()
        bank, client, _ = setup(name, fresh=False, factory=factory)
        if name == "provider_error":
            rejected(
                lambda client=client: asyncio.run(call(client)), ProviderRequestRejected
            )
        else:
            assert asyncio.run(call(client)).verdict == "APROVADO"
        assert len(attempts) == (1 if name == "provider_error" else 2)
        bank.close()
    passed(
        "provider errors remain errors; frozen transient retry and exact error/response replay"
    )

    bank, client, factory = setup("malformed_http_retry")
    delegate, malformed_attempts = client.delegate, []

    def malformed_once(*args):
        malformed_attempts.append(1)
        return b"truncated-json" if len(malformed_attempts) == 1 else delegate(*args)

    client.delegate = malformed_once
    client.client.base_delay = 0
    assert asyncio.run(call(client)).verdict == "APROVADO"
    evidence = json.loads(bank.export("L01").splitlines()[0])
    assert len(malformed_attempts) == 2 and evidence["record"]["attempt_count"] == 2
    assert len(evidence["attempts"]) == 2 and all(
        a["raw_base64"] for a in evidence["attempts"]
    )
    bank.close()
    passed(
        "frozen malformed-HTTP retry obtains next fake envelope; both raw attempts remain durable"
    )

    bank, client, factory = setup("concurrent_calls")

    async def ensemble():
        return await asyncio.gather(*(call(client, str(i)) for i in range(30)))

    assert len(asyncio.run(ensemble())) == 30
    client.assert_complete()
    assert factory.calls == 30 and len(bank.export("L01").splitlines()) == 30
    bank.db.execute("UPDATE calls SET raw_sha='corrupt' WHERE sequence=0")
    bank.db.commit()
    rejected(lambda: bank.export("L01"), JournalIntegrityError)
    bank.close()
    passed(
        "concurrent analyst calls have unique durable sequences; journal corruption fails closed"
    )


def integration(root, cleanup, document, sha):
    snapshot = synthetic_fixture(root)
    auth = authorization(root, "VALIDATION", document, sha)

    def batch(name, phase="VALIDATION", *, factory=None, checkpoint=None, auth_path=auth):
        factory = factory or NativeFactory()
        value = EvaluationBatch(
            root / name,
            snapshot,
            phase,
            manifest=CANDIDATE,
            manifest_sha256=sha,
            authorization=auth_path,
            transport_factory=factory,
            validation_checkpoint=checkpoint,
        )
        factory.bank = value.root / "provider.sqlite"
        cleanup.callback(value.close)
        return value, factory

    registry = dict(PARTICIPANT_REGISTRY)
    for spec in BENCHMARK_SPECS:
        assert type(build_participant(spec)) is registry[spec.kind]
        assert build_participant(spec) is not build_participant(spec)
    assert PARTICIPANT_REGISTRY == registry
    passed(
        "normal static registry; exact benchmark specs; fresh instances; no registry mutation"
    )

    rejected(lambda: batch("wrong_phase", "FINAL_TEST"), ValueError)
    from dataclasses import replace

    rejected(
        lambda: EvaluationBatch(
            root / "reserved",
            replace(snapshot, snapshot_id=RESERVED_SNAPSHOT),
            "VALIDATION",
            manifest=CANDIDATE,
            manifest_sha256=sha,
            authorization=auth,
            transport_factory=NativeFactory(),
        ),
        ValueError,
        "reserved",
    )
    rejected(lambda: verify_manifest(CANDIDATE, "0" * 64), ValueError)
    altered = read(CANDIDATE)
    altered["sources_sha256"].pop("src/experiments/runner.py")
    drift = root / "incomplete-manifest.json"
    drift.write_text(json.dumps(altered))
    rejected(lambda: verify_manifest(drift, sha_file(drift)), ValueError, "inventory")
    from src.experiments import h2_evaluation_manifest as identity

    real_git = identity.git
    with patch.object(
        identity,
        "git",
        side_effect=lambda *args: b" M synthetic.py"
        if args == ("status", "--porcelain")
        else real_git(*args),
    ):
        rejected(lambda: verify_manifest(CANDIDATE, sha), ValueError, "clean")
    final_without_release = authorization(root, "FINAL_TEST", document, sha)
    rejected(
        lambda: batch("no_checkpoint", "FINAL_TEST", auth_path=final_without_release),
        ValueError,
        "checkpoint",
    )
    tampered = read(auth)
    tampered["kind"] = "CAL_B4_H2_V6_SPECIFIC_EXTERNAL_AUTHORIZATION"
    bad = root / "bad-authorization.json"
    bad.write_text(json.dumps(tampered))
    rejected(
        lambda: batch("wrong_authorization", auth_path=bad), ValueError, "authorization"
    )
    from src.experiments.h2_evaluation_manifest import require_authorization

    rejected(
        lambda: require_authorization(document, sha, "VALIDATION", auth, synthetic=False),
        ValueError,
    )
    passed(
        "phase-specific consent, digest and reserved-data guards; candidates cannot enable real runs"
    )

    baseline, factory = batch("validation", factory=NativeFactory(block=True))
    with ThreadPoolExecutor(max_workers=1) as pool:
        running = pool.submit(baseline.execute)
        assert factory.started.wait(30)
        rejected(baseline.execute, FileExistsError)
        factory.proceed.set()
        summary = running.result()
    assert len(factory.transports) == 3 and len(factory.factory.clients) == 3
    count = factory.calls
    assert summary["statistics"]["mean"] == 0
    assert summary["statistics"]["delta"] < 0
    assert baseline.execute() == summary and factory.calls == count
    assert PARTICIPANT_REGISTRY == registry
    passed(
        "R3 native fake HTTP, independent slots, durable-before-transport; concurrent command refused; idempotency"
    )

    # Publication interrupted after all raw/validated calls were durable.
    baseline.db.execute("UPDATE slots SET state='STARTED',seal=NULL WHERE slot='L01'")
    baseline.db.commit()
    original = (baseline._path("L01") / "provider_journal.jsonl").read_bytes()
    assert baseline.execute() == summary and factory.calls == count
    assert (baseline._path("L01") / "provider_journal.jsonl").read_bytes() == original
    passed(
        "published-without-seal exact recovery preserves journal/artifacts and makes no new transport"
    )

    costs = baseline.cost_sensitivity()
    assert set(costs) == {"0", "5", "10", "20"}
    assert (
        baseline.db.execute(
            "SELECT count(*) FROM dispositions WHERE state='PENDING'"
        ).fetchone()[0]
        == 0
    )
    assert baseline.cost_sensitivity() == costs and factory.calls == count
    checkpoint = baseline.checkpoint()
    final_auth = authorization(root, "FINAL_TEST", document, sha, checkpoint=checkpoint)
    final, final_factory = batch(
        "final", "FINAL_TEST", auth_path=final_auth, checkpoint=checkpoint
    )
    passed(
        "valid exact cost replay and 24 closed dispositions; negative contrast releases; Final bound to checkpoint"
    )

    equity = baseline._path("L01") / "equity.csv"
    original = equity.read_bytes()
    equity.write_bytes(original + b"\n")
    rejected(final.execute, ValueError, "corrupted")
    equity.write_bytes(original)
    baseline.db.execute("UPDATE slots SET state='STARTED' WHERE slot='L01'")
    baseline.db.commit()
    rejected(final.execute, ValueError, "incomplete")
    baseline.db.execute("UPDATE slots SET state='COMPLETE' WHERE slot='L01'")
    baseline.db.commit()
    assert final_factory.calls == 0
    passed(
        "corrupted/incomplete Validation blocks Final before client construction, independent of performance"
    )

    final_summary = final.execute()
    assert final_summary["statistics"]["confirmatory_contrasts"] == 1
    assert final_summary["statistics"]["p"] is None
    final.cost_sensitivity()
    assert (
        final.db.execute(
            "SELECT count(*) FROM dispositions WHERE state='PENDING'"
        ).fetchone()[0]
        == 0
    )
    passed(
        "synthetic Final only after complete identical Validation; A degeneracy retained; no reserved outcomes"
    )

    buying, buying_factory = batch("negative_validation", factory=NativeFactory("TRADE"))
    buying_summary = buying.execute()
    assert all(i["metrics"]["total_return"] < 0 for i in buying_summary["individual"])
    buying_count = buying_factory.calls
    divergent = buying.cost_sensitivity()
    invalid = [
        i
        for spread in ("0", "10", "20")
        for i in divergent[spread]["individual"]
        if i["status"].startswith("COST_SENSITIVITY_NOT_ESTIMABLE")
    ]
    assert len(invalid) == 9 and all(
        i["metrics"] is None
        and i["secondary"] is None
        and i["reason"]
        and i["affected_identity"]
        for i in invalid
    )
    assert all(divergent[s]["statistics"] is None for s in ("0", "10", "20"))
    buying.checkpoint()
    assert buying_factory.calls == buying_count
    passed(
        "negative financial returns release on integrity; divergent cost replay N/A/null; no subset/no new calls"
    )

    # A deterministic scenario fails on disk: no N/A and no descriptive closure.
    operational, _ = batch("operational_cost")
    # Reuse native-independent baseline fixtures rather than infer extra calls.
    with patch.object(
        ExperimentRunner, "persist", side_effect=OSError("synthetic disk failure")
    ):
        rejected(operational.execute, OSError)
    rejected(operational.checkpoint, ValueError)
    original_disposition = baseline.db.execute(
        "SELECT value FROM meta WHERE key='L01-cost-0'"
    ).fetchone()[0]
    baseline.db.execute("UPDATE meta SET value='{}' WHERE key='L01-cost-0'")
    baseline.db.commit()
    rejected(baseline.cost_sensitivity, JournalIntegrityError, "corrupted")
    baseline.db.execute(
        "UPDATE meta SET value=? WHERE key='L01-cost-0'", (original_disposition,)
    )
    baseline.db.execute(
        "DELETE FROM meta WHERE key IN ('L01-cost-0','L01-cost-0:sha256')"
    )
    baseline.db.commit()
    normal = baseline._run_slot

    def cost_disk_failure(slot, *args):
        if slot == "L01-cost-0":
            raise OSError("synthetic replay publication failure")
        return normal(slot, *args)

    with patch.object(baseline, "_run_slot", side_effect=cost_disk_failure):
        rejected(baseline.cost_sensitivity, OSError)
    with patch.object(
        baseline,
        "_run_slot",
        side_effect=LLMDecisionError("synthetic code failure without matcher cause"),
    ):
        rejected(baseline.cost_sensitivity, LLMDecisionError)
    assert (
        baseline.db.execute("SELECT value FROM meta WHERE key='L01-cost-0'").fetchone()
        is None
    )
    assert factory.calls == count
    passed(
        "operational publication errors interrupt rather than become descriptive N/A; incomplete phase cannot release"
    )
    baseline.root.joinpath("execution.lock").write_text("synthetic abandoned owner")
    rejected(baseline.execute, FileExistsError)
    baseline.root.joinpath("execution.lock").unlink()
    passed("abandoned exclusive lock fails closed; no automatic replacement or rerun")
    return {
        "validation": summary,
        "final": final_summary,
        "negative_validation": buying_summary,
        "costs_valid": costs,
        "costs_divergent": divergent,
        "native_fake_calls": factory.calls,
        "negative_native_fake_calls": buying_factory.calls,
        "invalid_cost_dispositions": len(invalid),
    }


def preservation():
    result = verify_preservation()
    import run_cal_b4 as cal

    target = ROOT / "docs/evidence/cal_b4/run_20261008T221200Z"
    batch = cal.base.verify_seal(target)
    for anchor, sha in batch["anchor_seal_sha256"].items():
        assert sha_file(target / "anchors" / anchor / "sealed.json") == sha
    for name, sha in read(target / "AUDIT_SEAL.json").items():
        assert sha_file(target / name) == sha
    for path, sha in read(cal.GUARDS)["sources_sha256"].items():
        assert sha_file(ROOT / path) == sha
    assert len(read(target / "automatic_gates.json")["gates"]) == 12
    assert all(g["pass"] for g in read(target / "automatic_gates.json")["gates"].values())
    passed(
        "historical 6752 identities, declared infrastructure exceptions only; raw/anchor/audit seals and treatment intact"
    )
    return result


def main():
    if not __debug__:
        raise SystemExit("assert qualification requires no -O")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    started = time.perf_counter()
    sha = CANDIDATE.with_suffix(".sha256").read_text().strip()
    document = verify_manifest(CANDIDATE, sha)
    (ROOT / ".pytest_temp").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(
        dir=ROOT / ".pytest_temp", prefix="h2-production-"
    ) as folder:
        root = Path(folder)
        with no_network(), ExitStack() as cleanup:
            journal_checks(root, document["protocol"]["participant_spec"]["params"])
            metrics = metrics_and_benchmarks()
            report = {
                "integration": integration(root, cleanup, document, sha),
                "metrics": metrics,
                "preservation": preservation(),
            }
    report.update(
        {
            "status": QUALIFIED_STATUS,
            "manifest_sha256": sha,
            "checks": CHECKS,
            "check_groups": len(CHECKS),
            "elapsed_seconds": round(time.perf_counter() - started, 2),
            "provider_calls": 0,
            "data": "GENERATED_SYNTHETIC_ONLY",
            "real_validation_executed": False,
            "real_final_executed": False,
            "academic_approval": False,
            "system_freeze_executed": False,
            "individual_synthetic_artifacts": "TEMPORARY; REMOVED AFTER CHECKS",
        }
    )
    if args.report:
        target = args.report.resolve()
        if (
            not target.is_relative_to(ROOT / "docs/evidence/h2_v6_evaluation")
            or target.exists()
        ):
            raise ValueError(
                "new report must remain in evaluation evidence and never overwrite artifacts"
            )
        target.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    print(QUALIFIED_STATUS, flush=True)


if __name__ == "__main__":
    main()
