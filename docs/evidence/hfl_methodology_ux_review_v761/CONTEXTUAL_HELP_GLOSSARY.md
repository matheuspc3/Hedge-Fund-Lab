# Ajuda contextual e glossário

## 1. Padrão de interação do "?"

| Requisito | Especificação |
|---|---|
| Elemento | `<button type="button" class="help" aria-expanded="false" aria-controls="help-<termo>">` com o texto visível "?" e nome acessível "Ajuda: <termo>" |
| Abrir/fechar | clique, toque, Enter ou Espaço; Esc fecha e devolve o foco ao botão |
| Conteúdo | painel ancorado (popover) **não modal**, que permanece aberto até ser fechado; nunca some quando o mouse sai |
| Hover | só como pré-visualização adicional; nunca o único meio |
| Leitores de tela | o painel é região com `id`; o botão referencia por `aria-controls`; o termo do campo associado usa `aria-describedby` para o resumo curto |
| Alvo de toque | no mínimo 24 × 24 px (WCAG 2.2, 2.5.8); recomendado 44 × 44 em móvel |
| Estrutura do painel | 1) explicação curta; 2) "Saiba mais" expansível (técnica); 3) **Cuidado** (ressalva); 4) "Como o laboratório calcula" (referência ao código, para o perfil pesquisador); 5) link para o glossário |
| Fonte única | um arquivo de dados de glossário consumido por todas as páginas; o texto não é duplicado em cada HTML |
| Ajuda global | botão "?" no shell abre Ajuda › Como funciona / Glossário / FAQ |

Exemplo de painel (RSI):

```text
RSI — Índice de Força Relativa                                   [fechar ×]
Mede, de 0 a 100, a força das altas recentes em relação às quedas.
▸ Saiba mais
⚠ Cuidado: RSI acima de 70 é chamado de "sobrecompra", mas isso não garante queda.
  Como o laboratório calcula: média de Wilder, 14 períodos (src/indicators/rsi.py).
Glossário completo →
```

## 2. Glossário

Cada entrada traz: **nome visível**, **curta**, **técnica**, **onde aparece**,
**cuidado** e **referência no código** (quando o conceito é específico do
laboratório).

### Indicadores e estatística

**RSI**
- Nome visível: RSI (Índice de Força Relativa).
- Curta: mede, de 0 a 100, a força das altas recentes em relação às quedas.
- Técnica: 100 − 100/(1 + RS), com RS = média de ganhos ÷ média de perdas, suavizadas pela média de Wilder em 14 períodos.
- Onde: painel do Radar, detalhe do comitê, indicadores do ativo, métricas citadas pelo Gestor.
- Cuidado: valores acima de 70 ou abaixo de 30 são convenções de leitura; não garantem reversão nem indicam momento de compra ou venda.
- Código: `src/indicators/rsi.py` (`rsi(series, period=14)`).

**MACD**
- Nome visível: MACD.
- Curta: compara médias móveis rápida e lenta para indicar a direção e a força recente da tendência.
- Técnica: EMA(12) − EMA(26); linha de sinal = EMA(9) do MACD; histograma = MACD − sinal. O Radar usa as razões `macd_ratio` e `macd_signal_ratio` (divididas pelo preço).
- Onde: Radar, comitê, indicadores.
- Cuidado: indicador defasado, que confirma movimentos passados; cruzamentos não preveem preço.
- Código: `src/indicators/macd.py` (12, 26, 9).

**Bandas de Bollinger**
- Nome visível: Bandas de Bollinger.
- Curta: faixa ao redor da média de 20 dias que se alarga quando os preços variam mais.
- Técnica: média móvel de 20 ± 2 desvios-padrão. O Radar registra a distância do fechamento às bandas (`bb_upper_gap`, `bb_lower_gap`) e a largura (`bb_width`).
- Onde: Radar, comitê, indicadores.
- Cuidado: tocar a banda não é sinal infalível; "rompimento" só existe se o fechamento ficar fora da banda (`bb_upper_gap > 0`).
- Código: `src/indicators/bollinger.py` (20, 2,0).

**Volatilidade**
- Nome visível: Volatilidade (anualizada).
- Curta: quanto os retornos diários costumam oscilar, expressa em base anual.
- Técnica: no Radar, desvio-padrão amostral dos últimos 21 retornos diários × √252 (`asset_volatility_21`); na carteira (V5), calculada com 60 retornos.
- Onde: Radar (Risk), Carteira (risco global), glossário de limites.
- Cuidado: mede variação passada, não risco futuro garantido; 21 dias é uma janela curta e sensível a eventos isolados.
- Código: `scripts/multiasset_radar.py` (cálculo de `asset_volatility_21`); `POLICY["risk_window"] = 60` em `scripts/multiasset_portfolio.py`.

**Drawdown**
- Nome visível: Drawdown (queda desde o pico).
- Curta: quanto o patrimônio caiu desde o maior valor anterior.
- Técnica: (patrimônio_t − pico até t) ÷ pico até t; o drawdown máximo é o menor valor dessa série (fração negativa).
- Onde: carteiras prospectivas, backtests, métricas futuras.
- Cuidado: depende do período observado; um drawdown pequeno no passado não limita perdas futuras.
- Código: `src/backtesting/metrics.py` (`drawdown_series`, `max_drawdown`).

**Sharpe**
- Nome visível: Índice de Sharpe.
- Curta: retorno acima da taxa livre de risco por unidade de volatilidade.
- Técnica: média dos retornos excedentes ÷ desvio-padrão × √252; a taxa anual vira diária por rf/252.
- Onde: backtests legados, H2, métricas futuras.
- Cuidado: instável em amostras curtas e indefinido sem variação. O código H2 retorna 0,0 por convenção quando a volatilidade é praticamente nula; o protocolo V7.6 define esse caso como **indefinido**. A interface deve mostrar "indefinido", nunca 0.
- Código: `src/backtesting/metrics.py` (`sharpe_ratio`).

**Correlação**
- Nome visível: Correlação.
- Curta: o quanto dois ativos costumam subir e cair juntos (de −1 a 1).
- Técnica: correlação de Pearson entre retornos diários alinhados (60 retornos na carteira V5); o Gestor V2 só pode citar pares presentes em `verifiable_metrics`.
- Onde: Carteira (risco), métricas citadas.
- Cuidado: associação estatística, não causalidade; muda com o tempo; não existe "correlação setorial" no laboratório (não há dados de setor).
- Código: `scripts/multiasset_manager.py` (risco com `POLICY["risk_window"]`).

### Agentes e decisão

**Consenso**
- Nome visível: Consenso do comitê.
- Curta: resultado da votação de 5 analistas sobre COMPRA, MANTER ou VENDA.
- Técnica: vence o sinal com pelo menos 60% dos votos válidos; abaixo disso não há consenso.
- Onde: Radar, detalhe do comitê.
- Cuidado: unanimidade entre instâncias do mesmo modelo não é independência de opiniões; consenso não é ordem.
- Código: `scripts/multiasset_radar.py` (`consensus_threshold=0.6`).

**Confiança técnica**
- Nome visível: Confiança técnica (qualitativa).
- Curta: número de 0 a 1 que resume quão firmes foram os votos vencedores.
- Técnica: soma das confianças dos votos vencedores ÷ número total de analistas (ex.: WEGE3 0,476 = (0,55 + 0,60 + 0,58 + 0,65) ÷ 5).
- Onde: Radar, comitê, métricas citadas.
- Cuidado: **não** é probabilidade de lucro, nem retorno esperado, nem tamanho de posição.
- Código: agregação do comitê em `scripts/multiasset_radar.py`.

**Recomendação final**
- Nome visível: Recomendação final do parecer.
- Curta: sinal do comitê depois do parecer de risco.
- Técnica: igual ao sinal técnico, salvo veto (vira MANTER).
- Onde: Radar, Gestor Global.
- Cuidado: no motor da carteira, **só COMPRA permite compra**; MANTER e VENDA impedem compras (`ERRATUM-HFL-2026-002`).
- Código: `scripts/multiasset_manager.py:399`.

**Veto de Risk**
- Nome visível: Veto de risco.
- Curta: bloqueio imposto pelas regras de risco a um ativo.
- Técnica: o ativo recebe `VETADO` quando a volatilidade anualizada de 21 dias passa de 50% (regra determinística, sem LLM) ou quando o Risk consultivo veta. Com veto, a carteira não pode operar o ativo nem aumentar seu peso.
- Onde: Radar, comitê, Gestor Global, limites.
- Cuidado: na política atual o veto também impede **reduzir ou vender** uma posição existente (decisão pendente, [RISK_VETO_POLICY_DECISION.md](RISK_VETO_POLICY_DECISION.md)).
- Código: `scripts/multiasset_radar.py` (regra 0,5); `scripts/multiasset_manager.py:397`; validador V2 (I13).

### Carteira

**Caixa disponível**
- Nome visível: Caixa disponível.
- Curta: dinheiro hipotético que pode ser usado agora.
- Técnica: caixa liquidado menos reservas.
- Onde: Carteira, Gestor, operação paper.
- Cuidado: valores de vendas ainda não liquidadas (recebíveis) **não** entram.
- Código: estado V5 (`cash.available`, `cash.settled`) em `scripts/multiasset_portfolio.py`.

**Caixa reservado**
- Nome visível: Caixa reservado.
- Curta: parte do caixa presa a ordens ainda não concluídas.
- Técnica: preço-limite × quantidade + custo estimado de cada ordem pendente.
- Onde: Carteira, operação paper.
- Cuidado: volta a ser disponível se a ordem não for preenchida.
- Código: estado V5 (`cash.reserved`).

**Recebível D+2**
- Nome visível: Recebível (D+2).
- Curta: dinheiro de uma venda que só cai na conta dois pregões depois.
- Técnica: liquidação de ações à vista na B3 em D+2 pelo calendário oficial; compras que dependem dele precisam declarar a dependência e só são executadas após a liquidação.
- Onde: Carteira, Gestor (operações condicionadas).
- Cuidado: não é caixa disponível; usá-lo antes da liquidação é rejeitado.
- Código: `POLICY["settlement_rule"] = "B3_CASH_EQUITIES_D+2_OC041_2026_CONFIRMED"`.

**Peso-alvo**
- Nome visível: Peso-alvo.
- Curta: fração do patrimônio que a proposta quer em cada ativo.
- Técnica: pesos de todos os ativos + caixa somam exatamente 1; máximo de 40% por ativo e 85% em ações.
- Onde: Gestor Global, propostas.
- Cuidado: peso-alvo é intenção da proposta, não posição comprada.
- Código: validador V2 (I7, I8); `POLICY["max_concentration"]`, `["max_exposure"]`.

### Registros, custo e validação

**Verificar requisitos (preflight)**
- Nome visível: Verificar requisitos.
- Curta: checagem gratuita feita antes de qualquer chamada paga.
- Técnica: confere validade do contexto, origem dos pareceres, tamanho da entrada, orçamento e se já existe tentativa; gera o token de confirmação.
- Onde: Radar, Gestor, Decisão do dia.
- Cuidado: passar na verificação não autoriza a chamada; a autorização é um passo separado.
- Código: `preflight()` em `scripts/run_global_pm_v2.py`, `scripts/radar_runs.py`.

**Fotografia (snapshot)**
- Nome visível: Fotografia da carteira e dos pareceres.
- Curta: registro congelado de tudo o que a IA vai ver num instante.
- Técnica: snapshot da carteira + pareceres + históricos, selado por hash no contexto, válido por 24 h.
- Onde: Gestor, Radar (inputs).
- Cuidado: mudar qualquer dado exige uma fotografia nova; a antiga nunca é editada.
- Código: `make_snapshot`, `freeze` (`scripts/multiasset_global_pm_v2.py`).

**Hash SHA-256**
- Nome visível: Impressão digital (SHA-256).
- Curta: código que muda completamente se um único byte do arquivo mudar.
- Técnica: função de hash criptográfica de 256 bits usada para provar integridade.
- Onde: Auditoria, Evidências, selos de tratamento.
- Cuidado: prova que o conteúdo não mudou, não que está correto.
- Código: `hashlib.sha256` nos verificadores.

**Registro de tentativa (claim)**
- Nome visível: Registro de tentativa.
- Curta: anotação gravada antes de uma chamada paga para impedir que ela se repita sem querer.
- Técnica: `claim.json` vinculado à autorização e ao contexto; o preflight recusa um registro já reivindicado.
- Onde: Auditoria, Gestor, Radar.
- Cuidado: existir registro não significa que a chamada teve sucesso.
- Código: `run()` em `scripts/run_global_pm_v2.py`.

**Diário de chamadas (journal)**
- Nome visível: Diário de chamadas.
- Curta: cópia durável do que o provedor respondeu.
- Técnica: `provider_journal.jsonl` e `calls.sqlite`, privados, com o envelope bruto e o hash de cada chamada.
- Onde: Auditoria (estado e integridade; conteúdo privado não é exibido).
- Cuidado: o conteúdo bruto é privado e não deve ser publicado.

**Recuperar sem nova chamada (replay offline)**
- Nome visível: Recuperar sem nova chamada.
- Curta: refaz a validação a partir do diário, sem chamar a IA de novo.
- Técnica: `run(..., replay=True)` relê o journal e reconstrói o resultado; nenhum custo.
- Onde: Diagnóstico, Gestor, Radar.
- Cuidado: não gera resposta nova; se o diário não tem resposta, não há o que recuperar.

**Inferência paga**
- Nome visível: Inferência paga.
- Curta: consulta a um modelo de IA externo que pode gerar cobrança.
- Técnica: chamada ao Gemini com reserva conservadora de orçamento; custo real conhecido só pela fatura.
- Onde: todo botão com o selo de custo.
- Cuidado: uma falha incerta pode ser cobrada; a reserva não é devolvida automaticamente.

**Reserva conservadora** / **Piso de custo**
- Curta: a reserva é o teto bloqueado antes da chamada; o piso é o mínimo calculado pelos tokens informados.
- Cuidado: nenhum dos dois é o valor cobrado; tokens de raciocínio podem não ser informados (`ERRATUM-HFL-2026-001`).

**`VALID_PROPOSAL`**
- Nome visível: Proposta válida pelas regras.
- Curta: a resposta passou em todas as verificações automáticas do contrato e da carteira.
- Cuidado: não garante rentabilidade, não é ordem e não comprova que o texto explicativo está correto.
- Código: `validate()` em `scripts/multiasset_global_pm_v2.py`.

**`REJECTED_BY_VALIDATOR`**
- Nome visível: Resposta rejeitada pelo validador.
- Curta: a resposta violou alguma regra; o motivo aparece como código com descrição.
- Cuidado: a intenção econômica pode ser razoável mesmo assim; o registro fica para auditoria e nunca é corrigido depois.

**Demonstração sintética**
- Curta: exemplo com dados ou respostas roteirizadas, sem IA real.
- Cuidado: nunca é resultado do Gemini nem desempenho real.

**Tratamento científico**
- Curta: versão congelada de prompt, regras e contrato usada num experimento.
- Cuidado: tratamentos diferentes (ex.: Global PM V1 e V2) não são comparáveis como repetições.
