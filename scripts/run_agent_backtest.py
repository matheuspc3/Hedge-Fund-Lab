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
    parser.add_argument("--provider", choices=["mock", "omnirouter"], default="mock")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    data = read_ticker_from_db(args.ticker)
    if data is None or data.empty:
        raise SystemExit(f"Sem dados para {args.ticker}")
    data = data.tail(args.days)

    num_decisions = len(data) // args.decision_frequency
    calls_per_decision = args.analysts + 2  # analistas + risco + portfólio
    total_calls = num_decisions * calls_per_decision

    if args.dry_run:
        print("=== DRY RUN (Estimativa de Chamadas) ===")
        print(f"Ticker: {args.ticker}")
        print(f"Pregões: {len(data)}")
        print(f"Frequência de Decisão: a cada {args.decision_frequency} pregões ({num_decisions} decisões)")
        print(f"Analistas por rodada: {args.analysts}")
        print(f"Chamadas por rodada: {calls_per_decision} ({args.analysts} analistas + 1 risco + 1 portfólio)")
        print(f"Total estimado de chamadas LLM: {total_calls}")
        print("Nenhuma chamada externa realizada.")
        return

    if args.provider == "omnirouter":
        from src.agents import AgentRouterLLMClient, CachedLLMClient, RetryingLLMClient

        base_client = RetryingLLMClient(AgentRouterLLMClient())
        if not args.no_cache:
            cache_file = Path("data/cache/llm_cache.json")
            llm = CachedLLMClient(base_client, cache_file)
        else:
            llm = base_client
    else:
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
    suffix = "real" if args.provider == "omnirouter" else "mock"
    output = args.output or Path("data/agent_runs") / f"{args.ticker}_{suffix}.json"
    
    # Extrai os logs de telemetria acumulados no cliente
    telemetry_data = [t.__dict__ for t in getattr(llm, "all_telemetry", [])]
    result.save_audit(output, telemetry=telemetry_data)
    
    import logging
    logger = logging.getLogger("hedgefund.backtest")
    logger.info(
        f"{args.ticker} ({args.provider}): {result.initial_capital:.2f} -> {result.final_equity:.2f} | "
        f"{len(result.trades)} trades | auditoria: {output}"
    )
    if telemetry_data:
        total_prompts = sum(t["prompt_tokens"] for t in telemetry_data)
        total_completions = sum(t["completion_tokens"] for t in telemetry_data)
        logger.info(f"Telemetria: {len(telemetry_data)} chamadas | Prompt Tokens: {total_prompts} | Completion Tokens: {total_completions}")


if __name__ == "__main__":
    main()
