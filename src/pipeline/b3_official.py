"""Barras oficiais da B3 (COTAHIST) ajustadas pelo fator de retorno total.

Fonte de preço científica a partir do amendment de calendário/data-quality do
H2 (``docs/H2_METHODOLOGICAL_FREEZE_V1.md``, Amendment 1):

```text
OHLCV bruto   B3 Séries Históricas COTAHIST, mercado à vista (TPMERC 010),
              lote padrão (CODBDI 02) — preço oficial de cada sessão
fator         yfinance, auto_adjust=False: Adj Close / Close da mesma sessão
              (o fator acumulado de proventos que o provedor já aplicava)
barra         OHLC oficial x fator; volume = quantidade oficial negociada
```

A representação de preço continua a mesma (retorno total ajustado pelo fator
do yfinance). O que muda é o preço bruto: o do yfinance divergia do fechamento
oficial em dezenas de sessões e faltava em sessões oficiais.

Sessão científica = sessão oficial da B3 em que o ativo negociou. Nenhuma
barra é inventada: sessão oficial sem negócio do ativo falha fechado, e o
fator de uma sessão sem linha válida no yfinance só é herdado da sessão
anterior se coincidir com o da seguinte (nenhum evento entre elas).
"""

import hashlib
import io
import zipfile
from pathlib import Path
from typing import Any
from urllib import request

import numpy as np
import pandas as pd
import yfinance as yf

from src.pipeline.extract import DataExtractor
from src.pipeline.transform import validate_ohlcv

COTAHIST_URL = "https://bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_A{year}.ZIP"
PRICE_SOURCE = "b3_cotahist_ohlcv+yfinance_adjustment_factor"
#: Divergência relativa máxima entre os fatores das sessões vizinhas de uma
#: sessão sem fator no yfinance. Ruído de arredondamento do provedor é ~1e-7.
FACTOR_NEIGHBOR_TOLERANCE = 1e-6
#: Guarda contra desdobramento/grupamento: a mediana anual de
#: ``Close(yfinance) / fechamento oficial`` precisa ser 1 a menos disto.
SPLIT_GUARD_TOLERANCE = 1e-3


def read_cotahist(path: Path, symbol: str) -> pd.DataFrame:
    """Barras brutas oficiais de ``symbol`` (lote padrão, mercado à vista)."""
    rows: list[dict[str, Any]] = []
    with zipfile.ZipFile(path) as archive, archive.open(archive.namelist()[0]) as handle:
        for line in io.TextIOWrapper(handle, encoding="latin-1"):
            if line[:2] != "01" or line[24:27] != "010" or line[10:12] != "02":
                continue
            if line[12:24].strip() != symbol:
                continue
            rows.append(
                {
                    "date": pd.Timestamp(f"{line[2:6]}-{line[6:8]}-{line[8:10]}"),
                    "abertura": int(line[56:69]) / 100,
                    "maxima": int(line[69:82]) / 100,
                    "minima": int(line[82:95]) / 100,
                    "fechamento": int(line[108:121]) / 100,
                    "volume": float(int(line[152:170])),
                }
            )
    return pd.DataFrame(rows).set_index("date").sort_index() if rows else pd.DataFrame()


class B3OfficialAdjustedExtractor(DataExtractor):
    """Extrator científico: OHLCV oficial da B3 x fator de ajuste do yfinance.

    ``download_actions`` continua o do yfinance (evidência de proventos).
    ``source_description()`` alimenta o bloco ``source`` do manifest.
    """

    def __init__(self, cache_dir: str = "data/raw/cotahist") -> None:
        super().__init__(cache_dir=cache_dir)
        self.files: dict[str, str] = {}
        self.inherited_factors: dict[str, list[str]] = {}

    def _cotahist(self, year: int) -> Path:
        path = self.cache_dir / f"COTAHIST_A{year}.ZIP"
        if not path.exists():
            with request.urlopen(COTAHIST_URL.format(year=year), timeout=600) as response:
                path.write_bytes(response.read())
        self.files[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        return path

    def download(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        first, last = self._parse_interval(start, end)
        symbol = ticker.removesuffix(".SA")
        raw = pd.concat(
            [read_cotahist(self._cotahist(year), symbol) for year in range(first.year, last.year + 1)]
        )
        raw = raw.loc[(raw.index >= first) & (raw.index <= last)]
        raw = raw[raw["volume"] > 0]
        if raw.empty:
            raise ValueError(f"no official B3 bars for {symbol} in {start}..{end}")

        yahoo = yf.download(
            ticker,
            start=first.strftime("%Y-%m-%d"),
            end=(last + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
            auto_adjust=False,
            progress=False,
            actions=False,
        )
        if isinstance(yahoo.columns, pd.MultiIndex):
            yahoo.columns = [column[0] for column in yahoo.columns]
        yahoo = yahoo[(yahoo["Volume"] > 0) & (yahoo["Close"] > 0)]
        factor = (yahoo["Adj Close"] / yahoo["Close"]).reindex(raw.index)

        # Desdobramento muda o "Close" do yfinance e não o oficial: barrar.
        both = yahoo["Close"].reindex(raw.index).dropna()
        ratio = (both / raw.loc[both.index, "fechamento"]).groupby(both.index.year).median()
        if (ratio - 1).abs().max() > SPLIT_GUARD_TOLERANCE:
            raise ValueError(f"split-like mismatch between yfinance and B3 closes: {ratio.to_dict()}")

        inherited: list[str] = []
        values = factor.to_numpy(copy=True)
        for i in np.flatnonzero(np.isnan(values)):
            if i == 0 or i == len(values) - 1 or np.isnan(values[i - 1]) or np.isnan(values[i + 1]):
                raise ValueError(f"no adjustment factor around {raw.index[i].date()}")
            if abs(values[i - 1] / values[i + 1] - 1) > FACTOR_NEIGHBOR_TOLERANCE:
                raise ValueError(
                    f"adjustment factor changes around {raw.index[i].date()}; "
                    "a corporate event there makes inheritance unsafe"
                )
            values[i] = values[i - 1]
            inherited.append(str(raw.index[i].date()))
        self.inherited_factors[ticker] = inherited

        frame = raw.copy()
        for column in ("abertura", "maxima", "minima", "fechamento"):
            frame[column] = raw[column] * values
        frame.index.name = "Date"
        validate_ohlcv(frame)
        return frame

    def source_description(self) -> dict[str, Any]:
        return {
            "name": PRICE_SOURCE,
            "raw_ohlcv": "B3 COTAHIST, TPMERC 010, CODBDI 02 (official)",
            "cotahist_url": COTAHIST_URL,
            "cotahist_sha256": dict(sorted(self.files.items())),
            "adjustment_factor": "yfinance auto_adjust=False, Adj Close / Close per session",
            "inherited_factors": self.inherited_factors,
            "factor_neighbor_tolerance": FACTOR_NEIGHBOR_TOLERANCE,
        }
