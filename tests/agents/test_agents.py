import asyncio

import pytest
from pydantic import ValidationError

from src.agents.graph import build_graph
from src.agents.llm_client import CachedLLMClient, MockLLMClient, RetryingLLMClient
from src.agents.portfolio_manager import (
    PortfolioConfig,
    calculate_kelly_size,
    create_portfolio_manager_node,
)
from src.agents.risk_manager import RiskConfig, RiskManager
from src.agents.state import FinalDecision, RiskVerdict, TechnicalSignal
from src.agents.technical_analyst import (
    AnalystEnsembleConfig,
    build_prompt,
    create_technical_analyst_ensemble_node,
    create_technical_analyst_node,
    parse_indicators_from_state,
)


def state(**overrides):
    base = {
        "ticker": "WEGE3.SA",
        "date": "2025-01-02",
        "indicators": {"sma_50": 50.0, "sma_200": 45.0, "extra": 999.0},
        "cash": 100_000.0,
        "position": 0.0,
        "current_price": 55.0,
        "equity": 100_000.0,
        "recent_volatility": 0.20,
        "current_drawdown": 0.05,
        "payoff_ratio": 1.0,
        "errors": [],
    }
    base.update(overrides)
    return base


def run(awaitable):
    return asyncio.run(awaitable)


class RawClient:
    def __init__(self, response):
        self.response = response

    async def generate(self, *_args, **_kwargs):
        return self.response


class FlakyClient(RawClient):
    def __init__(self, response, failures):
        super().__init__(response)
        self.failures = failures
        self.calls = 0

    async def generate(self, *_args, **_kwargs):
        self.calls += 1
        if self.calls <= self.failures:
            raise TimeoutError("temporário")
        return self.response


def test_output_models_validate_literals_ranges_and_extra_fields():
    with pytest.raises(ValidationError):
        TechnicalSignal(signal="ACHO", justification="x", confidence=0.5)
    with pytest.raises(ValidationError):
        TechnicalSignal(signal="COMPRA", justification="x", confidence=1.1)
    with pytest.raises(ValidationError):
        FinalDecision(decision="COMPRA", position_size=-0.1, reasoning="x")
    with pytest.raises(ValidationError):
        RiskVerdict(verdict="APROVADO", analysis="x", risk_metrics={}, extra="não")


def test_mock_client_validates_structured_response_and_records_call():
    llm = MockLLMClient(
        {
            TechnicalSignal: {
                "signal": "COMPRA",
                "justification": "SMA curta acima da longa",
                "confidence": 0.7,
            }
        }
    )
    response = run(llm.generate("system", "user", TechnicalSignal))
    assert isinstance(response, TechnicalSignal)
    assert response.signal == "COMPRA"
    assert len(llm.calls) == 1

    assert run(llm.generate("system", "user")) == "MANTER"
    assert run(MockLLMClient({None: []}).generate("system", "user")) == "MANTER"


def test_retry_client_recovers_and_propagates_final_failure():
    signal = TechnicalSignal(signal="COMPRA", justification="x", confidence=0.7)
    flaky = FlakyClient(signal, failures=2)
    result = run(
        RetryingLLMClient(flaky, max_attempts=3, base_delay=0).generate(
            "system", "user", TechnicalSignal
        )
    )
    assert result == signal
    assert flaky.calls == 3

    with pytest.raises(TimeoutError):
        run(
            RetryingLLMClient(FlakyClient(signal, 3), 2, 0).generate(
                "system", "user", TechnicalSignal
            )
        )
    with pytest.raises(ValueError):
        RetryingLLMClient(flaky, max_attempts=0)


def test_cache_client_persists_structured_response(tmp_path):
    signal = TechnicalSignal(signal="COMPRA", justification="x", confidence=0.7)
    source = FlakyClient(signal, failures=0)
    path = tmp_path / "llm-cache.json"
    cached = CachedLLMClient(source, path)

    first = run(cached.generate("system", "user", TechnicalSignal))
    second = run(cached.generate("system", "user", TechnicalSignal))
    from_disk = run(
        CachedLLMClient(RawClient("não chamar"), path).generate(
            "system", "user", TechnicalSignal
        )
    )

    assert first == second == from_disk == signal
    assert source.calls == 1
    assert path.is_file()


def test_technical_prompt_filters_extra_data_and_has_guardrails():
    parsed = parse_indicators_from_state(state())
    prompt = build_prompt(state())
    assert parsed == {"sma_50": 50.0, "sma_200": 45.0}
    assert "999" not in prompt
    assert "COMPRA, VENDA ou MANTER" in prompt
    assert "informação externa" in prompt


def test_technical_node_falls_back_when_data_or_response_is_invalid():
    node = create_technical_analyst_node(MockLLMClient())
    result = run(node(state(indicators={})))
    assert result["technical_signal"].signal == "MANTER"
    assert result["errors"]

    invalid = create_technical_analyst_node(MockLLMClient({TechnicalSignal: "not-json"}))
    result = run(invalid(state()))
    assert result["technical_signal"].signal == "MANTER"
    assert "resposta inválida" in result["errors"][0]

    result = run(create_technical_analyst_node(RawClient("COMPRA"))(state()))
    assert result["technical_signal"].signal == "MANTER"


def test_single_technical_node_accepts_valid_response():
    signal = TechnicalSignal(signal="COMPRA", justification="tendência", confidence=0.7)
    result = run(create_technical_analyst_node(RawClient(signal))(state()))
    assert result["technical_signal"] == signal
    assert not result["errors"]


def test_technical_node_rejects_invalid_price():
    result = run(create_technical_analyst_node(MockLLMClient())(state(current_price=0)))
    assert result["technical_signal"].signal == "MANTER"
    assert "preço atual" in result["errors"][0]


def vote(signal, confidence=0.8):
    return {
        "signal": signal,
        "justification": f"voto {signal}",
        "confidence": confidence,
    }


def test_ensemble_requires_twenty_five_of_thirty_votes_by_default():
    responses = [vote("COMPRA")] * 25 + [vote("VENDA")] * 5
    llm = MockLLMClient({TechnicalSignal: responses})
    result = run(create_technical_analyst_ensemble_node(llm)(state()))
    assert result["technical_consensus"].consensus_reached
    assert result["technical_consensus"].counts == {
        "COMPRA": 25,
        "VENDA": 5,
        "MANTER": 0,
    }
    assert result["technical_signal"].signal == "COMPRA"
    assert result["technical_signal"].confidence == pytest.approx(0.8 * 25 / 30)
    assert len(llm.calls) == 30
    assert [v.analyst_id for v in result["technical_votes"]] == list(range(1, 31))
    assert result["technical_votes"][0].temperature == pytest.approx(0.2)
    assert result["technical_votes"][-1].temperature == pytest.approx(0.8)
    assert result["technical_votes"][0].seed == 10_001
    assert llm.calls[0].options["analyst_id"] == 1


def test_ensemble_holds_without_supermajority():
    responses = [vote("COMPRA")] * 24 + [vote("VENDA")] * 6
    result = run(
        create_technical_analyst_ensemble_node(
            MockLLMClient({TechnicalSignal: responses})
        )(state())
    )
    assert not result["technical_consensus"].consensus_reached
    assert result["technical_signal"].signal == "MANTER"


def test_ensemble_can_require_unanimity_and_all_valid_votes():
    config = AnalystEnsembleConfig(consensus_threshold=1.0)
    split = [vote("COMPRA")] * 29 + [vote("MANTER")]
    result = run(
        create_technical_analyst_ensemble_node(
            MockLLMClient({TechnicalSignal: split}), config
        )(state())
    )
    assert result["technical_signal"].signal == "MANTER"

    invalid = [vote("COMPRA")] * 29 + ["not-json"]
    result = run(
        create_technical_analyst_ensemble_node(MockLLMClient({TechnicalSignal: invalid}))(
            state()
        )
    )
    assert result["technical_signal"].signal == "MANTER"


def test_ensemble_rejects_inverted_temperature_range():
    with pytest.raises(ValidationError):
        AnalystEnsembleConfig(temperature_min=1.0, temperature_max=0.5)


def test_ensemble_holds_on_unstructured_response():
    result = run(
        create_technical_analyst_ensemble_node(
            RawClient("COMPRA"),
            AnalystEnsembleConfig(analyst_count=2),
        )(state())
    )
    assert result["technical_signal"].signal == "MANTER"
    assert result["errors"]


def test_ensemble_rejects_missing_market_data_before_calls():
    llm = MockLLMClient()
    result = run(create_technical_analyst_ensemble_node(llm)(state(indicators={})))
    assert result["technical_signal"].signal == "MANTER"
    assert not llm.calls


def test_risk_hard_rule_vetoes_before_llm():
    llm = MockLLMClient(
        {RiskVerdict: {"verdict": "APROVADO", "analysis": "ok", "risk_metrics": {}}}
    )
    manager = RiskManager(llm, RiskConfig(max_volatility=0.30))
    result = run(
        manager.evaluate(
            state(
                recent_volatility=0.31,
                technical_signal=TechnicalSignal(
                    signal="COMPRA", justification="tendência", confidence=0.7
                ),
            )
        )
    )
    assert result["risk_verdict"].verdict == "VETADO"
    assert not llm.calls


def test_risk_does_not_block_an_exit_without_metrics():
    manager = RiskManager(MockLLMClient())
    result = run(
        manager.evaluate(
            state(
                recent_volatility=None,
                current_drawdown=None,
                equity=None,
                technical_signal=TechnicalSignal(
                    signal="VENDA", justification="reversão", confidence=0.8
                ),
            )
        )
    )
    assert result["risk_verdict"].verdict == "APROVADO"


@pytest.mark.parametrize(
    ("overrides", "analysis"),
    [
        ({"technical_signal": None}, "sinal técnico ausente"),
        ({"equity": None}, "métricas ausentes"),
        ({"current_drawdown": 0.30}, "Drawdown acima"),
        ({"position": 600.0}, "Concentração no limite"),
    ],
)
def test_risk_safe_failures(overrides, analysis):
    buy = TechnicalSignal(signal="COMPRA", justification="tendência", confidence=0.7)
    inputs = {"technical_signal": buy}
    inputs.update(overrides)
    result = run(RiskManager(MockLLMClient()).evaluate(state(**inputs)))
    assert result["risk_verdict"].verdict == "VETADO"
    assert analysis in result["risk_verdict"].analysis


def test_risk_invalid_llm_response_is_vetoed():
    buy = TechnicalSignal(signal="COMPRA", justification="tendência", confidence=0.7)
    result = run(RiskManager(RawClient("APROVADO")).evaluate(state(technical_signal=buy)))
    assert result["risk_verdict"].verdict == "VETADO"
    assert result["errors"]


@pytest.mark.parametrize(
    ("probability", "expected"),
    [(0.6, 0.1), (0.5, 0.0), (0.4, 0.0)],
)
def test_fractional_kelly(probability, expected):
    assert calculate_kelly_size(probability) == pytest.approx(expected)


@pytest.mark.parametrize(
    "args",
    [(-0.1, 1.0, 0.5), (0.6, 0.0, 0.5), (0.6, 1.0, 0.0)],
)
def test_fractional_kelly_rejects_invalid_parameters(args):
    with pytest.raises(ValueError):
        calculate_kelly_size(*args)


def test_portfolio_caps_purchase_by_kelly_and_concentration():
    llm = MockLLMClient(
        {
            FinalDecision: {
                "decision": "COMPRA",
                "position_size": 0.8,
                "reasoning": "sinal aprovado",
            }
        }
    )
    node = create_portfolio_manager_node(
        llm,
        PortfolioConfig(kelly_fraction=0.5, max_position_size=0.5, max_concentration=0.3),
    )
    result = run(
        node(
            state(
                technical_signal=TechnicalSignal(
                    signal="COMPRA", justification="tendência", confidence=0.6
                ),
                risk_verdict=RiskVerdict(
                    verdict="APROVADO", analysis="risco normal", risk_metrics={}
                ),
            )
        )
    )
    assert result["final_decision"].position_size == pytest.approx(0.1)


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"technical_signal": None}, "parecer anterior"),
        ({"risk_verdict": RiskVerdict(verdict="VETADO", analysis="x")}, "vetada"),
        (
            {
                "technical_signal": TechnicalSignal(
                    signal="MANTER", justification="x", confidence=0.5
                )
            },
            "manter",
        ),
        ({"current_price": 0.0}, "preço atual"),
        ({"cash": 0.0}, "Caixa insuficiente"),
        (
            {
                "technical_signal": TechnicalSignal(
                    signal="COMPRA", justification="x", confidence=0.4
                )
            },
            "Kelly",
        ),
    ],
)
def test_portfolio_guardrails(overrides, reason):
    base = {
        "technical_signal": TechnicalSignal(
            signal="COMPRA", justification="x", confidence=0.7
        ),
        "risk_verdict": RiskVerdict(verdict="APROVADO", analysis="x"),
    }
    base.update(overrides)
    result = run(create_portfolio_manager_node(MockLLMClient())(state(**base)))
    assert result["final_decision"].decision == "MANTER"
    assert reason in result["final_decision"].reasoning


@pytest.mark.parametrize(
    ("response", "has_error"),
    [
        (FinalDecision(decision="VENDA", position_size=0.5, reasoning="oposto"), True),
        (FinalDecision(decision="MANTER", position_size=0.5, reasoning="cautela"), False),
        ("COMPRA", True),
    ],
)
def test_portfolio_validates_llm_decision(response, has_error):
    node = create_portfolio_manager_node(RawClient(response))
    result = run(
        node(
            state(
                technical_signal=TechnicalSignal(
                    signal="COMPRA", justification="x", confidence=0.7
                ),
                risk_verdict=RiskVerdict(verdict="APROVADO", analysis="x"),
            )
        )
    )
    assert result["final_decision"].decision == "MANTER"
    assert bool(result["errors"]) is has_error


def test_portfolio_can_size_a_sale():
    decision = FinalDecision(decision="VENDA", position_size=0.4, reasoning="reduzir")
    result = run(
        create_portfolio_manager_node(RawClient(decision))(
            state(
                position=100,
                technical_signal=TechnicalSignal(
                    signal="VENDA", justification="x", confidence=0.7
                ),
                risk_verdict=RiskVerdict(verdict="APROVADO", analysis="x"),
            )
        )
    )
    assert result["final_decision"].position_size == 0.4


def test_graph_approved_path_reaches_portfolio_manager():
    llm = MockLLMClient(
        {
            TechnicalSignal: {
                "signal": "COMPRA",
                "justification": "tendência",
                "confidence": 0.7,
            },
            RiskVerdict: {
                "verdict": "APROVADO",
                "analysis": "risco aceitável",
                "risk_metrics": {},
            },
            FinalDecision: {
                "decision": "COMPRA",
                "position_size": 0.8,
                "reasoning": "consenso",
            },
        }
    )
    result = run(build_graph(llm).ainvoke(state()))
    assert result["technical_signal"].signal == "COMPRA"
    assert result["risk_verdict"].verdict == "APROVADO"
    assert result["final_decision"].decision == "COMPRA"
    assert result["final_decision"].position_size == pytest.approx(0.2)
    assert len(llm.calls) == 32


def test_graph_veto_path_ends_before_portfolio_manager():
    llm = MockLLMClient(
        {
            TechnicalSignal: {
                "signal": "COMPRA",
                "justification": "tendência",
                "confidence": 0.7,
            }
        }
    )
    result = run(build_graph(llm).ainvoke(state(recent_volatility=0.8)))
    assert result["risk_verdict"].verdict == "VETADO"
    assert "final_decision" not in result
    assert len(llm.calls) == 30
