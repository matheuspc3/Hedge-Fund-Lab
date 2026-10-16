"""Barras oficiais da B3 x fator do yfinance, sem rede."""

import zipfile
from pathlib import Path

import pandas as pd
import pytest

from src.pipeline import b3_official
from src.pipeline.b3_official import B3OfficialAdjustedExtractor, read_cotahist

BARS = {  # data -> (abertura, máxima, mínima, fechamento, quantidade)
    "2020-11-18": (23.00, 23.50, 22.90, 23.40, 1_000),
    "2020-11-19": (23.40, 23.80, 23.10, 23.55, 2_000),
    "2020-11-20": (23.84, 23.99, 23.47, 23.65, 3_000),
    "2020-11-23": (23.70, 24.10, 23.60, 24.00, 4_000),
}


def line(day: str, symbol: str, bar: tuple, tpmerc: str = "010") -> str:
    open_, high, low, close, quantity = bar
    cents = lambda value: f"{round(value * 100):013d}"  # noqa: E731
    text = (
        "01" + day.replace("-", "") + "02" + symbol.ljust(12) + tpmerc
    ).ljust(56)
    text += cents(open_) + cents(high) + cents(low) + cents(close) + cents(close)
    text = text.ljust(152) + f"{quantity:018d}"
    return text.ljust(245) + "\n"


@pytest.fixture
def cache(tmp_path: Path) -> Path:
    body = "00HEADER\n" + "".join(line(day, "PETR4", bar) for day, bar in BARS.items())
    body += line("2020-11-19", "VALE3", BARS["2020-11-19"])  # outro ativo
    body += line("2020-11-19", "PETR4", (1, 2, 1, 1, 9), tpmerc="070")  # opções: ignorado
    with zipfile.ZipFile(tmp_path / "COTAHIST_A2020.ZIP", "w") as archive:
        archive.writestr("COTAHIST_A2020.TXT", body.encode("latin-1"))
    return tmp_path


def yahoo(factors: dict[str, float], close_scale: float = 1.0):
    def download(*args, **kwargs):
        index = pd.DatetimeIndex(list(factors))
        close = pd.Series([BARS[d][3] * close_scale for d in factors], index=index)
        return pd.DataFrame(
            {
                "Close": close,
                "Adj Close": close * pd.Series(list(factors.values()), index=index),
                "Volume": 1.0,
            }
        )

    return download


def test_le_so_o_lote_padrao_do_mercado_a_vista_do_ativo(cache: Path) -> None:
    bars = read_cotahist(cache / "COTAHIST_A2020.ZIP", "PETR4")
    assert list(bars.index.strftime("%Y-%m-%d")) == list(BARS)
    assert bars.loc["2020-11-20", "fechamento"] == 23.65
    assert bars.loc["2020-11-20", "volume"] == 3_000


def test_ohlc_oficial_vezes_fator_e_sessao_sem_yahoo_herda_fator(
    cache: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # 2020-11-20 não existe no yfinance (caso real): herda o fator vizinho.
    factors = {"2020-11-18": 0.27, "2020-11-19": 0.27, "2020-11-23": 0.27}
    monkeypatch.setattr(b3_official.yf, "download", yahoo(factors))
    extractor = B3OfficialAdjustedExtractor(cache_dir=str(cache))
    frame = extractor.download("PETR4.SA", "2020-11-18", "2020-11-23")
    assert list(frame.index.strftime("%Y-%m-%d")) == list(BARS)
    assert frame.loc["2020-11-20", "fechamento"] == pytest.approx(23.65 * 0.27)
    assert frame.loc["2020-11-20", "abertura"] == pytest.approx(23.84 * 0.27)
    assert frame.loc["2020-11-20", "volume"] == 3_000  # volume oficial, sem ajuste
    assert extractor.inherited_factors["PETR4.SA"] == ["2020-11-20"]
    source = extractor.source_description()
    assert source["name"] == b3_official.PRICE_SOURCE
    assert "COTAHIST_A2020.ZIP" in source["cotahist_sha256"]


def test_nao_herda_fator_atraves_de_evento_corporativo(
    cache: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    factors = {"2020-11-18": 0.27, "2020-11-19": 0.27, "2020-11-23": 0.26}
    monkeypatch.setattr(b3_official.yf, "download", yahoo(factors))
    with pytest.raises(ValueError, match="corporate event"):
        B3OfficialAdjustedExtractor(cache_dir=str(cache)).download(
            "PETR4.SA", "2020-11-18", "2020-11-23"
        )


def test_desdobramento_no_yahoo_e_recusado(
    cache: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    factors = dict.fromkeys(BARS, 0.27)
    monkeypatch.setattr(b3_official.yf, "download", yahoo(factors, close_scale=0.5))
    with pytest.raises(ValueError, match="split-like"):
        B3OfficialAdjustedExtractor(cache_dir=str(cache)).download(
            "PETR4.SA", "2020-11-18", "2020-11-23"
        )
