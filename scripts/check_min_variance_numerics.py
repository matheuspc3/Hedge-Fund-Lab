"""Past-data-only numerical validation: same covariance, objective and long-only simplex."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from scipy.optimize import minimize

import replay_multiasset as r
from continuous_replay_data import ROOT


def check():
    data = r.checked(ROOT / "inputs/market.json")["assets"]
    m = r.checked(ROOT / "inputs/manifest.json")
    out = []
    for index in (0, 63, 126):
        day = m["sessions"][index]
        symbols = sorted(data)
        prices = pd.DataFrame({t: pd.Series({x["date"]: x["close"] * x["factor"] for x in data[t]["rows"] if x["date"] <= day}).iloc[-253:] for t in symbols})
        cov = prices.pct_change().dropna().cov().values
        assert len(prices) == 253 and max(prices.index) == day
        equal = np.full(len(symbols), 1 / len(symbols))
        objective = lambda w: float(w @ cov @ w)
        kw = dict(method="SLSQP", bounds=[(0, 1)] * len(symbols), constraints={"type": "eq", "fun": lambda w: w.sum() - 1})
        old = minimize(objective, equal, **kw)
        scale = float(np.max(np.abs(cov)))
        reference = minimize(lambda w: objective(w) / scale, equal, **kw)
        assert reference.success and min(reference.x) >= -1e-12 and abs(sum(reference.x) - 1) < 1e-8
        gradient = 2 * cov @ old.x
        candidate = old.x.copy()
        step = min(.05, float(candidate[np.argmax(gradient)]))
        candidate[np.argmax(gradient)] -= step
        candidate[np.argmin(gradient)] += step
        improved = objective(candidate) < objective(old.x) - 1e-12
        assert improved, "diagnostic expected a feasible descent from the legacy equal weights"
        assert objective(reference.x) < objective(old.x) - 1e-12
        out.append({"decision_session": day, "input_start": min(prices.index), "last_input": max(prices.index), "past_returns": len(prices) - 1, "tickers": symbols, "covariance": cov.tolist(), "legacy": {"success": bool(old.success), "iterations": int(old.nit), "weights": old.x.tolist(), "variance": objective(old.x), "gradient": gradient.tolist(), "interior_kkt_gradient_spread": float(np.ptp(gradient))}, "feasible_local_candidate": {"weights": candidate.tolist(), "variance": objective(candidate), "strictly_improves": bool(improved)}, "scale": scale, "scaled_reference": {"success": bool(reference.success), "iterations": int(reference.nit), "weights": reference.x.tolist(), "variance": objective(reference.x)}, "variance_reduction_pct": (1 - objective(reference.x) / objective(old.x)) * 100})
    doc = {"diagnosis": "PREMATURE_NUMERICAL_CONVERGENCE_NOT_OPTIMAL_EQUAL_WEIGHTS", "method": "Multiplying objective by positive 1/max(abs(covariance)) preserves its minimizer and all constraints; no lookback/frequency/return tuning", "samples": out}
    r.save(ROOT / "optimizer_diagnostic.json", doc)
    return {"diagnosis": doc["diagnosis"], "samples": [{"day": x["decision_session"], "legacy_iterations": x["legacy"]["iterations"], "scaled_iterations": x["scaled_reference"]["iterations"], "variance_reduction_pct": x["variance_reduction_pct"]} for x in out]}


if __name__ == "__main__":
    print(json.dumps(check(), indent=2))
