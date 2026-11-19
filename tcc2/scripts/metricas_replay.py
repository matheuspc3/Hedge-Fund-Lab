"""Métricas de risco e figuras do Replay Contínuo Abril-Novembro 2026 (v1, v2, v3).

Uso, na raiz do repositório:
    PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe tcc2/scripts/metricas_replay.py

Lê tcc2/evidence/04-replay-abril-novembro/dados/series-v{1,2,3}/daily.csv,
reutiliza src/backtesting/metrics.py (Sharpe H2_SCIENTIFIC_SHARPE_DEFINITION_V1)
e grava:
    tcc2/agent-reports/METRICAS_REPLAY.md
    tcc2/chapters/tabelas/metricas-replay.tex
    tcc2/figures/replay-series.csv + replay-{patrimonio,drawdown,caixa}.tex (pgfplots)
Os asserts conferem os dados contra o documento mestre
(relatorios/evolucao_replay_v1_v2_v3_tcc.md); se algum falhar, nada é gravado.
"""

import csv
import json
import math
import sys
from pathlib import Path

import pandas as pd

TCC2 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TCC2.parent))

from src.backtesting.metrics import (  # noqa: E402
    SCIENTIFIC_SHARPE_DEFINITION,
    annualized_return,
    annualized_volatility,
    drawdown_series,
    max_drawdown,
    max_drawdown_duration,
    periodic_returns,
    scientific_sharpe,
    sortino_ratio,
    total_return,
)

DADOS = TCC2 / "evidence/04-replay-abril-novembro/dados"
CAPITAL = 100_000.0
INICIO = pd.Timestamp("2026-04-02")  # fechamento de referência da cesta inicial
CESTA = {"BBAS3": 855, "ITUB4": 461, "PETR4": 415, "VALE3": 239, "WEGE3": 397}
CUSTO = 0.0003  # 0,03% sobre o valor bruto de cada operação pós-entrada
REFS = ["BUY_HOLD", "SMA_50_200", "BOLLINGER_20_2", "EQUAL_WEIGHT_63", "MIN_VARIANCE_252_63"]
# chave -> (versão, estratégia, nome, nome LaTeX, estilo pgfplots P&B)
CARTEIRAS = {
    "ma_v1": ("v1", "MULTIAGENT", "Multiagentes v1", "Multiagentes v1",
              "black, thick, densely dotted"),
    "ma_v2": ("v2", "MULTIAGENT", "Multiagentes v2", "Multiagentes v2",
              "black, thick, dashed"),
    "ma_v3": ("v3", "MULTIAGENT", "Multiagentes v3", "Multiagentes v3",
              "black, very thick"),
    "bh": ("v1", "BUY_HOLD", "Buy & Hold", r"Buy \& Hold", "gray, thin"),
    "sma": ("v1", "SMA_50_200", "SMA 50/200", "SMA 50/200", "gray, dashdotted"),
    "boll": ("v1", "BOLLINGER_20_2", "Bollinger 20/2", "Bollinger 20/2",
             "gray, mark=square*, mark repeat=15, mark size=1.4pt"),
    "ew": ("v1", "EQUAL_WEIGHT_63", "Equal Weight 63d", "Equal Weight 63d",
           "gray, densely dashed, mark=o, mark repeat=15, mark size=1.6pt, mark options={solid}"),
    "mv": ("v1", "MIN_VARIANCE_252_63", "Mínima Variância 252/63",
           "Mínima Variância 252/63",
           "gray, mark=triangle*, mark repeat=15, mark size=1.8pt"),
}
# Valores auditados do documento mestre (§5.1 e tabela de concentração/caixa).
MESTRE = {  # final, compras, vendas, custos
    "ma_v1": (82178.71, 50, 36, 184.40), "ma_v2": (85743.57, 22, 16, 119.87),
    "ma_v3": (100067.36, 29, 52, 120.07), "bh": (88791.11, 0, 0, 0.00),
    "sma": (88866.68, 2, 4, 32.23), "boll": (104887.05, 12, 12, 151.26),
    "ew": (89869.29, 9, 6, 5.11), "mv": (95814.84, 8, 6, 27.94),
}
MESTRE_CAIXA = {"v1": (12.98, 1.64), "v2": (24.69, 45.86), "v3": (14.94, 0.75)}
MESTRE_MIN_MAX = {"v1": (80833.37, 104843.58), "v2": (84536.05, 104844.91),
                  "v3": (91337.03, 109275.01)}


def carregar(versao):
    df = pd.read_csv(DADOS / f"series-{versao}/daily.csv", encoding="utf-8-sig",
                     parse_dates=["session"])
    assert len(df) == 918, (versao, len(df))
    assert set(df.status) <= {"COMPLETED", "NO_ANALYSIS"}
    assert (df.strategy.value_counts() == 153).all() and df.strategy.nunique() == 6
    return df.sort_values(["strategy", "session"]).reset_index(drop=True)


def metricas(d):
    curva = pd.concat([pd.Series([CAPITAL], index=[INICIO]), d.set_index("session").equity])
    r = periodic_returns(curva)
    dd = drawdown_series(curva)
    vale = dd.idxmin()
    sh = scientific_sharpe(curva)
    assert sh["definition"] == SCIENTIFIC_SHARPE_DEFINITION and not sh["convention_zero"]
    # Operação = mudança de quantidade de um ativo entre estados diários consecutivos.
    pos = [CESTA] + [{t: int(q) for t, q in json.loads(p).items()} for p in d.positions]
    deltas = [b.get(t, 0) - a.get(t, 0)
              for a, b in zip(pos, pos[1:]) for t in CESTA if a.get(t, 0) != b.get(t, 0)]
    custos = float(d.costs.iloc[-1])
    # ponytail: volume derivado do custo acumulado (custo / 0,03%); o arredondamento
    # do custo ao centavo limita o erro a ~R$ 16,67 por operação. Upgrade: somar o
    # bruto das operações (só existe para a Multiagentes nos CSVs de auditoria).
    volume = custos / CUSTO
    caixa = d.cash / d.equity * 100
    return {
        "curva": curva, "dd": dd, "caixa": caixa,
        "final": float(curva.iloc[-1]),
        "ret": total_return(curva) * 100,
        "ret_a": annualized_return(curva, freq=252) * 100,
        "vol": annualized_volatility(r, freq=252) * 100,
        "sharpe": sh["sharpe"],
        # Erro-padrão aproximado do Sharpe sob retornos iid (Lo, 2002), anualizado.
        "ep_sharpe": math.sqrt((1 + (sh["sharpe"] / math.sqrt(252)) ** 2 / 2) / len(r))
        * math.sqrt(252),
        "sortino": sortino_ratio(r, rf=0.0, mar=0.0, freq=252),
        "mdd": max_drawdown(curva) * 100,
        "pico": curva[:vale].idxmax(), "vale": vale,
        "dur": max_drawdown_duration(curva),
        "compras": sum(x > 0 for x in deltas), "vendas": sum(x < 0 for x in deltas),
        "custos": custos, "volume": volume, "giro": volume / float(d.equity.mean()),
        "cx_medio": float(caixa.mean()), "cx_final": float(caixa.iloc[-1]),
        "n_ret": len(r),
    }


# ---------------------------------------------------------------- dados + checks
dfs = {v: carregar(v) for v in ("v1", "v2", "v3")}
CMP = ["session", "strategy", "cash", "costs", "equity", "positions", "receivable"]
ref = {v: df[df.strategy.isin(REFS)][CMP].reset_index(drop=True) for v, df in dfs.items()}
assert ref["v1"].equals(ref["v2"]) and ref["v1"].equals(ref["v3"]), "referências divergem"
sessoes = dfs["v1"].session.drop_duplicates().sort_values().reset_index(drop=True)
assert all(df.session.drop_duplicates().sort_values().reset_index(drop=True).equals(sessoes)
           for df in dfs.values()) and len(sessoes) == 153
sem_analise = {v: sorted(df[(df.strategy == "MULTIAGENT") & (df.status == "NO_ANALYSIS")]
                         .session.dt.strftime("%d/%m")) for v, df in dfs.items()}

M = {k: metricas(dfs[v][dfs[v].strategy == s]) for k, (v, s, *_) in CARTEIRAS.items()}
for k, (final, c, vd, custo) in MESTRE.items():
    m = M[k]
    assert round(m["final"], 2) == final, (k, m["final"])
    assert (m["compras"], m["vendas"]) == (c, vd), (k, m["compras"], m["vendas"])
    assert round(m["custos"], 2) == custo, (k, m["custos"])
    assert m["n_ret"] == 153
for v, (medio, final) in MESTRE_CAIXA.items():
    m = M[f"ma_{v}"]
    assert (round(m["cx_medio"], 2), round(m["cx_final"], 2)) == (medio, final), v
    assert (round(m["curva"].iloc[1:].min(), 2), round(m["curva"].max(), 2)) == \
        MESTRE_MIN_MAX[v], v


# ---------------------------------------------------------------- formatação
def br(x, nd=2):
    return f"{x:,.{nd}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def tx(x, nd=2):
    s = br(x, nd).replace(",", "{,}")
    return f"${s}$" if x < 0 else s


def dt(t):
    return t.strftime("%d/%m")


def escrever(caminho, texto):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)


# ---------------------------------------------------------------- relatório MD
md = [
    "# Métricas de risco do Replay Contínuo Abril–Novembro 2026 (v1, v2, v3)",
    "",
    "Gerado por `tcc2/scripts/metricas_replay.py` a partir dos `daily.csv` selados em "
    "`tcc2/evidence/04-replay-abril-novembro/dados/series-v{1,2,3}/`. Vínculo: DP-37 / "
    "`REPLAY-01..03`, material do capítulo de resultados (`TCC-02/03`).",
    "",
    "> **Ressalva.** 153 pregões (06/04/2026 a 12/11/2026), uma única trajetória de "
    "mercado, cinco ativos, reconstrução histórica feita depois do fechamento do "
    "período. As três versões da Multiagentes foram ajustadas a partir das auditorias "
    "desta mesma janela: os números são **dentro da amostra**, descritivos, e não "
    "têm significância estatística nem valor prospectivo (DP-09, DP-31, DP-37).",
    "",
    "## 1. Retorno e risco",
    "",
    "| Carteira | Patrimônio final (R$) | Retorno total | Retorno anualizado | "
    "Volatilidade anualizada | Sharpe | EP aprox. do Sharpe | Sortino | "
    "Máx. drawdown | Pico → vale | Duração máx. (pregões) |",
    "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|",
]
for k, (_, _, nome, *_r) in CARTEIRAS.items():
    m = M[k]
    md.append(
        f"| {nome} | {br(m['final'])} | {br(m['ret'])}% | {br(m['ret_a'])}% | "
        f"{br(m['vol'])}% | {br(m['sharpe'])} | {br(m['ep_sharpe'])} | "
        f"{br(m['sortino'])} | {br(m['mdd'])}% | {dt(m['pico'])} → {dt(m['vale'])} | "
        f"{m['dur']} |")
md += [
    "",
    "## 2. Operações, custos e caixa",
    "",
    "| Carteira | Operações (C / V) | Custos (R$) | Volume negociado estimado (R$) | "
    "Giro no período | Caixa médio | Caixa no fechamento |",
    "|---|---:|---:|---:|---:|---:|---:|",
]
for k, (_, _, nome, *_r) in CARTEIRAS.items():
    m = M[k]
    md.append(
        f"| {nome} | {m['compras'] + m['vendas']} ({m['compras']} / {m['vendas']}) | "
        f"{br(m['custos'])} | {br(m['volume'], 0)} | {br(m['giro'])}× | "
        f"{br(m['cx_medio'])}% | {br(m['cx_final'])}% |")
md += [
    "",
    "## 3. Notas metodológicas",
    "",
    "- **Curva de patrimônio.** Para cada carteira, 154 pontos: R$ 100.000,00 no "
    "fechamento de referência da cesta inicial (02/04/2026) seguidos dos 153 "
    "patrimônios de fechamento do `daily.csv` (posições a mercado + caixa + "
    "recebíveis). Daí resultam 153 retornos diários simples; dias sem operação "
    "(retorno da carteira parada ou em caixa) permanecem na série.",
    f"- **Sharpe.** Definição congelada `{SCIENTIFIC_SHARPE_DEFINITION}` de "
    "`src/backtesting/metrics.py` (função `scientific_sharpe`): "
    "`mean(r − rf/252) / std(r, ddof=1) · √252`, com **rf = 0** (taxa livre de risco "
    "nula, parâmetro do protocolo). A definição foi congelada para o protocolo H2; "
    "aqui é aplicada ao replay apenas para manter a mesma fórmula, sem que o replay "
    "seja um teste de H2. Como o caixa do replay não é remunerado, rf = 0 é coerente "
    "com a contabilidade da simulação, mas ignora o custo de oportunidade de uma "
    "taxa de juros positiva, que reduziria todos os índices.",
    "- **Erro-padrão aproximado do Sharpe.** `√((1 + SR_d²/2)/n) · √252`, com SR_d "
    "diário e n = 153, supondo retornos iid (Lo, 2002). Fica em torno de 1,3 para "
    "todas as carteiras: diferenças de Sharpe dessa ordem não se distinguem de ruído "
    "amostral nesta janela. <!-- TODO(redator): incluir Lo (2002) em references.bib "
    "se a nota for para o texto. -->",
    "- **Sortino.** `sortino_ratio` de `src/backtesting/metrics.py`, rf = 0 e MAR = 0; "
    "são defaults técnicos do módulo, não política científica congelada.",
    "- **Retorno anualizado e volatilidade.** `annualized_return` (composto, "
    "252/153) e `annualized_volatility` (desvio amostral × √252). A anualização "
    "de 153 pregões é extrapolação aritmética; serve só para comparar escalas.",
    "- **Máximo drawdown.** `max_drawdown` e `max_drawdown_duration` de "
    "`src/backtesting/metrics.py`; as datas de pico e vale (não existentes no "
    "módulo) são o fechamento de maior patrimônio anterior ao vale e o fechamento "
    "de menor drawdown. A duração conta pregões consecutivos abaixo do pico "
    "anterior (qualquer episódio, não necessariamente o do máximo drawdown).",
    "- **Operações.** Contadas como mudanças de quantidade de um ativo entre estados "
    "diários consecutivos, partindo da cesta inicial (855 BBAS3, 461 ITUB4, 415 "
    "PETR4, 239 VALE3, 397 WEGE3); a montagem da cesta não entra. Os totais "
    "conferem com o documento mestre para as oito carteiras.",
    "- **Custos e giro.** Custo = último valor acumulado da coluna `costs`. O volume "
    "negociado é estimado por custo / 0,03% (taxa única do replay); o arredondamento "
    "do custo ao centavo admite erro de até ~R$ 16,67 por operação. Giro = volume "
    "estimado / patrimônio médio dos 153 fechamentos. Não é o `turnover` legado de "
    "`metrics.py`, que mede variação de pesos e exigiria preços diários.",
    "- **Caixa.** `cash / equity` em cada fechamento (recebíveis fora do caixa).",
    "",
    "## 4. Verificações executadas (asserts do script)",
    "",
    "- 918 estados diários por versão (153 pregões × 6 carteiras), mesmas 153 sessões "
    "nas três versões; status apenas `COMPLETED` ou `NO_ANALYSIS`.",
    "- Cinco referências idênticas nas três versões em sessão, caixa, custos, "
    "patrimônio, posições e recebíveis. A única diferença textual entre os arquivos é "
    "o campo `status`: os pregões `NO_ANALYSIS` da Multiagentes (v1: "
    f"{', '.join(sem_analise['v1']) or 'nenhum'}; v2: {', '.join(sem_analise['v2'])}; "
    f"v3: {', '.join(sem_analise['v3'])}) são registrados com esse status nas seis "
    "carteiras da campanha, sem afetar os valores das referências.",
    "- Patrimônio final, compras, vendas e custos das oito carteiras iguais aos do "
    "documento mestre (§5.1); caixa médio e de fechamento e patrimônio mínimo e "
    "máximo das três Multiagentes iguais aos do documento mestre.",
    "",
    "## 5. Figuras e tabelas geradas",
    "",
    "- `tcc2/chapters/tabelas/metricas-replay.tex`: duas tabelas booktabs "
    "(`tab:replay-risco`, `tab:replay-operacoes`).",
    "- `tcc2/figures/replay-patrimonio.tex`, `replay-drawdown.tex`, `replay-caixa.tex` "
    "(pgfplots, dados em `tcc2/figures/replay-series.csv`; rótulos "
    "`fig:replay-patrimonio`, `fig:replay-drawdown`, `fig:replay-caixa`). Exigem "
    "`\\usepackage{pgfplots}` no preâmbulo de `main.tex`. matplotlib não está "
    "instalado no ambiente; por isso as figuras são compiladas pelo LaTeX.",
    "",
]
escrever(TCC2 / "agent-reports/METRICAS_REPLAY.md", "\n".join(md))

# ---------------------------------------------------------------- tabelas LaTeX
FONTE = ("Fonte: \\texttt{daily.csv} das campanhas \\texttt{REPLAY-01} a "
         "\\texttt{REPLAY-03}; 153 pregões, dentro da amostra.")
tex = [
    "% Gerado por tcc2/scripts/metricas_replay.py; não editar à mão.",
    "\\begin{table}[htbp]",
    "\\centering",
    "\\caption{Retorno e risco das carteiras no Replay Contínuo, 06/04/2026 a "
    "12/11/2026 (153 pregões). Sharpe pela definição "
    "\\texttt{H2\\_SCIENTIFIC\\_SHARPE\\_DEFINITION\\_V1} ($r_f = 0$); Sortino com "
    "$r_f = 0$ e MAR $= 0$.}",
    "\\label{tab:replay-risco}",
    "\\small",
    "\\setlength{\\tabcolsep}{4pt}",
    "\\resizebox{\\textwidth}{!}{%",
    "\\begin{tabular}{lrrrrrrc}",
    "\\toprule",
    "Carteira & Retorno (\\%) & Ret. anual. (\\%) & Vol. anual. (\\%) & Sharpe & "
    "Sortino & MDD (\\%) & Pico--vale \\\\",
    "\\midrule",
]
for k, (_, _, _, nome_tex, _) in CARTEIRAS.items():
    m = M[k]
    tex.append(f"{nome_tex} & {tx(m['ret'])} & {tx(m['ret_a'])} & {tx(m['vol'])} & "
               f"{tx(m['sharpe'])} & {tx(m['sortino'])} & {tx(m['mdd'])} & "
               f"{dt(m['pico'])}--{dt(m['vale'])} \\\\")
    if k == "ma_v3":
        tex.append("\\midrule")
tex += [
    "\\bottomrule",
    "\\end{tabular}}",
    "\\par\\smallskip\\footnotesize " + FONTE,
    "\\end{table}",
    "",
    "\\begin{table}[htbp]",
    "\\centering",
    "\\caption{Operações, custos e caixa das carteiras no Replay Contínuo. Giro = "
    "volume negociado estimado (custo / 0{,}03\\%) dividido pelo patrimônio médio.}",
    "\\label{tab:replay-operacoes}",
    "\\small",
    "\\resizebox{\\textwidth}{!}{%",
    "\\begin{tabular}{lrrrrrr}",
    "\\toprule",
    "Carteira & Patrimônio final (R\\$) & Operações (C/V) & Custos (R\\$) & Giro & "
    "Caixa médio (\\%) & Caixa final (\\%) \\\\",
    "\\midrule",
]
for k, (_, _, _, nome_tex, _) in CARTEIRAS.items():
    m = M[k]
    tex.append(f"{nome_tex} & {tx(m['final'])} & {m['compras'] + m['vendas']} "
               f"({m['compras']}/{m['vendas']}) & {tx(m['custos'])} & {tx(m['giro'])} & "
               f"{tx(m['cx_medio'])} & {tx(m['cx_final'])} \\\\")
    if k == "ma_v3":
        tex.append("\\midrule")
tex += ["\\bottomrule", "\\end{tabular}}", "\\par\\smallskip\\footnotesize " + FONTE,
        "\\end{table}", ""]
escrever(TCC2 / "chapters/tabelas/metricas-replay.tex", "\n".join(tex))

# ---------------------------------------------------------------- figuras pgfplots
datas = [INICIO] + list(sessoes)
with open(TCC2 / "figures/replay-series.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["idx", "data"] + [f"eq_{k}" for k in CARTEIRAS] + [f"dd_{k}" for k in CARTEIRAS]
               + ["cx_ma_v1", "cx_ma_v2", "cx_ma_v3"])
    for i, d in enumerate(datas):
        w.writerow([i, d.date().isoformat()]
                   + [f"{M[k]['curva'].iloc[i] / 1000:.5f}" for k in CARTEIRAS]
                   + [f"{M[k]['dd'].iloc[i] * 100:.4f}" for k in CARTEIRAS]
                   + ["nan" if i == 0 else f"{M[k]['caixa'].iloc[i - 1]:.4f}"
                      for k in ("ma_v1", "ma_v2", "ma_v3")])

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
ticks = [(i, MESES[d.month - 1]) for i, d in enumerate(datas)
         if i == 0 or d.month != datas[i - 1].month]


def figura(nome, legenda, ylabel, prefixo, chaves, extra=""):
    linhas = [
        "% Gerado por tcc2/scripts/metricas_replay.py; requer \\usepackage{pgfplots}.",
        "\\begin{figure}[htbp]",
        "\\centering",
        "\\begin{tikzpicture}",
        "\\begin{axis}[",
        "  width=\\textwidth, height=7.5cm, xmin=0, xmax=153,",
        "  xtick={" + ",".join(str(i) for i, _ in ticks) + "},",
        "  xticklabels={" + ",".join(m for _, m in ticks) + "},",
        "  xlabel={Pregão (2026)}, ylabel={" + ylabel + "},",
        "  ymajorgrids, grid style={gray!20}, tick label style={font=\\footnotesize},",
        "  label style={font=\\small}, scaled y ticks=false,",
        "  yticklabel style={/pgf/number format/use comma, /pgf/number format/1000 sep={.}},",
        "  legend style={at={(0.5,-0.2)}, anchor=north, legend columns=3,",
        "    font=\\footnotesize, draw=none, /tikz/every even column/.append style="
        "{column sep=6pt}},",
        "  legend cell align=left," + extra,
        "]",
    ]
    for k in chaves:
        linhas.append(f"\\addplot[{CARTEIRAS[k][4]}] table[x=idx, y={prefixo}{k}, "
                      "col sep=comma] {figures/replay-series.csv};")
        linhas.append(f"\\addlegendentry{{{CARTEIRAS[k][3]}}}")
    linhas += ["\\end{axis}", "\\end{tikzpicture}", f"\\caption{{{legenda}}}",
               f"\\label{{fig:{nome}}}", "\\end{figure}", ""]
    escrever(TCC2 / f"figures/{nome}.tex", "\n".join(linhas))


todas = ["ma_v1", "ma_v2", "ma_v3", "bh", "sma", "boll", "ew", "mv"]
figura("replay-patrimonio",
       "Patrimônio de fechamento das carteiras no Replay Contínuo, de 02/04/2026 "
       "(R\\$~100 mil) a 12/11/2026. As referências são idênticas nas três campanhas.",
       "Patrimônio (R\\$ mil)", "eq_", todas)
figura("replay-drawdown",
       "Drawdown (queda em relação ao pico anterior) das carteiras no Replay Contínuo.",
       "Drawdown (\\%)", "dd_", todas)
figura("replay-caixa",
       "Caixa em percentual do patrimônio das três versões da carteira Multiagentes "
       "no Replay Contínuo.",
       "Caixa (\\% do patrimônio)", "cx_", ["ma_v1", "ma_v2", "ma_v3"], " ymin=0,")

for k, (_, _, nome, *_r) in CARTEIRAS.items():
    m = M[k]
    print(f"{nome:<24} final={m['final']:>10.2f} ret={m['ret']:>7.2f}% "
          f"vol={m['vol']:.2f}% sharpe={m['sharpe']:.3f} sortino={m['sortino']:.3f} "
          f"mdd={m['mdd']:.2f}% {dt(m['pico'])}->{dt(m['vale'])} giro={m['giro']:.2f}")
print("OK: todos os asserts passaram.")
