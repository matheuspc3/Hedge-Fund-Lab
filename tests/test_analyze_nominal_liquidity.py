from typing import cast

import pandas as pd

from scripts.analyze_nominal_liquidity import (
    MINIMUM_HISTORY_SESSIONS,
    content_sha256,
    eligible_sessions,
    liquidity,
    split_check,
)


def _bars(index, close, volume, splits: float | pd.Series = 0.0):
    return pd.DataFrame(
        {"Open": close, "Close": close, "Volume": volume, "Stock Splits": splits},
        index=index,
    )


def test_elegiveis_comecam_na_504a_sessao_comum_e_gate_e_a_pior_mediana_movel():
    index = pd.bdate_range("2016-01-01", periods=MINIMUM_HISTORY_SESSIONS + 600)
    volume = pd.Series(1_000.0, index=index)
    volume.iloc[-400:-200] = 100.0  # 200 sessões ruins: domina uma janela de 252
    volume.iloc[-1] = 0.0  # volume zero é excluído, não vira ADV zero
    a = _bars(index, 10.0, volume)
    b = _bars(index, 5.0, 2_000.0)
    b.loc[index[3], "Open"] = 0.0  # barra incompleta tira a sessão do calendário comum

    eligible = eligible_sessions({"A": a, "B": b})
    result = liquidity(a, eligible)

    assert eligible[0] == index[MINIMUM_HISTORY_SESSIONS]
    assert result["sessions_excluded_zero_volume"] == 1
    assert result["median_eligible_adv_brl"] == 10_000.0
    assert result["worst_252_median_adv_brl"] == 1_000.0
    assert result["order_to_worst_adv"] == 100.0


def test_split_check_aceita_escala_coerente_e_rejeita_quebra_artificial():
    index = pd.bdate_range("2024-03-01", periods=40)
    event = cast(pd.Timestamp, index[20])
    splits = pd.Series(0.0, index=index)
    splits[event] = 2.0
    session = event.date().isoformat()
    # Coerente: Close e Volume ajustados pelo mesmo fator -> FV contínuo.
    coherent = _bars(index, 28.0, 1_000.0, splits)
    # Quebrado: o preço cai à metade no evento e o volume não dobra -> FV cai 2x.
    broken = _bars(index, 28.0, 1_000.0, splits)
    broken.loc[index >= event, "Close"] = 14.0

    assert split_check(coherent, "X", session, 2.0)["coherent"] is True
    assert split_check(broken, "X", session, 2.0)["coherent"] is False
    # razão registrada divergente da esperada também reprova
    assert split_check(coherent, "X", session, 3.0)["coherent"] is False


def test_hash_de_conteudo_nao_depende_da_ordem_das_chaves():
    assert content_sha256({"a": 1, "b": 2}) == content_sha256({"b": 2, "a": 1})
