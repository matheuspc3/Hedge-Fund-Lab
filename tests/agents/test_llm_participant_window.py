"""O participante LLM sob janela avaliada: warm-up, âncora e estado.

O que estas provas protegem é uma regressão fácil de cometer e difícil de ver:
com warm-up, qualquer heurística baseada em ``len(history)`` deixa de detectar
"primeira decisão", e o pico de patrimônio ou a grade de ``decision_frequency``
passam a depender de onde o snapshot começa em vez de onde a janela começa.
"""

from typing import Any, cast

import pandas as pd
import pytest

from src.agents.llm_client import LLMClient, MockLLMClient
from src.agents.participant import LLMDecisionError, LLMParticipant
from src.agents.state import PortfolioAction, RiskVerdict, TechnicalSignal
from src.backtesting.arena import ExecutionEngine, MarketObservation, OrderIntent

TICKER = "PETR4"
CAPITAL = 10_000.0
TARGET = 0.5

APPROVED = {"verdict": "APROVADO", "analysis": "mock", "risk_metrics": {}}


def signal(kind: str) -> dict[str, Any]:
    return {"signal": kind, "justification": "mock", "confidence": 1.0}


def action(kind: str) -> dict[str, Any]:
    return {"decision": kind, "reasoning": "mock"}


#: Preço em função da **data**, não da posição no recorte: dois quadros que
#: começam em datas diferentes concordam barra a barra onde se sobrepõem.
PRICE_EPOCH = pd.Timestamp("2022-06-01")


def frame(sessions: int, *, start: str = "2023-01-02") -> pd.DataFrame:
    index = pd.DatetimeIndex(pd.bdate_range(start, periods=sessions))
    closes = [10.0 + ((stamp - PRICE_EPOCH).days % 4) * 0.5 for stamp in index]
    return pd.DataFrame({"abertura": closes, "fechamento": closes}, index=index)


def at(data: pd.DataFrame, position: int) -> pd.Timestamp:
    """Sessão numa posição do recorte, já tipada como ``Timestamp``."""
    return cast(pd.Timestamp, data.index[position])


def day(data: pd.DataFrame, position: int) -> str:
    """Data ISO da sessão numa posição do recorte."""
    return at(data, position).date().isoformat()


def client_always(kind: str) -> MockLLMClient:
    return MockLLMClient(
        {
            TechnicalSignal: signal(kind),
            RiskVerdict: APPROVED,
            PortfolioAction: action(kind),
        }
    )


def participant(client: LLMClient, **overrides: Any) -> LLMParticipant:
    params: dict[str, Any] = {
        "analyst_count": 1,
        "consensus_threshold": 1.0,
        "risk_max_volatility": 100.0,
        "risk_max_drawdown": 1.0,
        "risk_max_concentration": 1.0,
        "long_target_weight": TARGET,
        "llm_client": client,
    }
    params.update(overrides)
    return LLMParticipant(TICKER, **params)


def run(
    data: pd.DataFrame,
    agent: LLMParticipant,
    *,
    decision_start: object = None,
    decision_end: object = None,
):
    return ExecutionEngine(
        agent,
        {TICKER: data},
        CAPITAL,
        decision_start=decision_start,
        decision_end=decision_end,
    ).run()


# ── Warm-up não custa chamada ────────────────────────────────────


def test_warmup_nao_chama_o_provedor() -> None:
    """Sessões de contexto não podem gastar uma única chamada paga."""
    data = frame(20)
    client = client_always("COMPRA")
    agent = participant(client)
    run(
        data,
        agent,
        decision_start=day(data, 15),
        decision_end=day(data, 16),
    )

    assert [record.session for record in agent.decisions] == [
        at(data, 15),
        at(data, 16),
    ]
    # Toda chamada emitida pertence a uma sessão avaliada: nenhuma no warm-up.
    assert client.calls, "o cenário precisa emitir chamadas para o teste valer"
    assert {record.request.decision_session for record in agent.llm_calls} <= {
        day(data, 15),
        day(data, 16),
    }


def test_warmup_nao_produz_registro_de_decisao() -> None:
    data = frame(20)
    agent = participant(client_always("MANTER"))
    run(
        data,
        agent,
        decision_start=day(data, 15),
        decision_end=day(data, 16),
    )

    assert all(
        record.session >= at(data, 15) for record in agent.decisions
    )
    assert len(agent.decisions) == 2


def test_warmup_nao_produz_trace() -> None:
    data = frame(20)
    agent = participant(client_always("COMPRA"))
    run(
        data,
        agent,
        decision_start=day(data, 15),
        decision_end=day(data, 16),
    )

    assert {record.request.decision_session for record in agent.llm_calls} == {
        day(data, 15),
        day(data, 16),
    }


# ── Histórico expansivo ──────────────────────────────────────────


def test_primeira_decisao_recebe_o_warmup_inteiro() -> None:
    """Expanding: o LLM decide em ``t`` com todo o histórico causal até ``t``."""
    data = frame(20)
    agent = participant(client_always("MANTER"))
    observed: list[int] = []
    original = agent._agent_state

    def spy(observation, history, equity, close):
        observed.append(len(history))
        return original(observation, history, equity, close)

    agent._agent_state = spy  # type: ignore[method-assign]
    run(
        data,
        agent,
        decision_start=day(data, 15),
        decision_end=day(data, 16),
    )

    assert observed == [16, 17]


# ── decision_frequency ancorado na janela ────────────────────────


def test_grade_de_decisao_nao_depende_do_tamanho_do_warmup() -> None:
    """Mesma janela + warm-ups diferentes = mesmas sessões elegíveis.

    Sem a âncora na janela, o contador de ``decision_frequency`` começaria em
    ``data_start`` e a grade se deslocaria conforme o snapshot crescesse para
    trás — mudando quais decisões existem sem que nada científico mudasse.
    """
    window = {"decision_start": "2023-02-01", "decision_end": "2023-02-15"}
    grades: list[list[pd.Timestamp]] = []
    for start in ("2023-01-02", "2022-11-01"):
        data = frame(90, start=start)
        agent = participant(client_always("MANTER"), decision_frequency=3)
        run(data, agent, **window)
        grades.append([record.session for record in agent.decisions])

    assert grades[0] == grades[1]
    assert grades[0][0] == pd.Timestamp("2023-02-01")


def test_primeira_sessao_da_janela_e_sempre_elegivel() -> None:
    data = frame(60)
    agent = participant(client_always("MANTER"), decision_frequency=5)
    run(data, agent, decision_start="2023-02-01", decision_end="2023-02-28")

    assert agent.decisions[0].session == pd.Timestamp("2023-02-01")


# ── Estado de portfólio ancorado na janela ───────────────────────


def test_pico_de_patrimonio_comeca_na_janela() -> None:
    """``current_drawdown`` da primeira decisão é zero: o pico nasce ali."""
    data = frame(30)
    agent = participant(client_always("MANTER"))
    states: list[dict[str, Any]] = []
    original = agent._agent_state

    def spy(observation, history, equity, close):
        state = original(observation, history, equity, close)
        states.append(dict(state))
        return state

    agent._agent_state = spy  # type: ignore[method-assign]
    run(data, agent, decision_start="2023-02-01", decision_end="2023-02-08")

    assert agent._peak_equity == pytest.approx(CAPITAL)
    assert states[0]["current_drawdown"] == pytest.approx(0.0)
    assert states[0]["equity"] == pytest.approx(CAPITAL)


def test_instancia_nao_pode_ser_reutilizada_entre_execucoes() -> None:
    """Sem ``len(history) == 1``, o relógio de sessões detecta a reutilização."""
    data = frame(20)
    agent = participant(client_always("MANTER"))
    run(data, agent, decision_start="2023-01-20", decision_end="2023-01-24")

    with pytest.raises(LLMDecisionError, match="does not advance past"):
        run(data, agent, decision_start="2023-01-20", decision_end="2023-01-24")


# ── Calibration Anchor ───────────────────────────────────────────


def test_ancora_unica_decide_uma_vez_e_executa_no_pregao_seguinte() -> None:
    data = frame(30)
    agent = participant(client_always("COMPRA"))
    anchor = day(data, 20)
    result = run(data, agent, decision_start=anchor, decision_end=anchor)

    assert [record.session for record in agent.decisions] == [at(data, 20)]
    assert [pd.Timestamp(trade.date) for trade in result.trades] == [at(data, 21)]
    assert list(result.equity_curve.index) == [at(data, 20), at(data, 21)]


def test_settlement_nao_consulta_o_provedor() -> None:
    data = frame(30)
    client = client_always("COMPRA")
    agent = participant(client)
    anchor = day(data, 20)
    run(data, agent, decision_start=anchor, decision_end=anchor)

    assert len(agent.decisions) == 1
    # Todas as chamadas pertencem à âncora; o settlement não consulta ninguém.
    assert {record.request.decision_session for record in agent.llm_calls} == {
        anchor
    }


# ── Causalidade ──────────────────────────────────────────────────


def test_observacao_nao_revela_a_janela_nem_a_fase() -> None:
    """O participante não pode saber que esta é a última decisão avaliada."""
    from dataclasses import fields

    data = frame(30)
    agent = participant(client_always("MANTER"))
    seen: list[MarketObservation] = []
    original = agent.decide

    def spy(observation: MarketObservation) -> list[OrderIntent]:
        seen.append(observation)
        return original(observation)

    engine = ExecutionEngine(
        cast(Any, type("Spy", (), {"decide": staticmethod(spy)})()),
        {TICKER: data},
        CAPITAL,
        decision_start="2023-02-01",
        decision_end="2023-02-08",
    )
    engine.run()

    names = {field.name for field in fields(MarketObservation)}
    assert names == {"session", "history", "positions", "cash", "equity"}
    for observation in seen:
        assert max(observation.history[TICKER].index) == observation.session


def test_historico_nunca_ultrapassa_a_sessao_decidida() -> None:
    data = frame(30)
    agent = participant(client_always("MANTER"))
    run(data, agent, decision_start="2023-02-01", decision_end="2023-02-08")

    for record in agent.decisions:
        assert record.session <= pd.Timestamp("2023-02-08")


# ── Ausência legítima de intent na âncora ────────────────────────


def test_ancora_com_manter_nao_produz_trade_e_o_run_segue_valido() -> None:
    """Decidir ``MANTER`` é decidir: uma decisão, nenhum intent, run válido.

    Há sessão seguinte e ela é processada; a ausência de pendente não pode
    virar erro de settlement.
    """
    data = frame(30)
    client = client_always("MANTER")
    agent = participant(client)
    anchor = day(data, 20)
    result = run(data, agent, decision_start=anchor, decision_end=anchor)

    assert [record.session for record in agent.decisions] == [at(data, 20)]
    assert agent.decisions[0].target_weight is None
    assert result.trades == []
    assert list(result.equity_curve.index) == [at(data, 20), at(data, 21)]
    assert result.final_equity == pytest.approx(CAPITAL)


def test_ancora_vetada_pelo_risco_nao_produz_trade_e_o_run_segue_valido() -> None:
    """Veto de risco também é ausência legítima de intent, não falha."""
    data = frame(30)
    # Limite de volatilidade impossível: qualquer oscilação já veta.
    agent = participant(client_always("COMPRA"), risk_max_volatility=0.0)
    anchor = day(data, 20)
    result = run(data, agent, decision_start=anchor, decision_end=anchor)

    record = agent.decisions[0]
    assert record.risk_verdict is not None and record.risk_verdict.verdict == "VETADO"
    assert record.target_weight is None
    assert result.trades == []
    assert list(result.equity_curve.index) == [at(data, 20), at(data, 21)]
    assert result.final_equity == pytest.approx(CAPITAL)


def test_grade_de_frequencia_pode_deixar_decision_end_sem_intent() -> None:
    """``decision_end`` fora da grade é consultado e não decide — sem forçar nada.

    Nenhuma chamada extraordinária é inventada no fim da janela: o participante
    não sabe que aquela é a última sessão avaliada, e o motor não lhe conta.
    """
    data = frame(60)
    agent = participant(client_always("COMPRA"), decision_frequency=5)
    result = run(data, agent, decision_start=day(data, 10), decision_end=day(data, 17))

    decided = [record.session for record in agent.decisions]
    assert decided == [at(data, 10), at(data, 15)]
    assert at(data, 17) not in decided
    # O settlement (posição 18) não tinha pendente: nenhum trade nasce ali.
    assert at(data, 18) not in [pd.Timestamp(trade.date) for trade in result.trades]
    assert result.equity_curve.index[-1] == at(data, 18)
