"""Operational retry v1 and a durable aggregate USD budget, independent of strategy."""
import hashlib
import json
import sqlite3
from contextlib import closing
from decimal import Decimal

from src.agents.llm_client import ProviderTransportError, RetryingLLMClient
from src.agents.llm_trace import RecordingLLMClient
from src.experiments.h2_evaluation_production import JournalIntegrityError, _PENDING_CALL

CAP = Decimal("34.78")
MAX_ATTEMPTS = 2


class BudgetStop(JournalIntegrityError):
    pass


class RecoveryStop(JournalIntegrityError):
    pass


class TestCrash(BaseException):
    pass


class Budget:
    """One charge per physical attempt; unknown and in-flight charges stay reserved."""
    def __init__(self, path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as c, c:
            c.execute("CREATE TABLE IF NOT EXISTS attempts (id TEXT PRIMARY KEY, reserve TEXT NOT NULL, charge TEXT NOT NULL, state TEXT NOT NULL, raw BLOB, sha TEXT, metadata TEXT NOT NULL)")

    def connect(self):
        c = sqlite3.connect(self.path, timeout=30)
        c.execute("PRAGMA synchronous=FULL")
        return c

    def reserve(self, key, bound, metadata):
        with closing(self.connect()) as c, c:
            c.execute("BEGIN IMMEDIATE")
            if c.execute("SELECT 1 FROM attempts WHERE id=?", (key,)).fetchone():
                raise RecoveryStop("physical_attempt_already_reserved_no_repeat")
            total = sum((Decimal(x[0]) for x in c.execute("SELECT charge FROM attempts")), Decimal(0))
            if total + bound > CAP:
                raise BudgetStop("aggregate_cap_would_be_exceeded")
            c.execute("INSERT INTO attempts VALUES (?,?,?,'IN_FLIGHT',NULL,NULL,?)", (key, str(bound), str(bound), json.dumps(metadata, sort_keys=True)))

    def capture(self, key, raw):
        try:
            payload = json.loads(raw)
            usage = payload.get("usageMetadata") if isinstance(payload, dict) else None
        except (json.JSONDecodeError, UnicodeDecodeError):
            usage = None
        usage = usage if isinstance(usage, dict) else {}
        p, o, t, total = (usage.get(k) for k in ("promptTokenCount", "candidatesTokenCount", "thoughtsTokenCount", "totalTokenCount"))
        if t is None and isinstance(p, int) and isinstance(o, int) and total == p + o:
            t = 0
        valid = all(type(x) is int and x >= 0 for x in (p, o, t, total)) and total == p + o + t
        cost = (Decimal(p) * Decimal("0.75") + Decimal(o + t) * Decimal("3.75")) / 1000000 if valid else None
        with closing(self.connect()) as c, c:
            reserve = Decimal(c.execute("SELECT reserve FROM attempts WHERE id=?", (key,)).fetchone()[0])
            charge = cost if cost is not None else reserve
            c.execute("UPDATE attempts SET charge=?,state=?,raw=?,sha=? WHERE id=?", (str(charge), "KNOWN" if valid else "UNKNOWN_USAGE", raw, hashlib.sha256(raw).hexdigest(), key))
        if charge > reserve:
            raise RecoveryStop("provider_usage_exceeded_reserved_bound")

    def unknown(self, key):
        with closing(self.connect()) as c, c:
            c.execute("UPDATE attempts SET state='UNKNOWN_TRANSPORT' WHERE id=?", (key,))

    def response(self, prefix):
        with closing(self.connect()) as c:
            rows = c.execute("SELECT raw,sha FROM attempts WHERE id LIKE ? AND raw IS NOT NULL ORDER BY id", (prefix + "/%",)).fetchall()
        if not rows:
            return None
        if len(rows) != 1 or hashlib.sha256(rows[0][0]).hexdigest() != rows[0][1]:
            raise RecoveryStop("budget_envelope_integrity_failed")
        return rows[0][0]

    def summary(self):
        with closing(self.connect()) as c:
            rows = c.execute("SELECT charge,state FROM attempts").fetchall()
        known = sum((Decimal(v) for v, state in rows if state == "KNOWN"), Decimal(0))
        uncertain = sum((Decimal(v) for v, state in rows if state != "KNOWN"), Decimal(0))
        return {"cap_usd": str(CAP), "physical_attempts": len(rows), "known_estimated_usd": str(known), "uncertain_and_inflight_reserved_usd": str(uncertain), "exposure_usd": str(known + uncertain), "unknown_attempts": sum(state != "KNOWN" for _, state in rows)}


def retry(client):
    return RetryingLLMClient(client, max_attempts=MAX_ATTEMPTS, base_delay=1, retry_exceptions=(ProviderTransportError, ConnectionError, TimeoutError))


def recording_retry(client, **kw):
    return RecordingLLMClient(retry(client), **kw)


class Transport:
    """Mixin for the existing Radar/Wallet native clients, before schema validation."""
    def __init__(self, *args, budget, bank_name, crash=False, **kw):
        super().__init__(*args, **kw)
        self.budget, self.bank_name, self.crash = budget, bank_name, crash
        self.fatal = None
        self.client = retry(self.native)
        delegate = self.delegate

        def dispatch(method, url, headers, body):
            slot, sequence = _PENDING_CALL.get()
            attempt = self.bank.attempt_count(slot, sequence)
            key = f"{self.bank_name}/{slot}/{sequence}/{attempt}"
            bound = Decimal("0.159744") if self.bank_name.endswith("manager") else Decimal("0.110592")
            self.budget.reserve(key, bound, {"bank": self.bank_name, "slot": slot, "sequence": sequence, "attempt": attempt, "request_identity": self.bank.row(slot, sequence)[1]})
            try:
                raw = delegate(method, url, headers, body)
            except Exception as exc:
                self.budget.unknown(key)
                if isinstance(exc, ProviderTransportError) and (getattr(exc, "retry_after", 0) or 0) > 30:
                    raise RecoveryStop("retry_after_over_30_seconds_requires_review") from exc
                raise
            if self.native.api_key and self.native.api_key.encode() in raw:
                raise RecoveryStop("secret_echo_not_persisted")
            self.budget.capture(key, raw)
            if self.crash:
                raise TestCrash("after_durable_budget_envelope_before_call_bank")
            return raw
        self.delegate = dispatch

    def _transport(self, method, url, headers, body):
        if self.fatal is not None:
            raise self.fatal
        try:
            return self._durable_transport(method, url, headers, body)
        except (JournalIntegrityError, TestCrash) as exc:
            self.fatal = exc
            raise

    def _durable_transport(self, method, url, headers, body):
        slot, sequence = _PENDING_CALL.get()
        row = self.bank.row(slot, sequence)
        if row is not None and row[2] is not None:
            return row[2]
        prefix = f"{self.bank_name}/{slot}/{sequence}"
        recovered = self.budget.response(prefix)
        if recovered is not None:
            self.bank.envelope(slot, sequence, recovered)
            return recovered
        if self.bank.attempt_count(slot, sequence) >= MAX_ATTEMPTS:
            raise RecoveryStop("two_physical_attempts_exhausted_no_automatic_replacement")
        return super()._transport(method, url, headers, body)
