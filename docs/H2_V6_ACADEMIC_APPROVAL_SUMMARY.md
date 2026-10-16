# H2 v6 - Resumo para aprovação acadêmica do amendment de avaliação

Objeto: decisões SF-B1..SF-B6 e política de custos, na branch `#1-Update`.
Situação: confirmação formal pendente; nenhum campo abaixo constitui aprovação previamente recebida. A versão PDF deste resumo contém duas páginas.

**Vinculação documental (SHA256 dos bytes, não do texto reformatado):**

Proposta: `docs/H2_V6_EVALUATION_AMENDMENT_PROPOSAL.md`
`23d6f9464ffbcbbdacc44ecd0d59f39b2cdaa3d5e8b5b873faf73f0653607244`

Deliberação: `docs/H2_V6_EVALUATION_AMENDMENT_DELIBERATION.md`
`fe01092079e8bb9df60b97151631b5c9bff6fd36a249f18e8ea8ea55b7495dbb`

**SF-B1 - Hipóteses e alcance.** Seja Sⱼ o Sharpe líquido diário anualizado do run j e S₀ o do Buy & Hold. O estimador é Δ̂ = (S₁ + S₂ + S₃)/3 - S₀; as hipóteses são H0₂: Δ ≤ 0 e HA₂: Δ > 0. Haverá um único contraste confirmatório no Final Test, condicionado às três trajetórias LLM observadas. A H1 multiativo permanece separada. Validation será exclusivamente descritiva, sem ajuste ou seleção de parâmetros.

**SF-B2 - Replicações.** Exatamente três runs LLM em Validation e três novos runs no Final Test, com instâncias, traces e identidades próprios, sem cache científico entre runs. Dados, tratamento, parâmetros e custos serão iguais dentro de cada fase. Independência das chamadas não implica mercados independentes nem independência interna demonstrada do provedor. Um run incompleto exige recuperação exata ou interrupção por integridade, sem substituição por desempenho.

**SF-B3 - Agregação.** Média aritmética dos três Sharpes individuais, sem seleção do melhor run ou uso do Sharpe da curva média. Publicar todos os runs, suas diferenças para B&H, média, mínimo, máximo e desvio-padrão entre runs (ddof=1), além de curvas, retornos, trades e custos. Esse desvio é descritivo, não erro-padrão confirmatório.

**SF-B4 - Bootstrap A.** A deliberação seleciona A, ainda sujeito à confirmação: stationary bootstrap temporal pareado, basic centrado, B=5000, α=0,05, NumPy PCG64 com seed estatística 20261008 e bloco médio 10 (reinício 0,1). A mesma sequência de índices reamostra as quatro séries; eᵦ = Δᵦ* - Δ̂. Usar p₊ = (1 + #{eᵦ ≥ Δ̂})/5001 e L₉₅ = Δ̂ - e₍₄₇₅₁₎, sem interpolação. Superioridade exige estimabilidade, Δ̂ > 0, p₊ < 0,05 e L₉₅ > 0. Série ou draw degenerado, ou erros todos iguais, implica conclusão inconclusiva e p/limite ausentes, sem excluir ou refazer draws. A alternativa B não foi selecionada.

**SF-B5 - Benchmarks.** B&H é primário, com entrada inicial e manutenção. SMA Regime 50/200 entra quando SMA50 > SMA200 e sai na igualdade; Bollinger Estado 20/2 usa desvio ddof=1, entrada close ≤ banda inferior e saída close ≥ superior, mantendo posição dentro das bandas e HOLD quando colapsadas. Ambos começam em caixa e emitem intenção apenas quando muda o alvo. Executar cada benchmark determinístico uma vez por fase/cenário; preservar os adapters históricos de cruzamento.

**SF-B6 - Métricas.** Sharpe científico v1: √252 × média(r)/sd(r, ddof=1), rf=0, com retornos líquidos diários, dias em caixa e settlement. Sortino: MAR diário=0/rf anual=0, escore técnico com flags e valor econômico ausente nas degenerações. Turnover: nocional absoluto efetivamente executado/capital inicial. Retorno, CAGR, drawdown, duração do drawdown, ordens e custos são descritivos; não geram novos contrastes confirmatórios.

<!-- PAGE_BREAK -->

**Custos e cenário não estimável.** Capital R$100.000, long-only, quantidade fracionária, rendimento de caixa zero; corretagem fixa=0, spread primário=5 bps e taxa=0,00032. A sensibilidade {0,5,10,20} bps é descritiva. O baseline 5 reutiliza os artifacts primários. Nos demais cenários LLM, somente replay exato, sem rede, com estado, quantidades e custos recalculados causalmente. Divergência, falta ou sobra de requests/respostas produz `COST_SENSITIVITY_NOT_ESTIMABLE — EXACT_REPLAY_INVALID`, motivo e identidade afetada; métricas completas ficam null/N/A, nunca zero. Resumo de cenário exige três replays completos; não agregar subconjunto. Não substituir por trades fixados ou novas chamadas. Registrar todas as disposições; indisponibilidade descritiva não invalida, por si só, baseline íntegro.

**Janelas e integridade.** Validation: 02/09/2024 a 29/08/2025, última decisão 28/08/2025; Final Test: 01/09/2025 a 31/08/2026, última decisão 28/08/2026. A última sessão é settlement, sem nova decisão ou venda terminal artificial. Warmup inclusivo mínimo=504 (503 anteriores + primeira sessão). Execução close(t) → open(t+1), sem ordens entre fases. Release para Final depende de identidade, integridade e completude, nunca de retorno positivo, Sharpe, p-valor ou superioridade.

**Limitações reconhecidas.** A inferência temporal não cobre a população de futuras realizações Gemini; R=3 oferece descrição restrita da variabilidade entre chamadas. As fases contêm 247/249 retornos, não três mercados independentes. A depende de estacionariedade aproximada, dependência fraca e regularidade do Sharpe; caudas, regimes e baixa volatilidade comprometem a aproximação. Bloco 10 não tem optimalidade demonstrada. O basic não studentizado não é teste nulo exato nem o método completo de Ledoit e Wolf. Não há estudo de tamanho, poder ou cobertura; checks computacionais não o substituem. Anualização por √252 é convenção protocolar. Não rejeição não prova igualdade; resultados negativos e inconclusivos serão publicados.

**Objeto e limites da aprovação.** Autor e coautor devem manifestar-se sobre as seis decisões, A, custos/N/A e limitações. O orientador deve registrar ciência e concordância com o mesmo conjunto, especialmente o alcance condicional da inferência. Aprovar ratifica a especificação identificada pelos hashes acima; não certifica desempenho, validade estatística irrestrita ou prontidão live. Preserva tratamento v6 e CAL-B4 consumida, `CAL_B4_PASS — SANITY CHECK ONLY`. Não autoriza System Freeze, Gemini, Validation, Final Test, alteração de tratamento ou preenchimento de manifestações de terceiros. A revisão de prontidão identifica bloqueios técnicos adicionais, a sanar antes do freeze; cada fase real exigirá autorização externa específica.

**Manifestação individual - Autor**

Nome: ____________________  Manifestação (aprovação, ressalvas ou rejeição): ____________________
Itens/ressalvas e referência aos hashes: ___________________________________________________
Data: ____________________  Assinatura ou referência ao registro eletrônico: ____________________

**Manifestação individual - Coautor**

Nome: ____________________  Manifestação (aprovação, ressalvas ou rejeição): ____________________
Itens/ressalvas e referência aos hashes: ___________________________________________________
Data: ____________________  Assinatura ou referência ao registro eletrônico: ____________________

**Manifestação individual - Orientador**

Nome: ____________________  Ciência/concordância, ressalvas ou discordância: ____________________
Itens/ressalvas e referência aos hashes: ___________________________________________________
Data: ____________________  Assinatura ou referência ao registro eletrônico: ____________________
