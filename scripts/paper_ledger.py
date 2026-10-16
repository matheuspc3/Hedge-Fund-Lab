"""V1 paper envelope over the sealed V5 reducer. Writers are temporary/synthetic only.

No provider, broker, H2 runner or official execution adapter is imported here.
"""

import copy
import json
import sqlite3
import tempfile
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

import multiasset_manager as manager
import multiasset_portfolio as b

IDENTITY = "HFL-MULTIASSET-PAPER-LEDGER-V1"
VERSION = 1
ROOT = Path(__file__).resolve().parents[1]
CALENDAR = ROOT / "docs/evidence/calendar/b3_official_sessions_2016-01-04_2026-08-31.txt"
CALENDAR_SHA = "c4af99f8807975bbdcdadcdd86a4d0e1f30a45a701ed7b2ed5657ed9bb4f0508"
CLASSIFICATIONS = (
    "SYNTHETIC_TEST",
    "CONSULTATIVE_SNAPSHOT",
    "PAPER_ACTIVE",
    "PAPER_CLOSED",
)
EVENTS = {
    "PORTFOLIO_CREATED": "INITIALIZED",
    "PROPOSAL_LINKED": "PROPOSED",
    "PROPOSAL_REFERENCED": None,
    "VALIDATION_RECORDED": None,
    "AUTHORIZATION_RECORDED": "APPROVED",
    "PAPER_ORDER_CREATED": "RESERVED",
    "PAPER_ORDER_CANCELLED": "CANCELLED",
    "PAPER_ORDER_EXECUTED": "FILLED",
    "SETTLEMENT_RECORDED": "SETTLED",
    "MARKET_PRICE_OBSERVED": None,
    "PORTFOLIO_VALUED": "MARKED",
    "PORTFOLIO_RECONCILED": None,
    "PORTFOLIO_CLOSED": None,
}


def canonical(value):
    return json.dumps(
        b.pack(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def fingerprints():
    return {
        name: b.sha_file(ROOT / name)
        for name in (
            "scripts/multiasset_portfolio.py",
            "scripts/multiasset_manager.py",
            "src/backtesting/b3_calendar.py",
        )
    }


def sessions():
    if b.sha_file(CALENDAR) != CALENDAR_SHA:
        raise ValueError("calendar_evidence_hash_mismatch")
    return tuple(
        d
        for d in CALENDAR.read_text(encoding="utf-8").splitlines()
        if d.startswith("2026-")
    )


def session(day):
    b.session(day)
    if day not in sessions():
        raise ValueError("calendar_coverage_unavailable")
    return day


def settlement_day(day):
    days = sessions()
    index = days.index(session(day))
    if index + 2 >= len(days):
        raise ValueError("settlement_calendar_unavailable")
    due = days[index + 2]
    if b.settlement_day(day) != due:
        raise ValueError("settlement_calendar_disagreement")
    return due


def observation(
    day, prices, *, classification="SYNTHETIC_TEST", price_type="SYNTHETIC_REFERENCE"
):
    """Fixture builder; OFFICIAL_B3_RAW denotes official-format fixture, never a live feed."""
    body = {
        "schema_version": 1,
        "session": day,
        "currency": "BRL",
        "basis": "RAW",
        "price_type": price_type,
        "classification": classification,
        "fixture": True,
        "observed_at": day + "T18:00:00-03:00",
        "source": "B3_COTAHIST_FIXTURE"
        if classification == "OFFICIAL_B3_RAW"
        else "SYNTHETIC_OFFLINE_NOT_MARKET_DATA",
        "prices": prices,
    }
    return b.sealed({**body, "data_sha256": b.digest(body)})


def checked_observation(quote, at):
    b.check_seal(quote)
    body = {k: v for k, v in quote.items() if k not in ("sha256", "data_sha256")}
    classification = quote["classification"]
    if (
        quote["schema_version"] != VERSION
        or quote["currency"] != "BRL"
        or quote["basis"] != "RAW"
        or quote["fixture"] is not True
        or classification not in ("SYNTHETIC_TEST", "OFFICIAL_B3_RAW")
        or quote["source"]
        != (
            "B3_COTAHIST_FIXTURE"
            if classification == "OFFICIAL_B3_RAW"
            else "SYNTHETIC_OFFLINE_NOT_MARKET_DATA"
        )
        or quote["price_type"]
        not in (
            ("CLOSE", "OPEN")
            if classification == "OFFICIAL_B3_RAW"
            else ("SYNTHETIC_REFERENCE",)
        )
        or quote["data_sha256"] != b.digest(body)
    ):
        raise ValueError("inconsistent_price_provenance")
    session(quote["session"])
    if b.instant(quote["observed_at"]).date().isoformat() != quote[
        "session"
    ] or b.instant(quote["observed_at"]) > b.instant(at):
        raise ValueError("price_timestamp_or_lookahead")
    for symbol, price in quote["prices"].items():
        b.ticker(symbol)
        b.amount(price, positive=True)
    return quote


def engine_marks(quote):
    # Versioned bridge: V5 receives its original synthetic RAW contract. The
    # envelope retains the original fixture provenance, never reclassifies it.
    return b.marks(quote["session"], quote["prices"])


def reconciliation(state, expected=None):
    financial = state["financial"]
    report = b.view(financial)
    errors = []
    if b.dec(financial["costs"]) != sum(
        (b.dec(e["cost"]) for e in financial["executions"].values()), b.ZERO
    ):
        errors.append("execution_cost_total_mismatch")
    if b.dec(financial["realized_pnl"]) != sum(
        (b.dec(e["realized_pnl"]) for e in financial["executions"].values()), b.ZERO
    ):
        errors.append("realized_pnl_total_mismatch")
    for oid, execution in financial["executions"].items():
        if execution["due_session"] != settlement_day(execution["trade_session"]):
            errors.append("settlement_date_mismatch:" + oid)
        if oid not in state["execution_ids"] or oid not in financial["used_orders"]:
            errors.append("execution_identity_missing:" + oid)
    for name, value in (expected or {}).items():
        if name not in report or report[name] != value:
            errors.append("expected_state_mismatch:" + name)
    if state["valuation_unavailable"]:
        errors.append("valuation_incomplete")
    return b.sealed(
        {
            "status": "RECONCILIATION_FAILED" if errors else "RECONCILED",
            "errors": errors,
            "financial_sha256": b.financial_hash(financial),
            "view": report,
        }
    )


def reduce(state, event):
    """Pure replay including authorization, chronology, financial and source guards."""
    kind, p, at, day = (
        event["kind"],
        event["payload"],
        event["effective_at"],
        event["session"],
    )
    if (
        kind not in EVENTS
        or event["authority"] != "SYNTHETIC_TEST_OPERATOR"
        or event["source"] != "ISOLATED_SYNTHETIC_QUALIFICATION"
    ):
        raise ValueError("unsupported_event_or_authority")
    session(day)
    if b.instant(at).date().isoformat() != day or event["economic_date"] != day:
        raise ValueError("economic_session_mismatch")
    state = copy.deepcopy(state)
    if kind == "PORTFOLIO_CREATED":
        meta = p["portfolio"]
        if (
            state is not None
            or meta["classification"] != "SYNTHETIC_TEST"
            or meta["ledger_version"] != IDENTITY
            or meta["currency"] != "BRL"
            or meta["portfolio_id"] != event["portfolio_id"]
            or meta["financial_policy"] != b.POLICY
            or meta["status"] != "OPEN"
            or not meta["display_name"]
            or meta["scientific_identity"] is not None
            or meta["authorization_ids"] != []
            or not meta["provenance"]
            or b.instant(meta["created_at"]) != b.instant(at)
        ):
            raise ValueError("synthetic_identity_and_policy_required")
        if (
            p["engine_fingerprints"] != fingerprints()
            or p["calendar_sha256"] != CALENDAR_SHA
        ):
            raise ValueError("implementation_or_calendar_changed")
        quote = checked_observation(p["observation"], at)
        if quote["session"] != day or meta["allowed_sources"] != [
            "SYNTHETIC_TEST",
            "OFFICIAL_B3_RAW",
        ]:
            raise ValueError("creation_source_mismatch")
        financial = b.apply(
            None,
            "INITIALIZED",
            {
                "portfolio_id": meta["portfolio_id"],
                "policy": b.POLICY,
                "capital": meta["initial_capital"],
                "marks": engine_marks(quote),
            },
        )
        state = {
            "portfolio": meta,
            "financial": financial,
            "quote": quote,
            "observations": {},
            "observed_data": [quote["data_sha256"]],
            "valued_observations": [],
            "unavailable_sessions": [],
            "validations": {},
            "authorizations": {},
            "advisory_references": {},
            "execution_ids": {},
            "settlement_ids": {},
            "history": [],
            "reconciliations": [],
            "valuation_unavailable": [],
            "reconciliation_failed": False,
            "last_effective_at": at,
        }
    elif state is None:
        raise ValueError("portfolio_not_initialized")
    else:
        if state["portfolio"]["status"] != "OPEN":
            raise ValueError("portfolio_closed")
        if (
            b.instant(at) < b.instant(state["last_effective_at"])
            or day < state["financial"]["as_of_session"]
        ):
            raise ValueError("economic_clock_backwards")
        financial = state["financial"]
        if kind == "MARKET_PRICE_OBSERVED":
            quote = checked_observation(p["observation"], at)
            if quote["session"] != day or event["event_id"] in state["observations"]:
                raise ValueError("observation_session_or_identity")
            if quote["data_sha256"] in state["observed_data"]:
                raise ValueError("duplicate_price_import")
            state["observations"][event["event_id"]] = quote
            state["observed_data"].append(quote["data_sha256"])
        elif kind == "PORTFOLIO_VALUED":
            quote = state["observations"][p["observation_id"]]
            if quote["session"] != day:
                raise ValueError("valuation_session_mismatch")
            if p["observation_id"] in state["valued_observations"] or any(
                h["session"] == day for h in state["history"]
            ):
                raise ValueError("duplicate_valuation_or_finalized_session")
            state["valued_observations"].append(p["observation_id"])
            missing = sorted(set(financial["positions"]) - set(quote["prices"]))
            state["valuation_unavailable"] = missing
            if missing:
                state["unavailable_sessions"].append(
                    {
                        "session": day,
                        "missing_tickers": missing,
                        "observation_id": p["observation_id"],
                    }
                )
            if not missing:
                state["financial"] = b.apply(
                    financial, "MARKED", {"marks": engine_marks(quote)}
                )
                state["quote"] = quote
        elif kind == "PROPOSAL_REFERENCED":
            reference = b.check_seal(p["reference"])
            rid = b.key(reference["record_id"])
            if (
                reference["classification"] != "CONSULTATIVE_SNAPSHOT"
                or reference["status"] not in ("REJECTED_BY_VALIDATOR", "VALID_PROPOSAL")
                or reference["execution_enabled"] is not False
                or rid in state["advisory_references"]
            ):
                raise ValueError("advisory_reference_only")
            for field in ("context_sha256", "result_sha256", "validation_sha256"):
                value = reference[field]
                if (
                    not isinstance(value, str)
                    or len(value) != 64
                    or any(c not in "0123456789abcdef" for c in value)
                ):
                    raise ValueError("invalid_advisory_reference_hash")
            state["advisory_references"][rid] = reference
        elif kind == "PROPOSAL_LINKED":
            record = b.check_seal(p["record"])
            if day != financial["marks"]["session"]:
                raise ValueError("proposal_requires_current_valuation")
            state["financial"] = b.apply(financial, "PROPOSED", p)
            if record["decision_session"] != day:
                raise ValueError("proposal_session_mismatch")
        elif kind == "VALIDATION_RECORDED":
            rid = b.key(p["proposal_id"])
            proposal = financial["proposals"][rid]
            report = manager.validate(
                financial, proposal, financial["proposal_contexts"][rid], at
            )
            state["validations"][event["event_id"]] = report
        elif kind == "AUTHORIZATION_RECORDED":
            report = state["validations"][p["validation_id"]]
            proposal = financial["proposals"][p["proposal_id"]]
            if (
                not report["valid"]
                or report["proposal_sha256"] != proposal["sha256"]
                or p["proposal_sha256"] != proposal["sha256"]
                or p["validation_sha256"] != report["sha256"]
                or p["portfolio_id"] != financial["portfolio_id"]
                or p["scope"] != IDENTITY
                or p["operator"] != event["authority"]
                or p["action"] != "APPROVE"
                or report["state_sha256"] != b.financial_hash(financial)
                or not b.instant(at)
                < b.instant(p["expires_at"])
                <= b.instant(proposal["expires_at"])
            ):
                raise ValueError("authorization_scope_validation_or_expiry")
            current = manager.validate(
                financial, proposal, financial["proposal_contexts"][p["proposal_id"]], at
            )
            if not current["valid"]:
                raise ValueError("proposal_no_longer_valid")
            approval = b.demo_approval(
                financial,
                report["ready_operations"],
                proposal_sha256=proposal["sha256"],
                risk_sha256=proposal["risk_report_sha256"],
                at=at,
                expires_at=p["expires_at"],
            )
            state["financial"] = b.apply(financial, "APPROVED", {"record": approval})
            state["authorizations"][event["event_id"]] = {
                "approval": approval,
                "proposal_id": p["proposal_id"],
                "validation_id": p["validation_id"],
            }
            state["portfolio"]["authorization_ids"].append(event["event_id"])
        elif kind == "PAPER_ORDER_CREATED":
            if (
                state["valuation_unavailable"]
                or state["reconciliation_failed"]
                or any(h["session"] == day for h in state["history"])
            ):
                raise ValueError("inconsistent_or_finalized_session")
            if (
                state["quote"]["classification"] != "SYNTHETIC_TEST"
                or state["quote"]["price_type"] != "SYNTHETIC_REFERENCE"
            ):
                raise ValueError("synthetic_execution_price_required")
            authorization = state["authorizations"][event["authorization_ref"]]
            if p != {"proposal_id": authorization["proposal_id"]}:
                raise ValueError("order_authorization_mismatch")
            report = state["validations"][authorization["validation_id"]]
            if not report["ready_operations"]:
                raise ValueError("valid_proposal_has_no_operations")
            settlement_day(day)
            state["financial"] = b.apply(
                financial,
                "RESERVED",
                {
                    "operations": report["ready_operations"],
                    "approval": authorization["approval"],
                    "state_sha256": b.financial_hash(financial),
                    "at": at,
                },
            )
            state["pending_authorization"] = event["authorization_ref"]
        elif kind == "PAPER_ORDER_EXECUTED":
            if (
                not financial["pending"]
                or event["authorization_ref"] != state.get("pending_authorization")
                or state["valuation_unavailable"]
                or state["reconciliation_failed"]
            ):
                raise ValueError("reserved_authorized_order_required")
            execution_id = b.key(p["execution_id"])
            if execution_id in state["execution_ids"].values():
                raise ValueError("duplicate_execution_id")
            settlement_day(day)
            state["financial"] = b.apply(
                financial,
                "FILLED",
                {
                    "reserved_state_sha256": b.financial_hash(financial),
                    "session": day,
                    "at": at,
                },
            )
            for oid in financial["pending"]:
                state["execution_ids"][oid] = execution_id
            state.pop("pending_authorization", None)
        elif kind == "PAPER_ORDER_CANCELLED":
            if not financial["pending"] or event["authorization_ref"] != state.get(
                "pending_authorization"
            ):
                raise ValueError("pending_order_authority_required")
            state["financial"] = b.apply(financial, "CANCELLED", {})
            state.pop("pending_authorization", None)
        elif kind == "SETTLEMENT_RECORDED":
            sid = b.key(p["settlement_id"])
            if (
                sid in state["settlement_ids"].values()
                or p["confirmation_source"] != "SYNTHETIC_CUSTODIAN_CONFIRMATION"
            ):
                raise ValueError("settlement_identity_or_source")
            if state["reconciliation_failed"] or state["valuation_unavailable"]:
                raise ValueError("inconsistent_financial_state")
            execution = financial["executions"][p["order_id"]]
            if day < settlement_day(execution["trade_session"]):
                raise ValueError("settlement_not_due")
            state["financial"] = b.apply(
                financial,
                "SETTLED",
                {
                    "operation_id": p["order_id"],
                    "session": day,
                    "confirmation_source": p["confirmation_source"],
                },
            )
            state["settlement_ids"][p["order_id"]] = sid
        elif kind == "PORTFOLIO_RECONCILED":
            if day != state["quote"]["session"] or day != financial["as_of_session"]:
                raise ValueError("reconciliation_requires_current_valuation")
            report = reconciliation(state, p.get("expected"))
            state["reconciliations"].append(
                {"event_id": event["event_id"], "session": day, "at": at, **report}
            )
            state["reconciliation_failed"] = bool(report["errors"])
            if not report["errors"]:
                point = {
                    "session": day,
                    "view": report["view"],
                    "quote_sha256": state["quote"]["sha256"],
                    "reconciliation_id": event["event_id"],
                }
                prior = next((h for h in state["history"] if h["session"] == day), None)
                if prior and prior["view"] != point["view"]:
                    raise ValueError("session_already_reconciled")
                if not prior:
                    state["history"].append(point)
        elif kind == "PORTFOLIO_CLOSED":
            if (
                financial["pending"]
                or financial["receivables"]
                or any(b.dec(pos["quantity"]) for pos in financial["positions"].values())
                or state["reconciliation_failed"]
                or state["valuation_unavailable"]
            ):
                raise ValueError("portfolio_cannot_close_with_financial_obligations")
            state["portfolio"]["status"] = "CLOSED"
    state["last_effective_at"] = at
    b.view(state["financial"])
    return state


def replay(events, checkpoint):
    state, previous, ids, commands = None, None, set(), set()
    for sequence, event in enumerate(events, 1):
        b.check_seal(event)
        if (
            event["schema_version"] != VERSION
            or event["ledger_version"] != IDENTITY
            or event["sequence"] != sequence
            or event["previous_sha256"] != previous
            or event["event_id"] in ids
            or event["idempotency_key"] in commands
            or (state and event["portfolio_id"] != state["portfolio"]["portfolio_id"])
        ):
            raise ValueError("event_chain_or_identity_broken")
        b.key(event["event_id"])
        b.key(event["idempotency_key"])
        b.instant(event["recorded_at"])
        if sequence > 1 and b.instant(event["recorded_at"]) < b.instant(
            events[sequence - 2]["recorded_at"]
        ):
            raise ValueError("recording_clock_backwards")
        state = reduce(state, event)
        previous = event["sha256"]
        ids.add(event["event_id"])
        commands.add(event["idempotency_key"])
    if checkpoint != {"sequence": len(events), "head_sha256": previous, "state": state}:
        raise ValueError("checkpoint_replay_mismatch")
    return state


def isolated_path(path):
    path = Path(path).resolve()
    temporary = Path(tempfile.gettempdir()).resolve()
    if (
        path.name != "ledger.sqlite3"
        or not path.parent.name.startswith("hfl-paper-")
        or not path.parent.is_relative_to(temporary)
        or path.is_relative_to(ROOT)
    ):
        raise ValueError("external_temporary_synthetic_storage_required")
    return path


SCHEMA = """
PRAGMA user_version=1;
CREATE TABLE events (
 portfolio_id TEXT NOT NULL, sequence INTEGER NOT NULL,
 event_id TEXT NOT NULL UNIQUE, idempotency_key TEXT NOT NULL,
 body TEXT NOT NULL, PRIMARY KEY(portfolio_id, sequence),
 UNIQUE(portfolio_id, idempotency_key)
);
CREATE TABLE checkpoints (portfolio_id TEXT PRIMARY KEY, body TEXT NOT NULL);
CREATE TRIGGER immutable_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT, 'immutable_event'); END;
CREATE TRIGGER immutable_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT, 'immutable_event'); END;
"""


class Store:
    def __init__(self, path, *, writable=False):
        self.path = isolated_path(path) if writable else Path(path).resolve()
        self.writable = writable

    @classmethod
    def create(cls, path):
        path = isolated_path(path)
        # xb rejects an uncertain/previous creation; never truncate an existing DB.
        with path.open("xb"):
            pass
        with closing(sqlite3.connect(path)) as conn:
            conn.executescript(SCHEMA)
        return cls(path, writable=True)

    def connect(self, *, write=False):
        if write and not self.writable:
            raise ValueError("read_only_store")
        if write:
            isolated_path(self.path)
        conn = sqlite3.connect(
            self.path.as_uri() + ("?mode=rw" if write else "?mode=ro"),
            uri=True,
            timeout=10,
        )
        if write:
            conn.execute("PRAGMA synchronous=FULL")
        return conn

    @staticmethod
    def _load(conn, portfolio_id):
        # ponytail: full replay is O(n) per read/command; verified checkpoints
        # plus immutable segments are the upgrade for long ledgers.
        if (
            conn.execute("PRAGMA user_version").fetchone()[0] != VERSION
            or conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok"
        ):
            raise ValueError("database_integrity_or_schema_failed")
        rows = conn.execute(
            "SELECT sequence,event_id,idempotency_key,body FROM events WHERE portfolio_id=? ORDER BY sequence",
            (portfolio_id,),
        ).fetchall()
        events = []
        for sequence, eid, command, body in rows:
            event = json.loads(body)
            if (
                event["sequence"],
                event["event_id"],
                event["idempotency_key"],
                event["portfolio_id"],
            ) != (sequence, eid, command, portfolio_id):
                raise ValueError("database_event_index_mismatch")
            events.append(event)
        row = conn.execute(
            "SELECT body FROM checkpoints WHERE portfolio_id=?", (portfolio_id,)
        ).fetchone()
        checkpoint = (
            json.loads(row[0])
            if row
            else {"sequence": 0, "head_sha256": None, "state": None}
        )
        return replay(events, checkpoint), events, checkpoint

    def load(self, portfolio_id):
        b.key(portfolio_id)
        with closing(self.connect()) as conn:
            conn.execute("BEGIN")
            return self._load(conn, portfolio_id)

    def append(
        self,
        portfolio_id,
        kind,
        payload,
        idempotency_key,
        *,
        effective_at,
        authority="SYNTHETIC_TEST_OPERATOR",
        authorization_ref=None,
        crash=None,
    ):
        b.key(portfolio_id)
        b.key(idempotency_key)
        day = b.instant(effective_at).date().isoformat()
        request = b.pack(
            {
                "portfolio_id": portfolio_id,
                "kind": kind,
                "payload": payload,
                "effective_at": effective_at,
                "economic_date": day,
                "session": day,
                "authority": authority,
                "authorization_ref": authorization_ref,
                "source": "ISOLATED_SYNTHETIC_QUALIFICATION",
            }
        )
        with closing(self.connect(write=True)) as conn, conn:
            conn.execute("BEGIN IMMEDIATE")
            state, events, checkpoint = self._load(conn, portfolio_id)
            prior = next(
                (e for e in events if e["idempotency_key"] == idempotency_key), None
            )
            if prior:
                if any(prior[k] != v for k, v in request.items()):
                    raise ValueError("idempotency_conflict")
                return state, prior
            event = b.sealed(
                {
                    **request,
                    "schema_version": VERSION,
                    "ledger_version": IDENTITY,
                    "sequence": len(events) + 1,
                    "event_id": "evt-" + uuid.uuid4().hex,
                    "idempotency_key": idempotency_key,
                    "previous_sha256": checkpoint["head_sha256"],
                    "recorded_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            if events and b.instant(event["recorded_at"]) < b.instant(
                events[-1]["recorded_at"]
            ):
                raise ValueError("recording_clock_backwards")
            state = reduce(state, event)
            conn.execute(
                "INSERT INTO events VALUES(?,?,?,?,?)",
                (
                    portfolio_id,
                    event["sequence"],
                    event["event_id"],
                    idempotency_key,
                    canonical(event),
                ),
            )
            if crash == "after_event":
                raise RuntimeError("simulated_interruption_before_checkpoint")
            checkpoint = {
                "sequence": event["sequence"],
                "head_sha256": event["sha256"],
                "state": state,
            }
            conn.execute(
                "INSERT INTO checkpoints VALUES(?,?) ON CONFLICT(portfolio_id) DO UPDATE SET body=excluded.body",
                (portfolio_id, canonical(checkpoint)),
            )
            if crash == "before_commit":
                raise RuntimeError("simulated_interruption_before_commit")
        if crash == "after_commit":
            raise RuntimeError("simulated_lost_confirmation_after_commit")
        return state, event

    def verify(self, portfolio_id):
        try:
            state, events, checkpoint = self.load(portfolio_id)
            if state is None:
                raise ValueError("portfolio_not_found")
            report = reconciliation(state)
            if state["reconciliation_failed"]:
                report = state["reconciliations"][-1]
            return {
                "ok": not report["errors"],
                "status": report["status"],
                "errors": report["errors"],
                "events": len(events),
                "head_sha256": checkpoint["head_sha256"],
            }
        except (
            ValueError,
            KeyError,
            TypeError,
            OSError,
            ArithmeticError,
            sqlite3.Error,
        ) as exc:
            return {"ok": False, "status": "RECONCILIATION_FAILED", "errors": [str(exc)]}

    def export(self, portfolio_id):
        _, events, checkpoint = self.load(portfolio_id)
        return b.sealed(
            {
                "identity": IDENTITY,
                "classification": "SYNTHETIC_TEST",
                "events": events,
                "checkpoint": checkpoint,
            }
        )


def creation(portfolio_id, day, prices, capital="100000.00"):
    return {
        "portfolio": {
            "portfolio_id": b.key(portfolio_id),
            "ledger_version": IDENTITY,
            "display_name": "Carteira sintética · qualificação V7.6.5",
            "scientific_identity": None,
            "classification": "SYNTHETIC_TEST",
            "currency": "BRL",
            "initial_capital": capital,
            "created_at": day + "T19:00:00-03:00",
            "status": "OPEN",
            "financial_policy": b.POLICY,
            "allowed_sources": ["SYNTHETIC_TEST", "OFFICIAL_B3_RAW"],
            "authorization_ids": [],
            "provenance": ["ISOLATED_OFFLINE_FIXTURE_NOT_AN_EXPERIMENT"],
        },
        "engine_fingerprints": fingerprints(),
        "calendar_sha256": CALENDAR_SHA,
        "observation": observation(day, prices),
    }
