"""Provas do contrato causal transmitido ao provedor de LLM.

Duas propriedades são exercidas aqui, e nenhuma delas é verificável lendo o
código:

``ESCALA``
    Multiplicar todo o prefixo histórico disponível em ``t`` por ``k > 0`` não
    pode mudar nada que o provedor veja. O nível da série ajustada depende de
    proventos posteriores a ``t``; se o prompt mudasse com ``k``, o modelo
    estaria lendo o futuro.

``ANONIMATO``
    Ticker e data abrem um canal distinto — memorização do próprio modelo — e
    também não podem atravessar. Eles continuam íntegros nos artefatos de
    auditoria, e é isso que separa "o provedor não sabe" de "ninguém sabe".

``k`` é deliberadamente **não** potência de dois: com ``k = 2`` a aritmética
IEEE-754 preserva os bits por sorte de expoente e o teste passaria mesmo sem a
quantização canônica, que é justamente o mecanismo sob teste.
"""

import asyncio
import json
from types import MappingProxyType
from typing import Any, cast

import numpy as np
import pandas as pd
import pytest

from src.agents.features import (
    FEATURE_KEYS,
    LLM_NUMERIC_PRECISION,
    canonical_number,
    dimensionless_features,
)
from src.agents.llm_client import LLMClient, MockLLMClient
from src.agents.llm_trace import ReplayLLMClient
from src.agents.participant import LLMParticipant
from src.agents.risk_manager import RiskConfig, RiskManager
from src.agents.state import (
    AgentState,
    PortfolioAction,
    RiskVerdict,
    TechnicalSignal,
)
from src.backtesting.arena import (
    QUANTITY_MODE_FRACTIONAL_NOTIONAL,
    ExecutionEngine,
    MarketObservation,
)
from src.backtesting.costs import CostModel

TICKER = "PETR4"
CAPITAL = 100_000.0

#: Fator de escala realista — a PETR4 do cache local está ~3,87x abaixo do
#: preço negociado em 2016 por causa do ajuste de proventos.
SCALE = 3.8718

#: Deriva de vintage de cinco semanas medida na PETR4 (~3,1%). Com o preço-base
#: deste módulo ela põe a razão de concentração **abaixo** do limiar por um
#: ULP, que é exatamente o modo de falha que a canonicalização existe para
#: fechar: sem ela, a mesma carteira seria vetada num vintage e aprovada no
#: outro.
BOUNDARY_SCALE = 1.0314

#: Preço-base distintivo: aparecer em qualquer prompt é prova de vazamento de
#: nível, e nenhum dígito dele colide com um valor de feature plausível.
BASE_PRICE = 137.4321


def long_frame(scale: float = 1.0) -> pd.DataFrame:
    """Recorte longo o bastante para que **todas** as features existam.

    240 pregões cobrem a SMA de 200, que é a janela mais longa do contrato.
    """
    sessions = pd.bdate_range("2022-01-03", periods=240)
    steps = np.arange(len(sessions), dtype=float)
    close = BASE_PRICE + steps * 0.21 + np.sin(steps / 7.0) * 9.0
    return pd.DataFrame(
        {"abertura": close * 0.994, "fechamento": close},
        index=sessions,
    ) * scale


def scripted_client() -> MockLLMClient:
    """Mock determinístico: a decisão é fixa, o prompt é o objeto sob teste."""
    return MockLLMClient(
        {
            TechnicalSignal: {
                "signal": "COMPRA",
                "justification": "mock",
                "confidence": 0.75,
            },
            RiskVerdict: {
                "verdict": "APROVADO",
                "analysis": "mock",
                "risk_metrics": {},
            },
            PortfolioAction: {"decision": "COMPRA", "reasoning": "mock"},
        }
    )


def participant(client: LLMClient) -> LLMParticipant:
    return LLMParticipant(
        TICKER,
        llm_client=client,
        analyst_count=1,
        consensus_threshold=1.0,
        risk_max_volatility=100.0,
        risk_max_drawdown=1.0,
        risk_max_concentration=1.0,
        long_target_weight=1.0,
    )


def decide_once(scale: float, units: float) -> LLMParticipant:
    """Uma decisão completa sobre a série escalada, com carteira equivalente.

    ``units`` é a quantidade na escala base; sob escala ``k`` a execução
    fracionária devolve ``units / k``, de modo que ``quantidade x preço`` — e
    portanto a concentração — permanece o mesmo número.
    """
    data = long_frame(scale)
    agent = participant(scripted_client())
    held = units / scale
    close = float(cast(pd.Series, data["fechamento"]).iloc[-1])
    equity = CAPITAL + held * close
    agent.decide(
        MarketObservation(
            session=cast(pd.Timestamp, data.index[-1]),
            history=MappingProxyType({TICKER: data}),
            positions=MappingProxyType({TICKER: held}),
            cash=CAPITAL,
            equity=equity,
        )
    )
    return agent


def prompt_identities(agent: LLMParticipant) -> list[tuple[str, str]]:
    """Estágio e hash do prompt lógico, na ordem de emissão."""
    return [
        (record.request.stage, record.request.combined_prompt_sha256)
        for record in agent.llm_calls
    ]


def features_of(prompt: str) -> dict[str, float]:
    """Payload de features de um prompt técnico, tal como o provedor o recebe."""
    line = next(line for line in prompt.splitlines() if line.startswith("Features: "))
    return json.loads(line.removeprefix("Features: "))


# ── Invariância de escala ────────────────────────────────────────


@pytest.mark.parametrize("scale", [SCALE, 1.031387, 1000.0, 0.25])
def test_features_sao_identicas_sob_qualquer_escala(scale: float) -> None:
    """``features(k * historico) == features(historico)``, campo a campo."""
    levels = {
        "sma_50": 131.5,
        "sma_200": 120.25,
        "bb_upper": 145.125,
        "bb_middle": 136.0,
        "bb_lower": 126.875,
        "rsi": 58.25,
        "macd": 1.375,
        "macd_sinal": 0.875,
    }
    scaled = {
        key: (value if key == "rsi" else value * scale) for key, value in levels.items()
    }

    assert dimensionless_features(BASE_PRICE * scale, scaled) == dimensionless_features(
        BASE_PRICE, levels
    )


def test_prompt_de_todos_os_estagios_e_identico_sob_escala() -> None:
    """SCALE INVARIANCE: analista, risco e portfólio, não só o primeiro."""
    base = decide_once(1.0, units=200.0)
    scaled = decide_once(SCALE, units=200.0)

    stages = {stage for stage, _ in prompt_identities(base)}
    assert stages == {"technical_analyst", "risk_manager", "portfolio_manager"}
    assert prompt_identities(base) == prompt_identities(scaled)


def test_quantizacao_e_o_que_torna_a_identidade_possivel() -> None:
    """Sem a quantização, a igualdade seria de álgebra e não de bytes.

    Guarda o motivo da constante: a razão bruta **difere** entre as escalas, e
    é o arredondamento canônico que as reconcilia. Se um dia a aritmética
    passar a ser exata, este teste falha e a constante pode ser revista.
    """
    raw_base = BASE_PRICE / 131.5 - 1.0
    raw_scaled = (BASE_PRICE * SCALE) / (131.5 * SCALE) - 1.0

    assert raw_base != raw_scaled
    assert canonical_number(raw_base) == canonical_number(raw_scaled)
    assert round(raw_base, LLM_NUMERIC_PRECISION) == canonical_number(raw_base)


# ── Anonimato e trava de contrato ────────────────────────────────


def test_nenhum_prompt_revela_ticker_data_ou_nivel_de_preco() -> None:
    """ANONYMIZATION: o provedor não recebe identidade, calendário nem nível."""
    agent = decide_once(1.0, units=200.0)
    data = long_frame()
    session = cast(pd.Timestamp, data.index[-1])
    close = float(cast(pd.Series, data["fechamento"]).iloc[-1])

    proibidos = (
        TICKER,
        session.date().isoformat(),
        str(session.year),
        repr(close),
        f"{close:.4f}",
        f"{BASE_PRICE}",
    )
    for record in agent.llm_calls:
        texto = record.request.system_prompt + "\n" + record.request.user_prompt
        for proibido in proibidos:
            assert proibido not in texto, f"{proibido!r} vazou em {record.request.stage}"


def test_auditoria_preserva_ticker_e_data_que_o_provedor_nao_ve() -> None:
    """O trace continua sabendo o que o provedor não sabe."""
    agent = decide_once(1.0, units=200.0)
    session = cast(pd.Timestamp, long_frame().index[-1])

    assert agent.ticker == TICKER
    assert {record.request.decision_session for record in agent.llm_calls} == {
        session.date().isoformat()
    }
    assert agent.decisions[0].session == session


def test_contrato_de_prompt_trava_o_conjunto_de_campos() -> None:
    """PROMPT CONTRACT LOCK: nenhum campo fora do contrato atravessa."""
    agent = decide_once(1.0, units=200.0)
    técnico = next(
        record
        for record in agent.llm_calls
        if record.request.stage == "technical_analyst"
    )
    risco = next(
        record for record in agent.llm_calls if record.request.stage == "risk_manager"
    )

    assert set(features_of(técnico.request.user_prompt)) == set(FEATURE_KEYS)

    payload = json.loads(risco.request.user_prompt)
    assert set(payload) == {"technical_signal", "risk_metrics"}
    assert set(payload["risk_metrics"]) <= {
        "recent_volatility",
        "current_drawdown",
        "current_concentration",
    }
    assert set(payload["technical_signal"]) == {"signal", "justification", "confidence"}


# ── Regras duras de risco na fronteira ───────────────────────────


def risk_state(price: float, position: float, equity: float) -> AgentState:
    return {
        "ticker": TICKER,
        "date": "2024-01-02",
        "features": {"rsi": 50.0},
        "cash": equity - position * price,
        "position": position,
        "current_price": price,
        "equity": equity,
        "recent_volatility": 0.10,
        "current_drawdown": 0.01,
        "errors": [],
        "technical_signal": TechnicalSignal(
            signal="COMPRA", justification="mock", confidence=0.5
        ),
    }


def test_veredito_duro_de_risco_e_invariante_na_fronteira() -> None:
    """HARD-RISK INVARIANCE: o limiar é atravessado pela mesma representação.

    A concentração é posta exatamente sobre o limite. Em ponto flutuante as
    duas escalas produzem razões **diferentes**, uma de cada lado; só a
    representação canônica as reconcilia antes da comparação.
    """
    manager = RiskManager(scripted_client(), RiskConfig(max_concentration=0.25))
    price = BASE_PRICE
    position = 0.25 * CAPITAL / price
    preço_escalado = price * BOUNDARY_SCALE
    posição_escalada = position / BOUNDARY_SCALE

    raw_base = position * price / CAPITAL
    raw_scaled = posição_escalada * preço_escalado / CAPITAL
    assert raw_base != raw_scaled, "cenário deixou de exercer a fronteira"

    veredito_base = asyncio.run(
        manager.evaluate(risk_state(price, position, CAPITAL))
    )["risk_verdict"]
    veredito_scaled = asyncio.run(
        manager.evaluate(risk_state(preço_escalado, posição_escalada, CAPITAL))
    )["risk_verdict"]

    assert veredito_base.verdict == veredito_scaled.verdict == "VETADO"
    assert (
        veredito_base.risk_metrics["current_concentration"]
        == veredito_scaled.risk_metrics["current_concentration"]
        == 0.25
    )


# ── Invariância de vintage sob replay ────────────────────────────


def run_engine(data: pd.DataFrame, client: LLMClient) -> LLMParticipant:
    agent = participant(client)
    ExecutionEngine(
        agent,
        {TICKER: data},
        CAPITAL,
        CostModel(tax_rate=0.00032),
        decision_start=data.index[236],
        decision_end=data.index[237],
        quantity_mode=QUANTITY_MODE_FRACTIONAL_NOTIONAL,
    ).run()
    return agent


def test_replay_de_vintage_escalado_consome_o_trace_inteiro() -> None:
    """VINTAGE INVARIANCE: dois vintages, uma única decisão científica.

    O ``ReplayLLMClient`` compara identidade de chamada e levanta na primeira
    divergência de prompt — é o verificador mais estrito disponível, e aqui ele
    atravessa um run inteiro sobre a série reescalada.
    """
    gravado = run_engine(long_frame(), scripted_client())
    trace: Any = gravado.run_artifacts()[0].content

    replay = ReplayLLMClient.from_trace(trace, provider="mock", requested_model="")
    run_engine(long_frame(SCALE), replay)

    replay.assert_complete()
    assert replay.consumed == len(gravado.llm_calls) > 0
