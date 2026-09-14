"""Avança o participante LLM em exatamente um pregão persistido."""

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.generate_dashboard_data import read_ticker_from_db
from src.agents import (
    AnalystEnsembleConfig,
    FinalDecision,
    MockLLMClient,
    RiskVerdict,
    TechnicalSignal,
    build_graph,
)
from src.backtesting import CostModel, DailyAgentRunner

logger = logging.getLogger("hedgefund.daily_agent")


def _build_graph(args):
    if args.provider == "omnirouter":
        from src.agents import AgentRouterLLMClient, CachedLLMClient, RetryingLLMClient

        client = RetryingLLMClient(AgentRouterLLMClient())
        llm = (
            client
            if args.no_cache
            else CachedLLMClient(client, Path("data/cache/llm_cache.json"))
        )
    else:
        llm = MockLLMClient(
            {
                TechnicalSignal: {
                    "signal": "COMPRA",
                    "justification": "Demonstração diária determinística",
                    "confidence": 0.7,
                },
                RiskVerdict: {
                    "verdict": "APROVADO",
                    "analysis": "Demonstração diária determinística",
                    "risk_metrics": {},
                },
                FinalDecision: {
                    "decision": "COMPRA",
                    "position_size": 0.10,
                    "reasoning": "Demonstração diária determinística",
                },
            }
        )
    return build_graph(
        llm,
        ensemble_config=AnalystEnsembleConfig(
            analyst_count=args.analysts,
            consensus_threshold=args.threshold,
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", default="WEGE3.SA")
    parser.add_argument("--history-days", type=int, default=252)
    parser.add_argument("--analysts", type=int, default=30)
    parser.add_argument("--threshold", type=float, default=5 / 6)
    parser.add_argument("--provider", choices=["mock", "omnirouter"], default="mock")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--as-of", type=pd.Timestamp)
    parser.add_argument("--initial-capital", type=float, default=100_000.0)
    parser.add_argument("--brokerage-fixed", type=float, default=0.0)
    parser.add_argument("--spread-bps", type=float, default=0.0)
    parser.add_argument("--tax-rate", type=float, default=0.0)
    parser.add_argument("--state", type=Path)
    args = parser.parse_args()

    data = read_ticker_from_db(args.ticker)
    if data is None or data.empty:
        raise SystemExit(f"Sem dados para {args.ticker}")
    if args.history_days < 2:
        raise SystemExit("--history-days deve ser >= 2")
    data = data.tail(args.history_days)

    suffix = "real" if args.provider == "omnirouter" else "mock"
    state_path = args.state or Path("data/agent_daily") / f"{args.ticker}_{suffix}.json"
    runner = DailyAgentRunner(
        _build_graph(args),
        args.ticker,
        state_path,
        initial_capital=args.initial_capital,
        cost_model=CostModel(
            brokerage_fixed=args.brokerage_fixed,
            spread_bps=args.spread_bps,
            tax_rate=args.tax_rate,
        ),
    )
    outcome = runner.run(data, as_of=args.as_of)
    if outcome.advanced:
        latest = outcome.state.decisions[-1]
        processed_session = outcome.state.last_session
        if processed_session is None:
            raise RuntimeError("advanced daily run without a processed session")
        logger.info(
            "%s: sessão %s processada | decisão=%s | status=%s | alvo=%s | estado=%s",
            args.ticker,
            processed_session.date(),
            latest.final_decision.decision if latest.final_decision else "NENHUMA",
            latest.status,
            outcome.expected_session.date(),
            state_path,
        )
    else:
        logger.info(
            "%s: aguardando barra da sessão %s | estado=%s",
            args.ticker,
            outcome.expected_session.date(),
            state_path,
        )


if __name__ == "__main__":
    main()
