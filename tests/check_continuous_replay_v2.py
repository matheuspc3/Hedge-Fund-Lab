"""Assert-based verification suite for REPLAY-02 (scripts/continuous_replay_v2.py)."""

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

import audit_replay_v2_comparison as audit_v2
import continuous_replay_v2 as v2
import export_continuous_replay_v2 as export_v2
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
            "features": default_features,
            "individual_risk": {"verdict": "APROVADO", "risk_metrics": {"asset_volatility_21": 0.25}},
            "technical_signal": {"signal": "MANTER", "confidence": 0.7},
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
        "cost_rate_pct": cost_rate_pct,
        "classification": "OFFLINE_UNIT_TEST",
    }


def _raw_proposal(actions_map, summary="Teste unitário V2"):
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
    bank = v2.radar.CallBank(
        tmp_dir / f"{label}.sqlite",
        v2.b.digest({"input": v2.b.digest(data), "label": label, "identity": v2.IDENTITY}),
        v2.IDENTITY,
    )
    budget = Budget(tmp_dir / f"{label}-budget.sqlite")
    try:
        client = v2.RadarClient(
            bank,
            "L01",
            {"model": v2.radar.MODEL, "retry_attempts": 1, "retry_base_delay": 0},
            fresh=True,
            gate=lambda: None,
            transport=transport,
            synthetic=True,
            budget=budget,
            bank_name=f"{data['session']}/{data['ticker']}/{label}",
        )

        async def invoke():
            client.semaphore = asyncio.Semaphore(1)
            return await v2.committee_v2(data, client)

        with no_network():
            result = asyncio.run(invoke())
        client.assert_complete()
        return result, budget
    finally:
        bank.close()


def test_preservation():
    assert v2.IDENTITY == "HFL-CONTINUOUS-EXPLORATORY-REPLAY-V2"
    assert v2.ROOT == v2.PROJECT / "data/cache/continuous-replay/april-november-2026-flash-v2"
    assert v2.MAX_ASSET_WEIGHT == Decimal("0.30")
    assert v2.MIN_TRADE_BRL == Decimal("2000.00")
    assert v2.TRIM_MIN_WEIGHT_BEFORE == Decimal("0.25")
    assert v2.TRIM_MIN_WEIGHT_AFTER == Decimal("0.15")

    frozen = v2.radar.frozen_sources()
    assert "scripts/multiasset_radar.py" in frozen

    # Verify v1 audit script still passes 100% without touching frozen v1 artifacts.
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
    print("PASS preservation: frozen_sources(), v2 identity/constants, and audit_replay_positions.py (918 states)")


def test_gargalo_1_trim_to_fund():
    # Real-like 2026-08-25 state: cash = R$ 144.46, PETR4 > 60% in MANTER, VALE3 = 0 in COMPRA + APROVADO.
    base_opinions = {
        "PETR4": {"recommendation": "MANTER", "risk_verdict": "APROVADO", "confidence": 0.7},
        "VALE3": {"recommendation": "COMPRA", "risk_verdict": "APROVADO", "confidence": 0.8},
        "ITUB4": {"recommendation": "MANTER", "risk_verdict": "APROVADO", "confidence": 0.6},
        "WEGE3": {"recommendation": "MANTER", "risk_verdict": "APROVADO", "confidence": 0.6},
        "BBAS3": {"recommendation": "MANTER", "risk_verdict": "APROVADO", "confidence": 0.6},
    }
    ctx = _make_context(
        cash="144.46",
        positions={"PETR4": 1400, "WEGE3": 700, "ITUB4": 40, "VALE3": 0, "BBAS3": 0},
        opinions=base_opinions,
    )
    # 1. Valid Trim-to-Fund: sell 500 PETR4 (weight_after ~40.5% >= 15%) to fund BUY 250 VALE3 (R$ 20,000 <= 30%).
    raw = _raw_proposal(
        {
            "PETR4": ("SELL", "500", "Trim-to-Fund parcial em PETR4 acima de 25%"),
            "VALE3": ("BUY", "250", "Entrada em VALE3 financiada pelo trim"),
            "ITUB4": ("HOLD", "0"),
            "WEGE3": ("HOLD", "0"),
            "BBAS3": ("HOLD", "0"),
        }
    )
    compiled = v2.compile_proposal_v2(ctx, raw)
    assert len(compiled["trades"]) == 2
    assert Decimal(compiled["cash_after"]) > Decimal("2000.00")
    by_ticker = {r["ticker"]: r for r in compiled["rows"]}
    assert Decimal(by_ticker["PETR4"]["weight_before"]) > Decimal("0.60")
    assert Decimal(by_ticker["PETR4"]["weight_after"]) >= Decimal("0.15")
    assert Decimal(by_ticker["VALE3"]["weight_after"]) <= Decimal("0.30")

    # 2. Same Trim-to-Fund with BUY listed before SELL in raw actions must also settle SELL first.
    raw_buy_first = _raw_proposal(
        {
            "VALE3": ("BUY", "250"),
            "PETR4": ("SELL", "500"),
            "ITUB4": ("HOLD", "0"),
            "WEGE3": ("HOLD", "0"),
            "BBAS3": ("HOLD", "0"),
        }
    )
    compiled_bf = v2.compile_proposal_v2(ctx, raw_buy_first)
    assert compiled_bf["cash_after"] == compiled["cash_after"]

    # 3. Trim on COMPRA asset > 25% to fund another COMPRA asset is allowed if weight_after >= 15%.
    compra_opinions = {**base_opinions, "PETR4": {"recommendation": "COMPRA", "risk_verdict": "APROVADO", "confidence": 0.7}}
    ctx_compra = _make_context(
        cash="144.46",
        positions={"PETR4": 1400, "WEGE3": 700, "ITUB4": 40},
        opinions=compra_opinions,
    )
    compiled_c = v2.compile_proposal_v2(ctx_compra, raw)
    assert len(compiled_c["trades"]) == 2

    # 4. Trim on overweight > 30% MANTER without any BUY is allowed (weight_before > MAX_ASSET_WEIGHT).
    raw_overweight_only = _raw_proposal(
        {
            "PETR4": ("SELL", "700"),  # leaves 700 * 45 = 31,500 (~31.5% >= 15%)
            "VALE3": ("HOLD", "0"),
            "ITUB4": ("HOLD", "0"),
            "WEGE3": ("HOLD", "0"),
            "BBAS3": ("HOLD", "0"),
        }
    )
    compiled_ow = v2.compile_proposal_v2(ctx, raw_overweight_only)
    assert len(compiled_ow["trades"]) == 1 and compiled_ow["trades"][0]["ticker"] == "PETR4"

    # 5. Negative: selling MANTER when weight_before <= 25% (exact 25.00% = 500 WEGE3 @ 50 = 25,000 / 100,000).
    ctx_25 = _make_context(
        cash="25000.00",
        positions={"PETR4": 555, "WEGE3": 500, "ITUB4": 500, "BBAS3": 0, "VALE3": 0},
        prices={"PETR4": "45.00", "WEGE3": "50.00", "ITUB4": "50.05", "BBAS3": "22.60", "VALE3": "80.00"},
        opinions=base_opinions,
    )
    # WEGE3 value = 25,000; equity = 25,000 + 24,975 + 25,000 + 25,025 = 100,000 => weight_before = 0.25 exactly.
    raw_sell_25 = _raw_proposal(
        {
            "WEGE3": ("SELL", "100"),
            "VALE3": ("BUY", "100"),
            "PETR4": ("HOLD", "0"),
            "ITUB4": ("HOLD", "0"),
            "BBAS3": ("HOLD", "0"),
        }
    )
    _assert_raises_value_error(
        lambda: v2.compile_proposal_v2(ctx_25, raw_sell_25),
        "manager_trim_weight_before_too_low",
    )

    # 6. Negative: reducing MANTER below 15% floor (1400 PETR4 -> sell 1100 leaves 300*45=13,500 = 13.5% < 15%).
    raw_below_floor = _raw_proposal(
        {
            "PETR4": ("SELL", "1100"),
            "VALE3": ("BUY", "250"),
            "ITUB4": ("HOLD", "0"),
            "WEGE3": ("HOLD", "0"),
            "BBAS3": ("HOLD", "0"),
        }
    )
    _assert_raises_value_error(
        lambda: v2.compile_proposal_v2(ctx, raw_below_floor),
        "manager_trim_weight_after_below_floor",
    )

    # 7. Negative: zeroing out MANTER completely without VENDA signal.
    raw_zero_out = _raw_proposal(
        {
            "PETR4": ("SELL", "1400"),
            "VALE3": ("BUY", "250"),
            "ITUB4": ("HOLD", "0"),
            "WEGE3": ("HOLD", "0"),
            "BBAS3": ("HOLD", "0"),
        }
    )
    _assert_raises_value_error(
        lambda: v2.compile_proposal_v2(ctx, raw_zero_out),
        "manager_trim_weight_after_below_floor",
    )

    # 8. Negative: selling MANTER with 25% < weight_before <= 30% (28%) when no BUY survives (dust BUY clamped to HOLD).
    ctx_28 = _make_context(
        cash="44000.00",
        positions={"PETR4": 0, "WEGE3": 560, "ITUB4": 560, "BBAS3": 0, "VALE3": 0},
        prices={"PETR4": "45.00", "WEGE3": "50.00", "ITUB4": "50.00", "BBAS3": "22.60", "VALE3": "80.00"},
        opinions=base_opinions,
    )
    # WEGE3 weight = 28,000 / 100,000 = 0.28 (between 0.25 and 0.30).
    raw_dust_buy_trim = _raw_proposal(
        {
            "WEGE3": ("SELL", "100"),  # leaves 23% >= 15%
            "VALE3": ("BUY", "10"),    # R$ 800 < R$ 2,000 -> clamped to HOLD!
            "PETR4": ("HOLD", "0"),
            "ITUB4": ("HOLD", "0"),
            "BBAS3": ("HOLD", "0"),
        }
    )
    _assert_raises_value_error(
        lambda: v2.compile_proposal_v2(ctx_28, raw_dust_buy_trim),
        "manager_trim_requires_buy_or_overweight",
    )
    print("PASS Gargalo 1 (Trim-to-Fund): 2026-08-25 scenario, ordering, overweight, <=25% & <15% & no-surviving-BUY rejections")


def test_gargalo_2_cap_and_min_trade():
    opinions = {
        "PETR4": {"recommendation": "MANTER", "risk_verdict": "APROVADO", "confidence": 0.7},
        "VALE3": {"recommendation": "COMPRA", "risk_verdict": "APROVADO", "confidence": 0.8},
        "ITUB4": {"recommendation": "MANTER", "risk_verdict": "APROVADO", "confidence": 0.6},
        "WEGE3": {"recommendation": "MANTER", "risk_verdict": "APROVADO", "confidence": 0.6},
        "BBAS3": {"recommendation": "COMPRA", "risk_verdict": "APROVADO", "confidence": 0.7},
    }
    # 1. BUY exceeding 30% weight is deterministically clamped to <= 30%.
    ctx = _make_context(
        cash="50000.00",
        positions={"VALE3": 100, "PETR4": 400, "WEGE3": 480},  # 8k + 18k + 24k + 50k cash = 100,000
        opinions=opinions,
    )
    raw_over = _raw_proposal(
        {
            "VALE3": ("BUY", "400"),  # would reach 500 * 80 = 40,000 (40%); max after = 375 -> buy 275
            "PETR4": ("HOLD", "0"),
            "ITUB4": ("HOLD", "0"),
            "WEGE3": ("HOLD", "0"),
            "BBAS3": ("HOLD", "0"),
        }
    )
    compiled_over = v2.compile_proposal_v2(ctx, raw_over)
    assert len(compiled_over["trades"]) == 1
    assert compiled_over["trades"][0]["quantity"] == "275"
    assert compiled_over["adjustments"][0]["reason"] == "MAX_ASSET_WEIGHT_CAP"
    row_vale = next(r for r in compiled_over["rows"] if r["ticker"] == "VALE3")
    assert Decimal(row_vale["value_after"]) / Decimal(compiled_over["equity_before"]) <= Decimal("0.30")

    # 2. Dust BUY (3 shares of BBAS3 at R$ 22.60 = R$ 67.80 < R$ 2,000) is clamped to HOLD ("0").
    raw_dust = _raw_proposal(
        {
            "BBAS3": ("BUY", "3"),
            "PETR4": ("HOLD", "0"),
            "VALE3": ("HOLD", "0"),
            "ITUB4": ("HOLD", "0"),
            "WEGE3": ("HOLD", "0"),
        }
    )
    compiled_dust = v2.compile_proposal_v2(ctx, raw_dust)
    assert compiled_dust["trades"] == []
    assert compiled_dust["adjustments"] == [
        {
            "ticker": "BBAS3",
            "from_side": "BUY",
            "from_quantity": "3",
            "to_side": "HOLD",
            "to_quantity": "0",
            "reason": "MIN_TRADE_BRL",
        }
    ]

    # 3. BUY clamped by 30% cap whose remaining room is < R$ 2,000 also clamps down to HOLD via MIN_TRADE_BRL.
    ctx_near_cap = _make_context(
        cash="30000.00",
        positions={"VALE3": 360, "PETR4": 400, "WEGE3": 464},  # 28,800 + 18,000 + 23,200 + 30,000 = 100,000
        opinions=opinions,
    )
    raw_cap_then_dust = _raw_proposal(
        {
            "VALE3": ("BUY", "50"),  # cap allows only 15 shares (R$ 1,200 < R$ 2,000) -> HOLD
            "PETR4": ("HOLD", "0"),
            "ITUB4": ("HOLD", "0"),
            "WEGE3": ("HOLD", "0"),
            "BBAS3": ("HOLD", "0"),
        }
    )
    compiled_ctd = v2.compile_proposal_v2(ctx_near_cap, raw_cap_then_dust)
    assert compiled_ctd["trades"] == []
    assert [a["reason"] for a in compiled_ctd["adjustments"]] == [
        "MAX_ASSET_WEIGHT_CAP",
        "MIN_TRADE_BRL",
    ]

    # 4. Small SELL (13 shares of BBAS3 = R$ 293.80 < R$ 2,000) to exit under VENDA is allowed.
    opinions_sell = {
        **opinions,
        "BBAS3": {"recommendation": "VENDA", "risk_verdict": "VETADO", "confidence": 0.8},
    }
    ctx_exit = _make_context(
        cash="1000.00",
        positions={"BBAS3": 13, "PETR4": 1000, "WEGE3": 1000},
        opinions=opinions_sell,
    )
    raw_exit = _raw_proposal(
        {
            "BBAS3": ("SELL", "13"),
            "PETR4": ("HOLD", "0"),
            "VALE3": ("HOLD", "0"),
            "ITUB4": ("HOLD", "0"),
            "WEGE3": ("HOLD", "0"),
        }
    )
    compiled_exit = v2.compile_proposal_v2(ctx_exit, raw_exit)
    assert len(compiled_exit["trades"]) == 1
    assert compiled_exit["trades"][0]["ticker"] == "BBAS3"
    assert compiled_exit["trades"][0]["side"] == "SELL"
    assert compiled_exit["trades"][0]["quantity"] == "13"
    print("PASS Gargalo 2 (30% Cap & R$ 2,000 Min BUY): cap clamp, dust BUY->HOLD, combined cap+min clamp, small SELL exit allowed")


def test_gargalo_3_r7_risk_asymmetry():
    bundle = v2.resolve_inputs()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        # Exercise real frozen high-volatility inputs from 2026-10-27 (ITUB4) and 2026-11-05 (PETR4).
        cases = [
            ("2026-10-27", "ITUB4"),
            ("2026-11-05", "PETR4"),
        ]
        for day, ticker in cases:
            ref = bundle["manifest"]["references"][day]
            data = bundle["get_input"](day, ticker, ref)
            assert data["risk_metrics"]["asset_volatility_21"] > 0.50, (day, ticker, data["risk_metrics"])

            def transport_venda(method, url, headers, body):
                prompt = json.loads(body["contents"][0]["parts"][0]["text"])
                assert "allowed_evidence_codes" in prompt, "HARD_ASSET_VOLATILITY_RULE must skip LLM risk call"
                code = prompt["allowed_evidence_codes"][0]
                return v2._fake_wrap(
                    {
                        "signal": "VENDA",
                        "confidence": 0.85,
                        "evidence": [{"code": code, "role": "SUPPORTS_VENDA"}],
                    }
                )

            out_venda, budget_v = _run_committee(tmp_dir, data, transport_venda, f"{day}-{ticker}-venda")
            assert out_venda["risk_source"] == "HARD_ASSET_VOLATILITY_RULE"
            assert out_venda["risk"]["verdict"] == "VETADO"
            assert out_venda["technical_signal"]["signal"] == "VENDA"
            assert out_venda["recommendation"] == "VENDA"
            assert budget_v.summary()["physical_attempts"] == 5

            def transport_compra(method, url, headers, body):
                prompt = json.loads(body["contents"][0]["parts"][0]["text"])
                code = prompt["allowed_evidence_codes"][0]
                return v2._fake_wrap(
                    {
                        "signal": "COMPRA",
                        "confidence": 0.85,
                        "evidence": [{"code": code, "role": "SUPPORTS_COMPRA"}],
                    }
                )

            out_compra, _ = _run_committee(tmp_dir, data, transport_compra, f"{day}-{ticker}-compra")
            assert out_compra["risk"]["verdict"] == "VETADO"
            assert out_compra["technical_signal"]["signal"] == "COMPRA"
            assert out_compra["recommendation"] == "MANTER"

        # Also verify ADVISORY_LLM VETADO preserves VENDA while blocking COMPRA.
        low_vol_data = bundle["get_input"]("2026-04-06", "PETR4", bundle["manifest"]["references"]["2026-04-06"])
        assert low_vol_data["risk_metrics"]["asset_volatility_21"] <= 0.50

        def transport_llm_veto_venda(method, url, headers, body):
            prompt = json.loads(body["contents"][0]["parts"][0]["text"])
            if "allowed_evidence_codes" in prompt:
                return v2._fake_wrap(
                    {
                        "signal": "VENDA",
                        "confidence": 0.8,
                        "evidence": [{"code": prompt["allowed_evidence_codes"][0], "role": "SUPPORTS_VENDA"}],
                    }
                )
            return v2._fake_wrap({"verdict": "VETADO", "analysis": "Risco elevado LLM.", "risk_metrics": {}})

        out_llm_veto, _ = _run_committee(tmp_dir, low_vol_data, transport_llm_veto_venda, "llm-veto-venda")
        assert out_llm_veto["risk_source"] == "ADVISORY_LLM"
        assert out_llm_veto["risk"]["verdict"] == "VETADO"
        assert out_llm_veto["recommendation"] == "VENDA"

    # compile_proposal_v2 on 2026-10-27 ITUB4 (380 shares, VETADO + VENDA) allows SELL and blocks BUY.
    opinions_r7 = {
        "ITUB4": {"recommendation": "VENDA", "risk_verdict": "VETADO", "confidence": 0.8},
        "PETR4": {"recommendation": "VENDA", "risk_verdict": "VETADO", "confidence": 0.8},
        "VALE3": {"recommendation": "MANTER", "risk_verdict": "APROVADO", "confidence": 0.6},
        "WEGE3": {"recommendation": "MANTER", "risk_verdict": "APROVADO", "confidence": 0.6},
        "BBAS3": {"recommendation": "COMPRA", "risk_verdict": "VETADO", "confidence": 0.8},
    }
    ctx_r7 = _make_context(
        cash="30000.00",
        positions={"ITUB4": 380, "PETR4": 1220, "WEGE3": 400},
        opinions=opinions_r7,
        reference_session="2026-10-26",
        target_date="2026-10-27",
    )
    raw_sell_ok = _raw_proposal(
        {
            "ITUB4": ("SELL", "380"),
            "PETR4": ("SELL", "1220"),
            "VALE3": ("HOLD", "0"),
            "WEGE3": ("HOLD", "0"),
            "BBAS3": ("HOLD", "0"),
        }
    )
    compiled_r7 = v2.compile_proposal_v2(ctx_r7, raw_sell_ok)
    assert {(t["ticker"], t["side"], t["quantity"]) for t in compiled_r7["trades"]} == {
        ("ITUB4", "SELL", "380"),
        ("PETR4", "SELL", "1220"),
    }

    raw_buy_blocked = _raw_proposal(
        {
            "ITUB4": ("HOLD", "0"),
            "PETR4": ("HOLD", "0"),
            "VALE3": ("HOLD", "0"),
            "WEGE3": ("HOLD", "0"),
            "BBAS3": ("BUY", "200"),
        }
    )
    _assert_raises_value_error(
        lambda: v2.compile_proposal_v2(ctx_r7, raw_buy_blocked),
        "manager_operation_incompatible_with_opinion",
    )
    print("PASS Gargalo 3 (R7 Risk Asymmetry): HARD_ASSET_VOLATILITY_RULE on 2026-10-27 ITUB4 & 2026-11-05 PETR4 + ADVISORY_LLM VETO allow SELL and block BUY")


def test_gargalo_4_heterogeneous_committee():
    def make_data(features, ticker="WEGE3", day="2026-08-24"):
        return {
            "schema_version": 1,
            "identity": v2.radar.IDENTITY,
            "ticker": ticker,
            "session": day,
            "adjusted_close": 48.0,
            "raw_bar": {"abertura": 48.0, "maxima": 48.5, "minima": 47.5, "fechamento": 48.0, "volume": 1e6},
            "features": features,
            "risk_metrics": {"asset_volatility_21": 0.25},
        }

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        # 1. Capture distinct lens prompts and validate TechnicalEvidenceResponse + allowed_evidence_codes.
        overbought_features = {
            "sma50_gap": 0.08,
            "sma200_gap": 0.14,
            "bb_upper_gap": 0.01,
            "bb_lower_gap": 0.15,
            "bb_width": 0.14,
            "rsi": 73.0,
            "macd_ratio": 0.03,
            "macd_signal_ratio": 0.01,
        }
        seen_prompts = []

        def recording_transport(method, url, headers, body):
            prompt = json.loads(body["contents"][0]["parts"][0]["text"])
            if "allowed_evidence_codes" in prompt:
                seen_prompts.append(body["systemInstruction"]["parts"][0]["text"])
            return v2.fake_gemini_v2(method, url, headers, body)

        out_top, _ = _run_committee(tmp_dir, make_data(overbought_features), recording_transport, "top")
        assert len(seen_prompts) == 5
        assert "[LENTE_TENDENCIA_ESTRUTURAL]" in seen_prompts[0]
        assert "[LENTE_TENDENCIA_ESTRUTURAL]" in seen_prompts[1]
        assert "[LENTE_REVERSAO_BOLLINGER_RSI]" in seen_prompts[2]
        assert "[LENTE_REVERSAO_BOLLINGER_RSI]" in seen_prompts[3]
        assert "[LENTE_REGIME_EQUILIBRIO]" in seen_prompts[4]
        assert len(set(seen_prompts)) == 3

        expected_codes = allowed_evidence_codes(overbought_features)
        assert out_top["allowed_evidence_codes"] == expected_codes
        for vote in out_top["votes"]:
            TechnicalEvidenceResponse.model_validate(vote["signal"])
            assert {e["code"] for e in vote["signal"]["evidence"]} <= set(expected_codes)
        # Stretched top (rsi > 65): must avoid COMPRA!
        assert all(v["signal"]["signal"] != "COMPRA" for v in out_top["votes"])
        assert out_top["technical_signal"]["signal"] != "COMPRA"
        assert out_top["recommendation"] != "COMPRA"

        # 2. Oversold bottom (rsi < 35): mean-reversion avoids panic VENDA, committee diverges (not 5x0 VENDA).
        oversold_features = {
            "sma50_gap": -0.09,
            "sma200_gap": -0.06,
            "bb_upper_gap": -0.15,
            "bb_lower_gap": -0.01,
            "bb_width": 0.14,
            "rsi": 29.0,
            "macd_ratio": -0.03,
            "macd_signal_ratio": -0.01,
        }
        out_bottom, _ = _run_committee(tmp_dir, make_data(oversold_features), v2.fake_gemini_v2, "bottom")
        votes_by_id = {v["analyst_id"]: v["signal"]["signal"] for v in out_bottom["votes"]}
        assert votes_by_id[1] == "VENDA" and votes_by_id[2] == "VENDA"
        assert votes_by_id[3] != "VENDA" and votes_by_id[4] != "VENDA"
        assert out_bottom["technical_signal"]["signal"] != "VENDA"
        assert out_bottom["recommendation"] != "VENDA"

        # 3. Healthy non-stretched uptrend reaches COMPRA consensus.
        healthy_up = {
            "sma50_gap": 0.04,
            "sma200_gap": 0.06,
            "bb_upper_gap": -0.05,
            "bb_lower_gap": 0.08,
            "bb_width": 0.12,
            "rsi": 56.0,
            "macd_ratio": 0.02,
            "macd_signal_ratio": 0.01,
        }
        out_up, _ = _run_committee(tmp_dir, make_data(healthy_up), v2.fake_gemini_v2, "healthy-up")
        assert out_up["consensus"]["consensus_reached"] is True
        assert out_up["technical_signal"]["signal"] == "COMPRA"
        assert out_up["recommendation"] == "COMPRA"

        # 4. Invalid evidence code must fail committee validation.
        def bad_evidence_transport(method, url, headers, body):
            prompt = json.loads(body["contents"][0]["parts"][0]["text"])
            if "allowed_evidence_codes" not in prompt:
                return v2.fake_gemini_v2(method, url, headers, body)
            forbidden = next(
                c
                for c in ("CLOSE_ABOVE_SMA50", "CLOSE_BELOW_SMA50", "CLOSE_AT_SMA50")
                if c not in prompt["allowed_evidence_codes"]
            )
            return v2._fake_wrap(
                {
                    "signal": "MANTER",
                    "confidence": 0.5,
                    "evidence": [{"code": forbidden, "role": "NEUTRAL"}],
                }
            )

        _assert_raises_value_error(
            lambda: _run_committee(tmp_dir, make_data(healthy_up), bad_evidence_transport, "bad-evidence"),
            "incomplete_or_invalid_committee",
        )
    print("PASS Gargalo 4 (Heterogeneous Committee): 3 distinct lens prompts, schema/evidence validation, no top-buy / bottom-sell")


def test_preflight_and_offline_e2e():
    # 1. Verify preflight() under no_network() and via CLI --preflight.
    with no_network():
        pf = v2.preflight()
    assert pf["identity"] == "HFL-CONTINUOUS-EXPLORATORY-REPLAY-V2"
    assert pf["sessions_count"] == 153
    assert pf["logical_calls_max"] == 153 * 31
    assert pf["hard_volatility_vetoes_skipped"] == 40
    assert pf["logical_calls_estimate"] == 4703
    assert pf["no_network_calls_made"] is True

    cli_pf = subprocess.run(
        [sys.executable, str(PROJECT / "scripts/continuous_replay_v2.py"), "--preflight"],
        cwd=str(PROJECT),
        capture_output=True,
        text=True,
        check=True,
    )
    cli_pf_json = json.loads(cli_pf.stdout)
    assert cli_pf_json["logical_calls_estimate"] == 4703

    # 2. Multi-session offline execution in a temporary directory under no_network().
    old_manual_root = v2.manual.ROOT
    old_market_root = v2.market.ROOT
    old_session_rows = v2.orders.session_rows
    try:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v2-offline"
            with no_network():
                res = v2.execute(root, offline=True, count=5)
            assert res["identity"] == "HFL-CONTINUOUS-EXPLORATORY-REPLAY-V2"
            assert res["sessions_completed"] == 5
            assert res["complete_analysis_days"] == 5
            assert res["gaps"] == []
            assert res["budget"]["unknown_attempts"] == 0
            assert Decimal(res["budget"]["exposure_usd"]) <= Decimal("34.78")
            assert (root / "summary.json").exists()
            assert (root / "daily.csv").exists()
            assert (root / "references_complete.json").exists()

            # Check every strategy reconciles and MULTIAGENT proposals respect V2 cap & min trade.
            with closing(v2.manual.connect()) as conn:
                wallets = v2.manual.catalog(conn)
                assert {w["strategy"] for w in wallets} == set(v2.STRATEGIES)
                for w in wallets:
                    v2.manual.replay(v2.manual.events(conn, w["id"]))

            for day_path in sorted((root / "sessions").glob("*/day.json")):
                day_data = v2.checked(day_path)
                assert day_data["status"] == "COMPLETED"
                prop = v2.checked(day_path.parent / "manager/proposal.json")
                eq_before = Decimal(prop["equity_before"])
                for tr in prop["trades"]:
                    if tr["side"] == "BUY":
                        gross = Decimal(tr["quantity"]) * Decimal(tr["price"])
                        assert gross >= v2.MIN_TRADE_BRL, (day_data["day"], tr)
                for row in prop["rows"]:
                    if row["side"] == "BUY":
                        assert Decimal(row["value_after"]) / eq_before <= v2.MAX_ASSET_WEIGHT

            # Idempotent resume must perform zero extra physical calls.
            attempts_before = res["budget"]["physical_attempts"]
            with no_network():
                res2 = v2.execute(root, offline=True, count=5)
            assert res2["budget"]["physical_attempts"] == attempts_before

            # Export v2 artifacts and verify audit_replay_v2_comparison on the offline export.
            mirror_dir = Path(tmp) / "mirror-exports"
            with no_network():
                exp_summary = export_v2.export(root, mirror=mirror_dir)
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
            comp = audit_v2.run_comparison(
                v2_dir=root / "exports",
                out_dir=comp_out,
                allow_partial=True,
            )
            assert comp["status"] == "PASS"
            assert all(comp["reference_parity_v1_v2"].values())
            assert comp["v2"]["daily_states_reconciled"] == 30
            assert len(comp["v2"]["concentration"]["dust_buys_below_2000"]) == 0
            assert (comp_out / "comparacao_v1_v2.json").exists()
            assert (comp_out / "comparacao_carteiras.csv").exists()
            assert (comp_out / "atribuicao_v1_vs_v2.csv").exists()

        # 3. Also verify CLI `--offline <dir> --count 3` end-to-end.
        with tempfile.TemporaryDirectory() as cli_tmp:
            cli_root = Path(cli_tmp) / "cli-offline"
            cli_run = subprocess.run(
                [
                    sys.executable,
                    str(PROJECT / "scripts/continuous_replay_v2.py"),
                    "--offline",
                    str(cli_root),
                    "--count",
                    "3",
                ],
                cwd=str(PROJECT),
                capture_output=True,
                text=True,
                check=True,
            )
            cli_summary = v2.checked(cli_root / "summary.json")
            assert cli_summary["sessions_completed"] == 3
            assert cli_summary["complete_analysis_days"] == 3
            assert cli_summary["identity"] == "HFL-CONTINUOUS-EXPLORATORY-REPLAY-V2"
    finally:
        v2.manual.ROOT = old_manual_root
        v2.market.ROOT = old_market_root
        v2.orders.session_rows = old_session_rows
    print("PASS preflight & offline E2E: --preflight (153 sessions, 4703 calls), 5-session & CLI 3-session offline runs, reconciliation, idempotent resume")


def test_compile_v2_non_strict_clamping():
    opinions = {
        "PETR4": {"recommendation": "MANTER", "risk_verdict": "APROVADO", "confidence": 0.7},
        "VALE3": {"recommendation": "COMPRA", "risk_verdict": "APROVADO", "confidence": 0.8},
        "ITUB4": {"recommendation": "MANTER", "risk_verdict": "APROVADO", "confidence": 0.6},
        "WEGE3": {"recommendation": "MANTER", "risk_verdict": "APROVADO", "confidence": 0.6},
        "BBAS3": {"recommendation": "COMPRA", "risk_verdict": "VETADO", "confidence": 0.7},
    }
    # 1. Trim violating weight_before <= 25% + over-cash BUY + VETADO BUY all clamp cleanly in strict=False.
    ctx = _make_context(
        cash="10000.00",
        positions={"PETR4": 1000, "WEGE3": 500, "ITUB4": 432},  # 45k, 25k (<25% of 100,044.80), ~20k, 10k cash
        prices={"PETR4": "45.00", "WEGE3": "50.00", "ITUB4": "46.40", "VALE3": "80.00", "BBAS3": "22.60"},
        opinions=opinions,
    )
    raw = _raw_proposal(
        {
            "PETR4": ("SELL", "900"),  # reduces 45k -> 4.5k (<15%) -> clamped to keep >= 15% (TRIM_WEIGHT_AFTER_FLOOR)
            "WEGE3": ("SELL", "100"),  # weight_before <= 25% -> clamped to HOLD (TRIM_WEIGHT_BEFORE_TOO_LOW)
            "VALE3": ("BUY", "375"),   # 375*80 = 30k; after PETR4 trim + 10k cash, cash clamp if needed
            "BBAS3": ("BUY", "100"),   # VETADO -> clamped to HOLD (OPINION_INCOMPATIBLE_WITH_BUY)
            "ITUB4": ("HOLD", "0"),
        }
    )
    compiled = v2.compile_proposal_v2(ctx, raw, strict=False)
    assert Decimal(compiled["cash_after"]) >= 0
    reasons = {a["reason"] for a in compiled["adjustments"]}
    assert "TRIM_WEIGHT_BEFORE_TOO_LOW" in reasons
    assert "TRIM_WEIGHT_AFTER_FLOOR" in reasons
    assert "OPINION_INCOMPATIBLE_WITH_BUY" in reasons
    row_petr = next(r for r in compiled["rows"] if r["ticker"] == "PETR4")
    assert Decimal(row_petr["value_after"]) / Decimal(compiled["equity_before"]) >= Decimal("0.15")

    # 2. Cash-only BUY overflow clamps down to available cash and respects MIN_TRADE_BRL.
    ctx_cash = _make_context(
        cash="5000.00",
        positions={"PETR4": 1000, "WEGE3": 1000},
        opinions=opinions,
    )
    raw_overcash = _raw_proposal(
        {
            "VALE3": ("BUY", "200"),  # R$ 16,000 > R$ 5,000 cash -> clamped to <= 62 shares (~R$ 4,960)
            "PETR4": ("HOLD", "0"),
            "ITUB4": ("HOLD", "0"),
            "WEGE3": ("HOLD", "0"),
            "BBAS3": ("HOLD", "0"),
        }
    )
    compiled_oc = v2.compile_proposal_v2(ctx_cash, raw_overcash, strict=False)
    assert Decimal(compiled_oc["cash_after"]) >= 0
    assert any(a["reason"] == "INSUFFICIENT_CASH" for a in compiled_oc["adjustments"])
    assert len(compiled_oc["trades"]) == 1 and int(compiled_oc["trades"][0]["quantity"]) == 62
    print("PASS non-strict live clamping: TRIM_WEIGHT_BEFORE_TOO_LOW, TRIM_WEIGHT_AFTER_FLOOR, OPINION_INCOMPATIBLE_WITH_BUY, INSUFFICIENT_CASH")


if __name__ == "__main__":
    test_preservation()
    test_gargalo_1_trim_to_fund()
    test_gargalo_2_cap_and_min_trade()
    test_gargalo_3_r7_risk_asymmetry()
    test_gargalo_4_heterogeneous_committee()
    test_compile_v2_non_strict_clamping()
    test_preflight_and_offline_e2e()
    print("ALL CHECKS PASSED: continuous_replay_v2 verified")
