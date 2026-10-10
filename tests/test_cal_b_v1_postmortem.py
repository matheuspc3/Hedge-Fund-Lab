"""Regras do post-mortem da CAL-B v1: maioria estrita, sinais de features e afirmação de banda."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import cal_b_v1_postmortem as pm  # noqa: E402


def test_maioria_estrita_por_prefixo() -> None:
    assert pm.majority(["COMPRA", "MANTER", "COMPRA"]) == "COMPRA"
    assert pm.majority(["COMPRA", "MANTER", "COMPRA", "MANTER"]) == "NO_MAJORITY"
    assert pm.majority(["MANTER"] * 3 + ["COMPRA"] * 2) == "MANTER"


def test_sinais_e_posicao_na_banda() -> None:
    base = {"sma50_gap": 0.01, "sma200_gap": -0.02, "bb_upper_gap": -0.05, "bb_lower_gap": 0.05, "bb_width": 0.1,
            "rsi": 72.0, "macd_ratio": 0.01, "macd_signal_ratio": 0.02}
    s = pm.feature_signs(base)
    assert (s["sma50_gap"], s["sma200_gap"], s["macd_minus_signal"]) == ("+", "-", "-")
    assert s["bollinger_position"] == "INSIDE" and s["rsi_zone"] == "OVERBOUGHT(>70)"
    assert 0 < s["bollinger_percent_b"] < 1
    assert pm.feature_signs({**base, "bb_upper_gap": 0.01})["bollinger_position"] == "ABOVE_UPPER"
    assert pm.feature_signs({**base, "bb_lower_gap": -0.01})["bollinger_position"] == "BELOW_LOWER"


def test_afirmacao_de_rompimento_da_banda_superior() -> None:
    claim = lambda t: bool(re.search(pm.UPPER_BREACH_CLAIM, t, re.IGNORECASE))  # noqa: E731
    assert claim("o preço rompeu levemente acima da banda superior de Bollinger")
    assert claim("O preço ultrapassou ligeiramente a banda superior")
    assert not claim("o preço próximo à banda superior sugere consolidação")
    assert not claim("opera acima das médias móveis, dentro das bandas de Bollinger")
