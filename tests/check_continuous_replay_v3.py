"""Assert-based verification suite for REPLAY-03 (scripts/continuous_replay_v3.py)."""

import asyncio
import json
import subprocess
import sys
import tempfile
from contextlib import closing
from decimal import Decimal
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(PROJECT), str(PROJECT / "scripts"), str(PROJECT / "dashboard")]

import audit_replay_v3_comparison as audit_v3
import continuous_replay_v3 as v3
import export_continuous_replay_v3 as export_v3
from continuous_replay_runtime import Budget
from src.agents.technical_evidence import (
    TechnicalEvidenceResponse,
    allowed_evidence_codes,
)
from src.experiments.h2_evaluation_offline import no_network


def _make_context(
    *,
    cash="144.46",
    positions=None,
    prices=None,
    opinions=None,
    position_memory=None,
    cost_rate_pct="0.03",
    reference_session="2026-08-24",
    target_date="2026-08-25",
):
    default_prices = {
        "PETR4": "45.00",
        "VALE3": "80.00",
        "ITUB4": "46.39",
        "WEGE3": "50.00",
        "BBAS3": "22.60",
    }
    prices = prices or default_prices
    positions = positions or {}
    default_features = {
        "sma50_gap": 0.0,
        "sma200_gap": 0.0,
        "bb_upper_gap": -0.05,
        "bb_lower_gap": 0.05,
        "bb_width": 0.10,
        "rsi": 50.0,
        "macd_ratio": 0.0,
        "macd_signal_ratio": 0.0,
    }
    opinions = opinions or {
        t: {
            "recommendation": "MANTER",
            "risk_verdict": "APROVADO",
            "confidence": 0.7,
            "features": dict(default_features),
            "individual_risk": {"verdict": "APROVADO", "risk_metrics": {"asset_volatility_21": 0.25}},
            "technical_signal": {"signal": "MANTER", "confidence": 0.7},
        }
        for t in prices
    }
    for t, op in opinions.items():
        if "features" not in op:
            op["features"] = dict(default_features)
        if "individual_risk" not in op:
            op["individual_risk"] = {
                "verdict": op.get("risk_verdict", "APROVADO"),
                "risk_metrics": {"asset_volatility_21": 0.25},
            }
        if "technical_signal" not in op:
            op["technical_signal"] = {"signal": op.get("recommendation", "MANTER"), "confidence": op.get("confidence", 0.7)}

    if position_memory is None:
        position_memory = {
            t: {
                "quantity": int(positions.get(t, 0)),
                "avg_buy_price": str(prices[t]) if int(positions.get(t, 0)) > 0 else None,
                "unrealized_return_pct": "0.00" if int(positions.get(t, 0)) > 0 else None,
                "last_sell_session": None,
                "last_sell_price": None,
                "sessions_since_last_sell": None,
            }
            for t in prices
        }

    return {
        "wallet": {
            "id": "manual-test-wallet",
            "cash": str(cash),
            "positions": [{"ticker": t, "quantity": str(q)} for t, q in positions.items() if int(q) > 0],
        },
        "reference_session": reference_session,
        "target_date": target_date,
        "prices": prices,
        "opinions": opinions,
        "position_memory": position_memory,
        "cost_rate_pct": cost_rate_pct,
        "classification": "OFFLINE_UNIT_TEST",
    }


def _raw_proposal(actions_map, summary="Teste unitário V3"):
    return {
        "summary": summary,
        "actions": [
            {
                "ticker": t,
                "side": spec[0],
                "quantity": str(spec[1]),
                "reasoning": spec[2] if len(spec) > 2 else f"Ação {spec[0]} em {t}.",
            }
            for t, spec in actions_map.items()
        ],
        "risks": ["Risco sintético de teste."],
    }


def _assert_raises_value_error(fn, expected_substr):
    try:
        fn()
    except ValueError as exc:
        assert expected_substr in str(exc), f"Expected '{expected_substr}', got '{exc}'"
    else:
        raise AssertionError(f"Expected ValueError containing '{expected_substr}', none raised")


def _run_committee(tmp_dir, data, transport, label="unit"):
    bank = v3.radar.CallBank(
        tmp_dir / f"{label}.sqlite",
        v3.b.digest({"input": v3.b.digest(data), "label": label, "identity": v3.IDENTITY}),
        v3.IDENTITY,
    )
    budget = Budget(tmp_dir / f"{label}-budget.sqlite")
    try:
        client = v3.RadarClient(
            bank,
            "L01",
            {"model": v3.radar.MODEL, "retry_attempts": 1, "retry_base_delay": 0},
            fresh=True,
            gate=lambda: None,
            transport=transport,
            synthetic=True,
            budget=budget,
            bank_name=f"{data['session']}/{data['ticker']}/{label}",
        )

        async def invoke():
            client.semaphore = asyncio.Semaphore(1)
            return await v3.committee_v3(data, client)

        with no_network():
            result = asyncio.run(invoke())
        client.assert_complete()
        return result, budget
    finally:
        bank.close()


def test_preservation():
    assert v3.IDENTITY == "HFL-CONTINUOUS-EXPLORATORY-REPLAY-V3"
    assert v3.ROOT == v3.PROJECT / "data/cache/continuous-replay/april-november-2026-flash-v3"
    assert v3.MAX_ASSET_WEIGHT == Decimal("0.30")
    assert v3.DIP_REBALANCE_MAX_WEIGHT == Decimal("0.22")
    assert v3.MIN_TRADE_BRL == Decimal("2000.00")
    assert v3.CORE_FLOOR_WEIGHT == Decimal("0.08")
    assert v3.MAX_NORMAL_SELL_FRACTION == Decimal("0.45")
    assert v3.ANTI_WHIPSAW_COOLDOWN_SESSIONS == 8
    assert v3.CASH_DRAG_THRESHOLD == Decimal("0.25")
    assert v3.STRENGTH_TRIM_MIN_WEIGHT_AFTER == Decimal("0.12")
    assert v3.STRENGTH_TRIM_MAX_FRACTION == Decimal("0.35")

    frozen = v3.radar.frozen_sources()
    assert "scripts/multiasset_radar.py" in frozen

    v1_hashes = audit_v3.verify_v1_preserved()
    v2_hashes = audit_v3.verify_v2_preserved()
    assert len(v1_hashes) == 2 and len(v2_hashes) == 2

    res = subprocess.run(
        [sys.executable, str(PROJECT / "scripts/audit_replay_positions.py")],
        cwd=str(PROJECT),
        capture_output=True,
        text=True,
        check=True,
    )
    audit_payload = json.loads(res.stdout)
    assert audit_payload["status"] == "PASS"
    assert audit_payload["daily_states_reconciled"] == 918
    assert audit_payload["asset_days_covered"] == 765
    assert audit_payload["calls"] == 4703

    with tempfile.TemporaryDirectory() as tmp:
        res_v2 = subprocess.run(
            [
                sys.executable,
                str(PROJECT / "scripts/audit_replay_v2_comparison.py"),
                "--out",
                tmp,
            ],
            cwd=str(PROJECT),
            capture_output=True,
            text=True,
            check=True,
        )
        v2_payload = json.loads(res_v2.stdout)
        assert v2_payload["status"] == "PASS"
        assert v2_payload["v2"]["daily_states_reconciled"] == 918
    print("PASS preservation: v1 & v2 export hashes, frozen_sources(), audit_replay_positions, audit_replay_v2_comparison")


def test_pilar_1_lenses_and_guards():
    expected_lenses = {
        1: "LENTE_BANDAS_BOLLINGER",
        2: "LENTE_EXAUSTAO_RSI_MACD",
        3: "LENTE_VALOR_RELATIVO_SMA50",
        4: "LENTE_ESTRUTURA_LONGA_SMA200",
        5: "LENTE_ASSIMETRIA_RISCO_RETORNO",
    }
    assert v3.ANALYST_LENSES == expected_lenses

    def make_data(features, ticker="WEGE3", day="2026-08-24", vol=0.25):
        return {
            "schema_version": 1,
            "identity": v3.radar.IDENTITY,
            "ticker": ticker,
            "session": day,
            "adjusted_close": 48.0,
            "raw_bar": {"abertura": 48.0, "maxima": 48.5, "minima": 47.5, "fechamento": 48.0, "volume": 1e6},
            "features": features,
            "risk_metrics": {"asset_volatility_21": vol},
        }

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)

        # 1. Verify 5 distinct systemInstruction prompts & TechnicalEvidenceResponse validation.
        neutral_features = {
            "sma50_gap": 0.01,
            "sma200_gap": 0.05,
            "bb_upper_gap": -0.05,
            "bb_lower_gap": 0.06,
            "bb_width": 0.11,
            "rsi": 52.0,
            "macd_ratio": 0.01,
            "macd_signal_ratio": 0.005,
        }
        seen_prompts = []

        def recording_transport(method, url, headers, body):
            prompt = json.loads(body["contents"][0]["parts"][0]["text"])
            if "allowed_evidence_codes" in prompt:
                seen_prompts.append(body["systemInstruction"]["parts"][0]["text"])
            return v3.fake_gemini_v3(method, url, headers, body)

        out_prompts, _ = _run_committee(tmp_dir, make_data(neutral_features), recording_transport, "lenses")
        assert len(seen_prompts) == 5
        assert len(set(seen_prompts)) == 5, "Each of the 5 analysts must have a unique lens prompt"
        for i, lens_name in expected_lenses.items():
            assert f"[{lens_name}]" in seen_prompts[i - 1]
        expected_codes = allowed_evidence_codes(neutral_features)
        assert out_prompts["allowed_evidence_codes"] == expected_codes
        for vote in out_prompts["votes"]:
            TechnicalEvidenceResponse.model_validate(vote["signal"])
            assert {e["code"] for e in vote["signal"]["evidence"]} <= set(expected_codes)
        assert out_prompts["committee_guard"] is None

        # 2. ANTI_BOTTOM_SELL_GUARD: 3-2 VENDA when rsi < 40 or bb_lower_gap < 0.035 (and sma200_gap > -0.08).
        bottom_features = {
            "sma50_gap": -0.05,
            "sma200_gap": -0.02,
            "bb_upper_gap": -0.14,
            "bb_lower_gap": 0.02,
            "bb_width": 0.16,
            "rsi": 36.0,
            "macd_ratio": -0.02,
            "macd_signal_ratio": -0.01,
        }
        call_idx = {"n": 0}

        def transport_3_2_venda(method, url, headers, body):
            prompt = json.loads(body["contents"][0]["parts"][0]["text"])
            if "allowed_evidence_codes" not in prompt:
                return v3._fake_wrap({"verdict": "APROVADO", "analysis": "OK", "risk_metrics": {}})
            call_idx["n"] += 1
            code = prompt["allowed_evidence_codes"][0]
            if call_idx["n"] <= 3:
                return v3._fake_wrap({"signal": "VENDA", "confidence": 0.8, "evidence": [{"code": code, "role": "SUPPORTS_VENDA"}]})
            return v3._fake_wrap({"signal": "MANTER", "confidence": 0.7, "evidence": [{"code": code, "role": "NEUTRAL"}]})

        out_ab, _ = _run_committee(tmp_dir, make_data(bottom_features), transport_3_2_venda, "anti-bottom")
        assert out_ab["consensus"]["counts"]["VENDA"] == 3
        assert out_ab["committee_guard"] == "ANTI_BOTTOM_SELL_GUARD"
        assert out_ab["technical_signal"]["signal"] == "MANTER"
        assert out_ab["technical_signal"]["confidence"] == 0.0
        assert "ANTI_BOTTOM_SELL_GUARD" in out_ab["technical_signal"]["justification"]
        assert out_ab["recommendation"] == "MANTER"

        # 3. 4-1 VENDA on the same bottom features must NOT trigger ANTI_BOTTOM_SELL_GUARD.
        call_idx["n"] = 0

        def transport_4_1_venda(method, url, headers, body):
            prompt = json.loads(body["contents"][0]["parts"][0]["text"])
            if "allowed_evidence_codes" not in prompt:
                return v3._fake_wrap({"verdict": "APROVADO", "analysis": "OK", "risk_metrics": {}})
            call_idx["n"] += 1
            code = prompt["allowed_evidence_codes"][0]
            if call_idx["n"] <= 4:
                return v3._fake_wrap({"signal": "VENDA", "confidence": 0.8, "evidence": [{"code": code, "role": "SUPPORTS_VENDA"}]})
            return v3._fake_wrap({"signal": "MANTER", "confidence": 0.7, "evidence": [{"code": code, "role": "NEUTRAL"}]})

        out_4_1, _ = _run_committee(tmp_dir, make_data(bottom_features), transport_4_1_venda, "4-1-venda")
        assert out_4_1["committee_guard"] is None
        assert out_4_1["technical_signal"]["signal"] == "VENDA"
        assert out_4_1["recommendation"] == "VENDA"

        # 4. ANTI_TOP_CHASE_GUARD: 3-2 COMPRA when rsi > 62 or bb_upper_gap > -0.02.
        top_features = {
            "sma50_gap": 0.07,
            "sma200_gap": 0.12,
            "bb_upper_gap": -0.01,
            "bb_lower_gap": 0.14,
            "bb_width": 0.15,
            "rsi": 66.0,
            "macd_ratio": 0.02,
            "macd_signal_ratio": 0.01,
        }
        call_idx["n"] = 0

        def transport_3_2_compra(method, url, headers, body):
            prompt = json.loads(body["contents"][0]["parts"][0]["text"])
            if "allowed_evidence_codes" not in prompt:
                return v3._fake_wrap({"verdict": "APROVADO", "analysis": "OK", "risk_metrics": {}})
            call_idx["n"] += 1
            code = prompt["allowed_evidence_codes"][0]
            if call_idx["n"] <= 3:
                return v3._fake_wrap({"signal": "COMPRA", "confidence": 0.8, "evidence": [{"code": code, "role": "SUPPORTS_COMPRA"}]})
            return v3._fake_wrap({"signal": "MANTER", "confidence": 0.7, "evidence": [{"code": code, "role": "NEUTRAL"}]})

        out_tc, _ = _run_committee(tmp_dir, make_data(top_features), transport_3_2_compra, "anti-top")
        assert out_tc["consensus"]["counts"]["COMPRA"] == 3
        assert out_tc["committee_guard"] == "ANTI_TOP_CHASE_GUARD"
        assert out_tc["technical_signal"]["signal"] == "MANTER"
        assert out_tc["technical_signal"]["confidence"] == 0.0
        assert "ANTI_TOP_CHASE_GUARD" in out_tc["technical_signal"]["justification"]
        assert out_tc["recommendation"] == "MANTER"

        # 5. R7 preservation: VETADO + VENDA preserves VENDA, VETADO + COMPRA becomes MANTER.
        call_idx["n"] = 0

        def transport_5_0_venda(method, url, headers, body):
            prompt = json.loads(body["contents"][0]["parts"][0]["text"])
            code = prompt["allowed_evidence_codes"][0]
            return v3._fake_wrap({"signal": "VENDA", "confidence": 0.85, "evidence": [{"code": code, "role": "SUPPORTS_VENDA"}]})

        out_r7, _ = _run_committee(tmp_dir, make_data(bottom_features, vol=0.60), transport_5_0_venda, "r7-venda")
        assert out_r7["risk_source"] == "HARD_ASSET_VOLATILITY_RULE"
        assert out_r7["risk"]["verdict"] == "VETADO"
        assert out_r7["recommendation"] == "VENDA"
    print("PASS Pilar 1: 5 unique lenses, ANTI_BOTTOM_SELL_GUARD, ANTI_TOP_CHASE_GUARD, R7 preserved")


def test_pilar_2_core_floor_and_anti_whipsaw():
    # Setup: equity = 100,000 -> PETR4: 1000 * 45 = 45,000 (45%), WEGE3: 700 * 50 = 35,000 (35%), cash = 20,000.
    opinions = {
        "PETR4": {"recommendation": "VENDA", "risk_verdict": "APROVADO", "confidence": 0.8},
        "WEGE3": {"recommendation": "VENDA", "risk_verdict": "VETADO", "confidence": 0.8},
        "ITUB4": {"recommendation": "COMPRA", "risk_verdict": "APROVADO", "confidence": 0.8},
        "VALE3": {"recommendation": "COMPRA", "risk_verdict": "APROVADO", "confidence": 0.8},
        "BBAS3": {"recommendation": "MANTER", "risk_verdict": "APROVADO", "confidence": 0.6},
    }
    mem = {
        "PETR4": {"quantity": 1000, "avg_buy_price": "44.00", "unrealized_return_pct": "2.27", "last_sell_session": None, "last_sell_price": None, "sessions_since_last_sell": None},
        "WEGE3": {"quantity": 700, "avg_buy_price": "52.00", "unrealized_return_pct": "-3.85", "last_sell_session": None, "last_sell_price": None, "sessions_since_last_sell": None},
        "ITUB4": {"quantity": 0, "avg_buy_price": None, "unrealized_return_pct": None, "last_sell_session": "2026-08-18", "last_sell_price": "45.00", "sessions_since_last_sell": 4},
        "VALE3": {"quantity": 0, "avg_buy_price": None, "unrealized_return_pct": None, "last_sell_session": "2026-08-18", "last_sell_price": "82.00", "sessions_since_last_sell": 4},
        "BBAS3": {"quantity": 0, "avg_buy_price": None, "unrealized_return_pct": None, "last_sell_session": None, "last_sell_price": None, "sessions_since_last_sell": None},
    }
    ctx = _make_context(
        cash="20000.00",
        positions={"PETR4": 1000, "WEGE3": 700},
        opinions=opinions,
        position_memory=mem,
    )

    # 1. Normal APROVADO VENDA trying to sell 100% (1000 PETR4) fails strict mode.
    raw_full_sell = _raw_proposal(
        {"PETR4": ("SELL", "1000"), "WEGE3": ("HOLD", "0"), "ITUB4": ("HOLD", "0"), "VALE3": ("HOLD", "0"), "BBAS3": ("HOLD", "0")}
    )
    _assert_raises_value_error(
        lambda: v3.compile_proposal_v3(ctx, raw_full_sell, strict=True),
        "manager_core_floor_or_step_sell_exceeded",
    )

    # Non-strict clamps PETR4 SELL to max 45% (450 shares, leaving 550 * 45 = 24,750 = 24.75% >= 8% floor).
    compiled_step = v3.compile_proposal_v3(ctx, raw_full_sell, strict=False)
    assert compiled_step["trades"][0]["quantity"] == "450"
    assert compiled_step["adjustments"][0]["reason"] == "CORE_FLOOR_STEP_SELL"

    # 2. Core Floor (8%) binds when 45% step would breach 8% floor:
    # Suppose PETR4 holds 200 shares * 45 = 9,000 (9% of 100,000); 8% = 8,000 -> ceil(8000/45)=178 shares must remain -> max sell = 22.
    ctx_small = _make_context(
        cash="56000.00",
        positions={"PETR4": 200, "WEGE3": 700},  # 9k + 35k + 56k = 100k
        opinions=opinions,
    )
    raw_small = _raw_proposal(
        {"PETR4": ("SELL", "80"), "WEGE3": ("HOLD", "0"), "ITUB4": ("HOLD", "0"), "VALE3": ("HOLD", "0"), "BBAS3": ("HOLD", "0")}
    )
    compiled_floor = v3.compile_proposal_v3(ctx_small, raw_small, strict=False)
    assert compiled_floor["trades"][0]["quantity"] == "22"
    assert compiled_floor["adjustments"][0]["reason"] == "CORE_FLOOR_STEP_SELL"
    row_petr = next(r for r in compiled_floor["rows"] if r["ticker"] == "PETR4")
    assert Decimal(row_petr["value_after"]) / Decimal(compiled_floor["equity_before"]) >= Decimal("0.08")

    # 3. R7 VENDA under VETADO (WEGE3) still allows 100% full exit!
    raw_r7_full = _raw_proposal(
        {"PETR4": ("HOLD", "0"), "WEGE3": ("SELL", "700"), "ITUB4": ("HOLD", "0"), "VALE3": ("HOLD", "0"), "BBAS3": ("HOLD", "0")}
    )
    compiled_r7 = v3.compile_proposal_v3(ctx, raw_r7_full, strict=True)
    assert compiled_r7["trades"] == [{"ticker": "WEGE3", "side": "SELL", "quantity": "700", "price": "50.00", "costs": "10.50"}]

    # 4. Anti-Whipsaw: ITUB4 sold 4 sessions ago at 45.00, current price 46.39 (> 45.00) -> blocked!
    raw_whipsaw = _raw_proposal(
        {"PETR4": ("HOLD", "0"), "WEGE3": ("HOLD", "0"), "ITUB4": ("BUY", "200"), "VALE3": ("HOLD", "0"), "BBAS3": ("HOLD", "0")}
    )
    _assert_raises_value_error(
        lambda: v3.compile_proposal_v3(ctx, raw_whipsaw, strict=True),
        "manager_anti_whipsaw_higher_rebuy",
    )
    compiled_ws = v3.compile_proposal_v3(ctx, raw_whipsaw, strict=False)
    assert compiled_ws["trades"] == []
    assert compiled_ws["adjustments"] == [
        {
            "ticker": "ITUB4",
            "from_side": "BUY",
            "from_quantity": "200",
            "to_side": "HOLD",
            "to_quantity": "0",
            "reason": "ANTI_WHIPSAW_HIGHER_REBUY",
        }
    ]

    # 5. Lower-price rebuy within 8 sessions (VALE3 sold at 82.00, current 80.00 <= 82.00) is ALLOWED.
    raw_lower_rebuy = _raw_proposal(
        {"PETR4": ("HOLD", "0"), "WEGE3": ("HOLD", "0"), "ITUB4": ("HOLD", "0"), "VALE3": ("BUY", "100"), "BBAS3": ("HOLD", "0")}
    )
    compiled_lr = v3.compile_proposal_v3(ctx, raw_lower_rebuy, strict=True)
    assert compiled_lr["trades"][0]["ticker"] == "VALE3" and compiled_lr["trades"][0]["side"] == "BUY"

    # 6. Higher-price rebuy AFTER > 8 sessions (sessions_since_last_sell = 9) is ALLOWED.
    mem_expired = {**mem, "ITUB4": {**mem["ITUB4"], "sessions_since_last_sell": 9}}
    ctx_expired = _make_context(cash="20000.00", positions={"PETR4": 1000, "WEGE3": 700}, opinions=opinions, position_memory=mem_expired)
    compiled_exp = v3.compile_proposal_v3(ctx_expired, raw_whipsaw, strict=True)
    assert compiled_exp["trades"][0]["ticker"] == "ITUB4" and compiled_exp["trades"][0]["side"] == "BUY"
    print("PASS Pilar 2: CORE_FLOOR_STEP_SELL (45% step + 8% floor), R7 100% exit, ANTI_WHIPSAW_HIGHER_REBUY")


def test_pilar_3_trim_on_strength():
    # Setup: PETR4 weight = 20% (444 * 45 = 19,980 / 100,000), avg_buy_price = 40.00 (price 45.00 = +12.5% >= +2%),
    # recommendation = MANTER, rsi = 66 >= 63, NO BUY in basket!
    opinions = {
        "PETR4": {
            "recommendation": "MANTER",
            "risk_verdict": "APROVADO",
            "confidence": 0.7,
            "features": {"sma50_gap": 0.06, "sma200_gap": 0.10, "bb_upper_gap": -0.01, "bb_lower_gap": 0.12, "bb_width": 0.13, "rsi": 66.0, "macd_ratio": 0.02, "macd_signal_ratio": 0.01},
        },
        "VALE3": {"recommendation": "MANTER", "risk_verdict": "APROVADO", "confidence": 0.6},
        "ITUB4": {"recommendation": "MANTER", "risk_verdict": "APROVADO", "confidence": 0.6},
        "WEGE3": {"recommendation": "MANTER", "risk_verdict": "APROVADO", "confidence": 0.6},
        "BBAS3": {"recommendation": "MANTER", "risk_verdict": "APROVADO", "confidence": 0.6},
    }
    mem = {
        "PETR4": {"quantity": 444, "avg_buy_price": "40.00", "unrealized_return_pct": "12.50", "last_sell_session": None, "last_sell_price": None, "sessions_since_last_sell": None},
        "VALE3": {"quantity": 250, "avg_buy_price": "80.00", "unrealized_return_pct": "0.00", "last_sell_session": None, "last_sell_price": None, "sessions_since_last_sell": None},
        "ITUB4": {"quantity": 0, "avg_buy_price": None, "unrealized_return_pct": None, "last_sell_session": None, "last_sell_price": None, "sessions_since_last_sell": None},
        "WEGE3": {"quantity": 400, "avg_buy_price": "50.00", "unrealized_return_pct": "0.00", "last_sell_session": None, "last_sell_price": None, "sessions_since_last_sell": None},
        "BBAS3": {"quantity": 0, "avg_buy_price": None, "unrealized_return_pct": None, "last_sell_session": None, "last_sell_price": None, "sessions_since_last_sell": None},
    }
    # 444*45=19980, 250*80=20000, 400*50=20000, cash=40020 -> equity=100,000.
    ctx = _make_context(
        cash="40020.00",
        positions={"PETR4": 444, "VALE3": 250, "WEGE3": 400},
        opinions=opinions,
        position_memory=mem,
    )

    # 1. Valid Trim-on-Strength without any BUY: sell 150 PETR4 (<= ceil(444*0.35)=156, leaves 294*45=13,230 = 13.23% >= 12%).
    raw_strength = _raw_proposal(
        {"PETR4": ("SELL", "150"), "VALE3": ("HOLD", "0"), "ITUB4": ("HOLD", "0"), "WEGE3": ("HOLD", "0"), "BBAS3": ("HOLD", "0")}
    )
    compiled = v3.compile_proposal_v3(ctx, raw_strength, strict=True)
    assert len(compiled["trades"]) == 1
    assert compiled["trades"][0]["ticker"] == "PETR4" and compiled["trades"][0]["quantity"] == "150"

    # 2. Exceeding 35% / 12% floor in non-strict mode clamps with STRENGTH_TRIM_FLOOR_CAP.
    raw_over_strength = _raw_proposal(
        {"PETR4": ("SELL", "300"), "VALE3": ("HOLD", "0"), "ITUB4": ("HOLD", "0"), "WEGE3": ("HOLD", "0"), "BBAS3": ("HOLD", "0")}
    )
    compiled_clamp = v3.compile_proposal_v3(ctx, raw_over_strength, strict=False)
    assert compiled_clamp["adjustments"][0]["reason"] == "STRENGTH_TRIM_FLOOR_CAP"
    assert int(compiled_clamp["trades"][0]["quantity"]) == 156
    row_petr = next(r for r in compiled_clamp["rows"] if r["ticker"] == "PETR4")
    assert Decimal(row_petr["value_after"]) / Decimal(compiled_clamp["equity_before"]) >= Decimal("0.12")

    # 3. Negative: if price < avg_buy_price * 1.02 (e.g. avg_buy_price = 44.50 -> 44.50*1.02 = 45.39 > 45.00), Trim-on-Strength is NOT eligible.
    mem_no_gain = {**mem, "PETR4": {**mem["PETR4"], "avg_buy_price": "44.50"}}
    ctx_no_gain = _make_context(cash="40020.00", positions={"PETR4": 444, "VALE3": 250, "WEGE3": 400}, opinions=opinions, position_memory=mem_no_gain)
    _assert_raises_value_error(
        lambda: v3.compile_proposal_v3(ctx_no_gain, raw_strength, strict=True),
        "manager_trim_weight_before_too_low",
    )
    print("PASS Pilar 3 (Trim-on-Strength): partial SELL on MANTER without BUY, STRENGTH_TRIM_FLOOR_CAP, gain check")


def test_pilar_4_anti_cash_drag():
    # Setup: cash = 40,000 / equity = 100,000 (40% > 25% threshold).
    # VALE3 is MANTER + APROVADO, discounted (sma50_gap=-0.04 < 0, rsi=42 <= 46).
    # WEGE3 is MANTER + APROVADO, NOT discounted (sma50_gap=0.02, rsi=55, bb_lower_gap=0.08).
    opinions = {
        "PETR4": {"recommendation": "MANTER", "risk_verdict": "APROVADO", "confidence": 0.6},
        "VALE3": {
            "recommendation": "MANTER",
            "risk_verdict": "APROVADO",
            "confidence": 0.65,
            "features": {"sma50_gap": -0.04, "sma200_gap": 0.02, "bb_upper_gap": -0.10, "bb_lower_gap": 0.03, "bb_width": 0.13, "rsi": 42.0, "macd_ratio": -0.01, "macd_signal_ratio": -0.005},
        },
        "ITUB4": {"recommendation": "MANTER", "risk_verdict": "APROVADO", "confidence": 0.6},
        "WEGE3": {
            "recommendation": "MANTER",
            "risk_verdict": "APROVADO",
            "confidence": 0.6,
            "features": {"sma50_gap": 0.02, "sma200_gap": 0.04, "bb_upper_gap": -0.06, "bb_lower_gap": 0.08, "bb_width": 0.14, "rsi": 55.0, "macd_ratio": 0.01, "macd_signal_ratio": 0.005},
        },
        "BBAS3": {"recommendation": "MANTER", "risk_verdict": "APROVADO", "confidence": 0.6},
    }
    ctx_high_cash = _make_context(
        cash="40000.00",
        positions={"PETR4": 400, "VALE3": 100, "WEGE3": 680},  # 18k + 8k + 34k + 40k cash = 100k
        opinions=opinions,
    )

    # 1. Dip-Rebalance BUY on VALE3 clamped to 22% (22,000 / 80 = 275 total -> max buy = 175 shares = R$ 14,000).
    raw_dip = _raw_proposal(
        {"VALE3": ("BUY", "250"), "PETR4": ("HOLD", "0"), "ITUB4": ("HOLD", "0"), "WEGE3": ("HOLD", "0"), "BBAS3": ("HOLD", "0")}
    )
    compiled_dip = v3.compile_proposal_v3(ctx_high_cash, raw_dip, strict=False)
    assert len(compiled_dip["trades"]) == 1
    assert compiled_dip["trades"][0]["ticker"] == "VALE3"
    assert compiled_dip["trades"][0]["quantity"] == "175"
    assert compiled_dip["adjustments"] == [
        {
            "ticker": "VALE3",
            "from_side": "BUY",
            "from_quantity": "250",
            "to_side": "BUY",
            "to_quantity": "175",
            "reason": "DIP_REBALANCE_WEIGHT_CAP",
        }
    ]
    row_vale = next(r for r in compiled_dip["rows"] if r["ticker"] == "VALE3")
    assert Decimal(row_vale["value_after"]) / Decimal(compiled_dip["equity_before"]) <= Decimal("0.22")

    # 2. Non-discounted MANTER (WEGE3) cannot be bought even with high cash.
    raw_not_discounted = _raw_proposal(
        {"VALE3": ("HOLD", "0"), "PETR4": ("HOLD", "0"), "ITUB4": ("HOLD", "0"), "WEGE3": ("BUY", "100"), "BBAS3": ("HOLD", "0")}
    )
    _assert_raises_value_error(
        lambda: v3.compile_proposal_v3(ctx_high_cash, raw_not_discounted, strict=True),
        "manager_operation_incompatible_with_opinion",
    )

    # 3. Low cash (cash/equity = 20% <= 25%) blocks Dip-Rebalance BUY on discounted MANTER.
    ctx_low_cash = _make_context(
        cash="20000.00",
        positions={"PETR4": 400, "VALE3": 100, "WEGE3": 1080},  # 18k + 8k + 54k + 20k = 100k
        opinions=opinions,
    )
    _assert_raises_value_error(
        lambda: v3.compile_proposal_v3(ctx_low_cash, raw_dip, strict=True),
        "manager_operation_incompatible_with_opinion",
    )
    print("PASS Pilar 4 (Anti-Cash-Drag / Dip-Rebalance): 22% cap on discounted MANTER when cash > 25%, blocks otherwise")


def test_preflight_and_offline_e2e():
    # 1. Verify preflight() under no_network() and via CLI --preflight.
    with no_network():
        pf = v3.preflight()
    assert pf["identity"] == "HFL-CONTINUOUS-EXPLORATORY-REPLAY-V3"
    assert pf["sessions_count"] == 153
    assert pf["logical_calls_max"] == 153 * 31
    assert pf["hard_volatility_vetoes_skipped"] == 40
    assert pf["logical_calls_estimate"] == 4703
    assert pf["no_network_calls_made"] is True

    cli_pf = subprocess.run(
        [sys.executable, str(PROJECT / "scripts/continuous_replay_v3.py"), "--preflight"],
        cwd=str(PROJECT),
        capture_output=True,
        text=True,
        check=True,
    )
    cli_pf_json = json.loads(cli_pf.stdout)
    assert cli_pf_json["logical_calls_estimate"] == 4703

    # 2. Multi-session 5-day offline execution, idempotent resume, export, and audit comparison.
    old_manual_root = v3.manual.ROOT
    old_market_root = v3.market.ROOT
    old_session_rows = v3.orders.session_rows
    try:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v3-offline"
            with no_network():
                res = v3.execute(root, offline=True, count=5)
            assert res["identity"] == "HFL-CONTINUOUS-EXPLORATORY-REPLAY-V3"
            assert res["sessions_completed"] == 5
            assert res["complete_analysis_days"] == 5
            assert res["gaps"] == []
            assert res["budget"]["unknown_attempts"] == 0
            assert Decimal(res["budget"]["exposure_usd"]) <= Decimal("34.78")
            assert (root / "summary.json").exists()
            assert (root / "daily.csv").exists()
            assert (root / "references_complete.json").exists()

            with closing(v3.manual.connect()) as conn:
                wallets = v3.manual.catalog(conn)
                assert {w["strategy"] for w in wallets} == set(v3.STRATEGIES)
                for w in wallets:
                    v3.manual.replay(v3.manual.events(conn, w["id"]))

            for day_path in sorted((root / "sessions").glob("*/day.json")):
                day_data = v3.checked(day_path)
                assert day_data["status"] == "COMPLETED"
                ctx_day = v3.checked(day_path.parent / "manager/context.json")
                assert "position_memory" in ctx_day
                prop = v3.checked(day_path.parent / "manager/proposal.json")
                eq_before = Decimal(prop["equity_before"])
                for tr in prop["trades"]:
                    if tr["side"] == "BUY":
                        gross = Decimal(tr["quantity"]) * Decimal(tr["price"])
                        assert gross >= v3.MIN_TRADE_BRL, (day_data["day"], tr)
                for row in prop["rows"]:
                    if row["side"] == "BUY":
                        rec = ctx_day["opinions"][row["ticker"]]["recommendation"]
                        cap = v3.DIP_REBALANCE_MAX_WEIGHT if rec == "MANTER" else v3.MAX_ASSET_WEIGHT
                        assert Decimal(row["value_after"]) / eq_before <= cap

            ctx_last = v3.checked(root / "sessions/2026-04-10/manager/context.json")
            petr_mem = ctx_last["position_memory"]["PETR4"]
            assert petr_mem["last_sell_session"] == "2026-04-07"
            assert petr_mem["sessions_since_last_sell"] == 3
            assert petr_mem["avg_buy_price"] is not None
            assert petr_mem["unrealized_return_pct"] is not None

            # Idempotent resume must perform zero extra physical calls.
            attempts_before = res["budget"]["physical_attempts"]
            with no_network():
                res2 = v3.execute(root, offline=True, count=5)
            assert res2["budget"]["physical_attempts"] == attempts_before

            # Export v3 artifacts and verify audit_replay_v3_comparison on the partial export.
            mirror_dir = Path(tmp) / "mirror-exports"
            with no_network():
                exp_summary = export_v3.export(root, mirror=mirror_dir)
            expected_files = (
                "daily.csv",
                "operations.csv",
                "decisions.csv",
                "dividends.csv",
                "calls.csv",
                "explorer.json",
                "calls.json",
                "manifest.json",
                "index.html",
                "calls-data.js",
                "abrir_explorador.py",
                "LEIA-ME.txt",
            )
            for fname in expected_files:
                assert (root / "exports" / fname).exists(), f"missing export {fname}"
                assert (mirror_dir / fname).exists(), f"missing mirror {fname}"
            assert exp_summary["daily_sessions"] == 5
            assert exp_summary["daily_wallet_states"] == 30
            assert exp_summary["budget_audit"]["status"] == "PASS"

            comp_out = Path(tmp) / "audit-out"
            comp = audit_v3.run_comparison(
                v3_dir=root / "exports",
                out_dir=comp_out,
                allow_partial=True,
            )
            assert comp["status"] == "PASS"
            assert all(comp["reference_parity_v1_v2"].values())
            assert all(comp["reference_parity_v1_v3"].values())
            assert comp["v3"]["daily_states_reconciled"] == 30
            assert len(comp["v3"]["concentration"]["dust_buys_below_2000"]) == 0
            assert comp["v3"]["full_exits_non_r7"] == 0
            assert (comp_out / "comparacao_v1_v2_v3.json").exists()
            assert (comp_out / "comparacao_carteiras.csv").exists()
            assert (comp_out / "atribuicao_v1_v2_v3.csv").exists()
            assert (comp_out / "committee_guards_v3.csv").exists()
            assert (comp_out / "trim_on_strength_v3.csv").exists()
            assert (comp_out / "dip_rebalance_buys_v3.csv").exists()
    finally:
        v3.manual.ROOT = old_manual_root
        v3.market.ROOT = old_market_root
        v3.orders.session_rows = old_session_rows
    print("PASS preflight & offline E2E: --preflight (153 sessions, 4703 calls), 5-session offline, idempotent resume, export & v1/v2/v3 comparison")


if __name__ == "__main__":
    test_preservation()
    test_pilar_1_lenses_and_guards()
    test_pilar_2_core_floor_and_anti_whipsaw()
    test_pilar_3_trim_on_strength()
    test_pilar_4_anti_cash_drag()
    test_preflight_and_offline_e2e()
    print("ALL CHECKS PASSED: continuous_replay_v3 verified")
