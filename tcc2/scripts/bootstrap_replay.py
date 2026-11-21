"""Bootstrap A (H2 v6) aplicado às comparações pareadas de Sharpe do Replay Contínuo.

Uso, na raiz do repositório (~3 min; 33 execuções de B = 5000):
    PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe tcc2/scripts/bootstrap_replay.py

Importa tcc2/scripts/metricas_replay.py (que refaz seus asserts e regrava, idênticos,
seus artefatos) para obter as curvas, e reutiliza sem alteração
src.experiments.h2_evaluation.bootstrap. Grava:
    tcc2/agent-reports/BOOTSTRAP_REPLAY.md
    tcc2/overleaf/chapters/tabelas/bootstrap-replay.tex
"""

import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metricas_replay as mr  # noqa: E402  (executa asserts e insere a raiz no sys.path)

from src.backtesting.metrics import periodic_returns  # noqa: E402
from src.experiments.h2_evaluation import B, COLUMNS, MEAN_BLOCK, SEED, bootstrap  # noqa: E402

ALPHA = 0.05
R = {k: periodic_returns(mr.M[k]["curva"]) for k in mr.CARTEIRAS}
assert all(r.index.equals(R["bh"].index) and len(r) == 153 for r in R.values())


def quadro(a, b):
    """Frame no formato de h2_evaluation: referência em buy_and_hold e a carteira
    avaliada repetida nas três colunas llm_*. Assim delta = Sharpe(a) - Sharpe(b)."""
    # ponytail: o replay tem uma execução por versão (R = 1), não três; repetir a série
    # torna a média das três igual a ela e a dispersão entre execuções nula.
    return pd.DataFrame({COLUMNS[0]: R[b], **{c: R[a] for c in COLUMNS[1:]}})


def holm(ps):
    ordem = sorted(range(len(ps)), key=ps.__getitem__)
    adj, acc = [0.0] * len(ps), 0.0
    for i, j in enumerate(ordem):
        acc = max(acc, min(1.0, (len(ps) - i) * ps[j]))
        adj[j] = acc
    return adj


assert holm([0.01, 0.04, 0.03]) == [0.03, 0.06, 0.06]

REFS = ["bh", "sma", "boll", "ew", "mv"]
PARES = [("H1", "sma", "ew")] + [(f"H2-{v}", f"ma_{v}", r)
                                 for v in ("v1", "v2", "v3") for r in REFS]
RES = []
for h, a, b in PARES:
    fw, rv = bootstrap(quadro(a, b)), bootstrap(quadro(b, a))  # rv: direção inversa
    d = mr.M[a]["sharpe"] - mr.M[b]["sharpe"]
    assert fw["status"] == rv["status"] == "ESTIMABLE" and fw["degenerate_draws"] == 0
    assert math.isclose(fw["delta"], d, abs_tol=1e-12) and math.isclose(rv["delta"], -d, abs_tol=1e-12)
    # p+ + p- = (2 + B + empates) / (B + 1): confere a leitura da direção inversa.
    assert abs(fw["p"] + rv["p"] - (B + 2) / (B + 1)) < 3 / (B + 1), (h, a, b)
    RES.append({"h": h, "a": a, "b": b, "d": fw["delta"], "L": fw["lower95"],
                "U": -rv["lower95"], "p": fw["p"], "p_inv": rv["p"],
                "sup": fw["superiority"], "inf": rv["superiority"],
                "idx": fw["indices_sha256"], "roots": fw["roots_sha256"]})
    print(f"{h:<6} {a:>6} vs {b:<5} d={fw['delta']:+.3f} L95={fw['lower95']:+.3f} "
          f"U95={-rv['lower95']:+.3f} p+={fw['p']:.4f} p-={rv['p']:.4f}")

# Reprodutibilidade: mesma semente -> mesmos índices, raízes e resultado.
assert bootstrap(quadro("sma", "ew")) == bootstrap(quadro("sma", "ew"))
# Pareamento: as 16 comparações usam a mesma sequência de índices (n = 153, mesma semente).
assert len({x["idx"] for x in RES}) == 1
for v in ("v1", "v2", "v3"):
    fam = [x for x in RES if x["h"] == f"H2-{v}"]
    for x, ph in zip(fam, holm([x["p"] for x in fam])):
        x["holm"] = ph
RES[0]["holm"] = RES[0]["p"]  # H1: comparação única
# Padrão observado em que o texto abaixo se apoia; se os dados mudarem, o texto também.
SUP = [x for x in RES if x["sup"]]
assert [(x["h"], x["b"]) for x in SUP] == [("H2-v3", "sma")] and SUP[0]["holm"] >= ALPHA
assert not any(x["inf"] for x in RES)
V3S = SUP[0]


# ---------------------------------------------------------------- saída
def nome(k, latex=False):
    return mr.CARTEIRAS[k][3 if latex else 2]


def pv(p, latex=False):
    s = "< 0,001" if p < 0.001 else mr.br(p, 3)
    return ("$<$ 0{,}001" if p < 0.001 else s.replace(",", "{,}")) if latex else s


def decisao(x):
    if not x["sup"]:
        return "Não rejeita H0"
    if x["h"] in ("H2-v2", "H2-v3"):  # Cap. 5: versões exploratórias não recebem decisão inferencial
        return "Critério numérico atingido, só descritivo" + ("" if x["holm"] < ALPHA else "; não após Holm")
    return "Rejeita H0 (superioridade)" + ("" if x["holm"] < ALPHA else "; não após Holm")


ROTULO = {"H1": "H1", "H2-v1": "H2 · v1 (pré-especificada)",
          "H2-v2": "H2 · v2 (exploratória)", "H2-v3": "H2 · v3 (exploratória)"}
inferiores = [x for x in RES if x["inf"]]

md = [
    "# Inferência Bootstrap A no Replay Contínuo Abril–Novembro 2026",
    "",
    "Gerado por `tcc2/scripts/bootstrap_replay.py`, que reutiliza sem alteração "
    "`bootstrap(frame)` de `src/experiments/h2_evaluation.py` sobre os 153 retornos "
    "diários calculados por `tcc2/scripts/metricas_replay.py` (ver "
    "`METRICAS_REPLAY.md`). Vínculo: DP-37 / `REPLAY-01..03`, capítulo de resultados.",
    "",
    "> **Ressalva.** O Bootstrap A foi especificado para o protocolo H2 v6 (PETR4, "
    "fase Final, três execuções LLM contra Buy & Hold). Aqui o mesmo procedimento é "
    "reaplicado ao replay, que não é o teste confirmatório congelado: uma única "
    "trajetória de 153 pregões, cinco ativos, reconstrução histórica posterior ao "
    "período e uma execução por versão (DP-09, DP-31, DP-37).",
    "",
    "## 1. O que a função faz",
    "",
    "- **Estatística.** Δ̂ = média do Sharpe das colunas `llm_1..3` − Sharpe da "
    "coluna `buy_and_hold`, com a definição congelada "
    f"`{mr.SCIENTIFIC_SHARPE_DEFINITION}` (`sharpe_components`, rf = 0, √252).",
    f"- **Reamostragem.** *Stationary bootstrap* (Politis–Romano) pareado: B = {B}, "
    f"NumPy PCG64 com semente {SEED} reiniciada a cada chamada, bloco médio "
    f"{MEAN_BLOCK} (reinício com probabilidade 0,1), índices circulares. A mesma "
    "sequência de índices reamostra todas as colunas do quadro, preservando a "
    "correlação diária entre as carteiras comparadas.",
    "- **Centragem e hipótese nula.** Raízes eᵦ = Δᵦ* − Δ̂ (bootstrap *basic* "
    "centrado). Teste unilateral de superioridade, H0: Δ ≤ 0 contra H1: Δ > 0.",
    "- **p-valor e limite.** p₊ = (1 + #{eᵦ ≥ Δ̂}) / (B + 1); limite inferior "
    "unilateral de 95% L₉₅ = Δ̂ − e₍₄₇₅₁₎ (posto 4751, sem interpolação). A função "
    "verifica que p₊ < 0,05 ⇔ L₉₅ > 0.",
    "- **Regra de decisão.** Superioridade (rejeição de H0) somente se a estatística "
    "for estimável, Δ̂ > 0, p₊ < 0,05 e L₉₅ > 0. Série ou *draw* degenerado "
    "(volatilidade nula) torna o resultado inconclusivo, sem refazer *draws*.",
    "",
    "## 2. Montagem do quadro (adaptação)",
    "",
    "A função exige exatamente as colunas `buy_and_hold, llm_1, llm_2, llm_3`. Para "
    "cada comparação A vs B, a referência B ocupa `buy_and_hold` e a carteira A é "
    "repetida nas três colunas `llm_*`; logo Δ̂ = Sharpe(A) − Sharpe(B). A "
    "repetição é necessária porque o replay tem uma execução por versão (R = 1): a "
    "variabilidade entre chamadas do modelo, coberta parcialmente pelo protocolo com "
    "R = 3, não é representada. Nenhum código em `src/` foi alterado.",
    "",
    "Como complemento **exploratório** (fora da regra congelada), a função é chamada "
    "também com os papéis trocados (B contra A). Isso dá p₋, o p-valor unilateral de "
    "inferioridade (H0: Δ ≥ 0), e o limite superior U₉₅ = −L₉₅(B vs A) = Δ̂ − e₍₂₅₀₎. "
    "[L₉₅; U₉₅] é um intervalo bilateral de 90%.",
    "",
    "## 3. Resultados",
    "",
    "Δ = diferença de Sharpe anualizado (A − B), 153 retornos diários pareados. "
    "Holm: ajuste de Holm sobre p₊ dentro de cada família de cinco referências.",
    "",
    "| Hipótese | A | B | Δ Sharpe | L₉₅ | U₉₅ | p₊ | p₊ Holm | p₋ (explor.) | "
    "Decisão (α = 0,05) |",
    "|---|---|---|---:|---:|---:|---:|---:|---:|---|",
]
for x in RES:
    md.append(f"| {ROTULO[x['h']]} | {nome(x['a'])} | {nome(x['b'])} | {mr.br(x['d'])} | "
              f"{mr.br(x['L'])} | {mr.br(x['U'])} | {pv(x['p'])} | {pv(x['holm'])} | "
              f"{pv(x['p_inv'])} | {decisao(x)} |")
inf_txt = ("; ".join(f"{nome(x['a'])} vs {nome(x['b'])} (p₋ = {pv(x['p_inv'])})"
                     for x in inferiores) or "nenhuma")
md += [
    "",
    f"Todas as {len(RES)} comparações usaram a mesma sequência de índices "
    f"(SHA-256 `{RES[0]['idx'][:16]}…`), nenhuma teve *draw* degenerado.",
    "",
    "## 4. Interpretação",
    "",
    f"- **H1 (SMA 50/200 vs Equal Weight 63d).** Δ̂ = {mr.br(RES[0]['d'])}: o "
    "Sharpe do SMA foi menor, não maior. A regra de superioridade não se aplica "
    f"(Δ̂ < 0, p₊ = {pv(RES[0]['p'])}); H0 não é rejeitada. O intervalo de 90% "
    f"[{mr.br(RES[0]['L'])}; {mr.br(RES[0]['U'])}] contém zero, portanto também não "
    "há evidência de inferioridade.",
    "- **H2 · v1 (execução pré-especificada).** Única versão cujas regras foram "
    "fixadas antes de observar o período; é a leitura que conta para H2. Nenhuma das "
    "cinco comparações atinge superioridade; H0 não é rejeitada, com ou sem Holm.",
    "- **H2 · v2 e v3 (iterações exploratórias).** Desenhadas depois de observar as "
    "auditorias da v1 (e da v2) no mesmo período. Seus p-valores são otimistas por "
    "construção (seleção dentro da amostra, *garden of forking paths*). A v2 não "
    "atinge superioridade em nenhuma comparação. A v3 atinge a regra bruta em uma "
    f"única comparação, contra o SMA 50/200 (Δ̂ = {mr.br(V3S['d'])}, "
    f"p₊ = {pv(V3S['p'])}, L₉₅ = {mr.br(V3S['L'])}), justamente a referência de pior "
    "Sharpe no período; o resultado não sobrevive ao ajuste de Holm na família da v3 "
    f"(p₊ ajustado = {pv(V3S['holm'])}) e, pela origem exploratória da v3, não "
    "constitui evidência confirmatória. Contra Buy & Hold, Equal Weight, Mínima "
    "Variância e Bollinger, a v3 nem atinge o critério numérico. Como v2 e v3 não "
    "recebem decisão inferencial (Cap. 5), nenhum desses valores rejeita H0.",
    f"- **Inferioridade (exploratório, p₋ < 0,05):** {inf_txt}.",
    "- **Multiplicidade.** A regra primária congelada é unilateral, comparação a "
    "comparação, a α = 0,05, e não foi trocada; Holm é mostrado apenas como leitura "
    "complementar. Na v1 (família pré-especificada) nenhuma p₊ bruta fica abaixo de "
    "0,05, logo o ajuste não muda nada; o único efeito do Holm é retirar o critério "
    "bruto atingido pela v3 contra o SMA. Observe-se que \"superior a todas as referências\" é "
    "um teste de interseção–união, que dispensa ajuste e não é atendido por nenhuma "
    "versão; \"superior a pelo menos uma\" é o caso que exige ajuste.",
    "- **Conclusão.** No replay, os dados não permitem rejeitar H0 para H1 nem para "
    "H2 na execução pré-especificada (v1). O único critério bruto atingido (v3 vs SMA "
    "50/200) vem de uma iteração exploratória, é só descritivo e não resiste ao "
    "controle de multiplicidade. "
    "Não rejeitar H0 não prova igualdade: os intervalos de 90% têm amplitude de "
    f"{mr.br(min(x['U'] - x['L'] for x in RES), 1)} a "
    f"{mr.br(max(x['U'] - x['L'] for x in RES), 1)} pontos de Sharpe, e diferenças "
    "economicamente grandes não se distinguem de ruído. Sortino, máximo drawdown e "
    "giro (`METRICAS_REPLAY.md`) permanecem descritivos; a função não faz inferência "
    "sobre eles.",
    "",
    "## 5. Limitações",
    "",
    "- **Amostra única.** 153 retornos diários de uma única trajetória de mercado e "
    "cinco ativos; o bootstrap trata a incerteza amostral dessa série, não a de "
    "outros regimes ou períodos. A aproximação supõe estacionariedade e dependência "
    "fraca; o bloco 10 não tem optimalidade demonstrada; o *basic* não studentizado "
    "não é teste exato.",
    "- **Possível contaminação.** O modelo foi executado depois do fechamento do "
    "período e pode conhecer o desfecho (motivo da DP-31; reaberta de forma limitada "
    "e exploratória pela DP-37). Mesmo um resultado favorável não seria evidência "
    "prospectiva.",
    "- **Iterações dentro da amostra.** v2 e v3 foram projetadas a partir das "
    "auditorias da mesma janela; seus resultados não são independentes da v1 nem "
    "dos dados usados para avaliá-las.",
    "- **R = 1.** Uma execução por versão; a variabilidade entre chamadas do modelo "
    "não entra no intervalo.",
    "- **rf = 0.** Sharpe sem taxa livre de risco, coerente com o caixa não "
    "remunerado do replay; com rf > 0 todos os índices cairiam.",
    "",
    "## 6. Verificações executadas (asserts do script)",
    "",
    "- Asserts de `metricas_replay.py` (dados, referências idênticas, valores do "
    "documento mestre) passam na importação.",
    "- Δ̂ da função igual à diferença dos Sharpe de `metricas_replay.py`; estado "
    "`ESTIMABLE` e zero *draws* degenerados em todas as execuções.",
    "- Reprodutibilidade: duas chamadas com a mesma semente dão resultados idênticos "
    "(incluindo os hashes de índices e raízes); todas as execuções compartilham os "
    "mesmos índices; p₊ + p₋ = (B + 2)/(B + 1) a menos de empates; Holm conferido "
    "num exemplo manual.",
    "",
]
mr.escrever(mr.TCC2 / "agent-reports/BOOTSTRAP_REPLAY.md", "\n".join(md))

ROT_TEX = {"H1": "H1", "H2-v1": "H2 (v1)", "H2-v2": "H2 (v2)", "H2-v3": "H2 (v3)"}
tex = [
    "% Gerado por tcc2/scripts/bootstrap_replay.py; não editar à mão.",
    "\\begin{table}[H]",
    "\\centering",
    "\\caption{Comparações pareadas de Sharpe no Replay Contínuo (153 pregões) pelo "
    f"\\textit{{bootstrap}} A: estacionário, \\textit{{basic}} centrado, $B={B}$, "
    f"semente {SEED}, bloco médio {MEAN_BLOCK}. $\\Delta$ = Sharpe(A) $-$ Sharpe(B), "
    "$r_f = 0$. $p_+$ e $L_{95}$: teste unilateral de superioridade (regra congelada); "
    "$U_{95}$ e $p_-$: direção inversa, exploratória. Holm dentro de cada família de "
    "cinco referências.}",
    "\\label{tab:replay-bootstrap}",
    "\\setlength{\\tabcolsep}{4pt}",
    "\\resizebox{\\textwidth}{!}{%",
    "\\begin{tabular}{llrrrrrrc}",
    "\\toprule",
    "Hipótese & A vs B & $\\Delta$ & $L_{95}$ & $U_{95}$ & $p_+$ & $p_+$ Holm & $p_-$ & "
    "Critério? \\\\",
    "\\midrule",
]
for i, x in enumerate(RES):
    a = nome(x["a"], True).replace("Multiagentes ", "MA ")
    tex.append(f"{ROT_TEX[x['h']]} & {a} vs {nome(x['b'], True)} & {mr.tx(x['d'])} & "
               f"{mr.tx(x['L'])} & {mr.tx(x['U'])} & {pv(x['p'], True)} & "
               f"{pv(x['holm'], True)} & {pv(x['p_inv'], True)} & "
               f"{('sim$^{*}$' if x['h'] in ('H2-v2', 'H2-v3') else 'sim') if x['sup'] else 'não'} \\\\")
    if i in (0, 5, 10):
        tex.append("\\midrule")
tex += [
    "\\bottomrule",
    "\\end{tabular}}",
    "\\par\\smallskip\\footnotesize v1: execução pré-especificada; v2 e v3: iterações "
    "exploratórias desenhadas após observar o mesmo período (p-valores otimistas). "
    "Critério: $\\hat{\\Delta} > 0$, $p_+ < 0{,}05$ e $L_{95} > 0$; só rejeita $H_0$ em H1 e "
    "H2 (v1). $^{*}$Apenas descritivo: v2 e v3 não recebem decisão inferencial "
    "(Seção~\\ref{sec:met-inferencia}); não se mantém após Holm. "
    "Fonte: \\texttt{daily.csv} das campanhas \\texttt{REPLAY-01} a \\texttt{REPLAY-03}; "
    "\\texttt{src/experiments/h2\\_evaluation.py}.",
    "\\end{table}",
    "",
]
mr.escrever(mr.OVERLEAF / "chapters/tabelas/bootstrap-replay.tex", "\n".join(tex))
print("OK: bootstrap reprodutível e todos os asserts passaram.")
