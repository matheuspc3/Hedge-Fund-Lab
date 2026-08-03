"""Executa uma demonstração reproduzível do comitê com respostas simuladas."""

import argparse
import sys
from pathlib import Path

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
from src.backtesting import AgentBacktestEngine


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", default="WEGE3.SA")
    parser.add_argument("--days", type=int, default=60)
    parser.add_argument("--analysts", type=int, default=30)
    parser.add_argument("--threshold", type=float, default=5 / 6)
    parser.add_argument("--decision-frequency", type=int, default=5)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    data = read_ticker_from_db(args.ticker)
    if data is None or data.empty:
        raise SystemExit(f"Sem dados para {args.ticker}")
    data = data.tail(args.days)

    llm = MockLLMClient(
        {
            TechnicalSignal: {
                "signal": "COMPRA",
                "justification": "Demonstração determinística",
                "confidence": 0.7,
            },
            RiskVerdict: {
                "verdict": "APROVADO",
                "analysis": "Demonstração determinística",
                "risk_metrics": {},
            },
            FinalDecision: {
                "decision": "COMPRA",
                "position_size": 0.10,
                "reasoning": "Demonstração determinística",
            },
        }
    )
    graph = build_graph(
        llm,
        ensemble_config=AnalystEnsembleConfig(
            analyst_count=args.analysts,
            consensus_threshold=args.threshold,
        ),
    )
    result = AgentBacktestEngine(
        graph,
        data,
        args.ticker,
        decision_frequency=args.decision_frequency,
    ).run()
    output = args.output or Path("data/agent_runs") / f"{args.ticker}_mock.json"
    result.save_audit(output)
    print(
        f"{args.ticker}: {result.initial_capital:.2f} -> {result.final_equity:.2f} | "
        f"{len(result.trades)} trades | auditoria: {output}"
    )


if __name__ == "__main__":
    main()
