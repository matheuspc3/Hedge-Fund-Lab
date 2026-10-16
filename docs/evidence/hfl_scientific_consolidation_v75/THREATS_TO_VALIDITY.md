# Ameaças à validade

Escopo: Radar `radar-2026-10-09-recovery-01` e as inferências Global PM V1
(`v7-5a78…`) e V2 (`v74-76d0…`). As mitigações abaixo são **propostas** para
experimentos futuros; nenhuma foi executada nesta etapa.

Organização: validade interna (o que os registros sustentam sobre causa e
efeito), de construto (se o que se mede corresponde ao conceito), externa
(generalização) e de conclusão (força estatística)
**[REFERÊNCIA PENDENTE: taxonomia de ameaças à validade em engenharia de software experimental]**.

| # | Ameaça | Tipo | Como afeta as conclusões | Mitigação futura proposta |
|---|---|---|---|---|
| T1 | **Amostra reduzida:** uma sessão de mercado, cinco comitês, duas inferências globais | conclusão, externa | Nenhuma taxa (aprovação, rejeição, divergência do gestor) é estimável; as contagens descrevem só este caso | Várias sessões pré-registradas; tamanho de amostra definido antes da coleta e justificado pelo efeito de interesse |
| T2 | **Mudança de tratamento:** V1 e V2 diferem em prompt, schema, contrato, política de validação e snapshot | interna | A diferença de desfecho não pode ser atribuída a um fator isolado; V1 e V2 não são replicações | Desenho fatorial (prompt × schema) sobre os mesmos contextos congelados, um tratamento versionado por célula |
| T3 | **Ausência de repetição independente:** uma chamada por tratamento | conclusão | Sem variância observada, não há estimativa de robustez nem intervalo | N chamadas por tratamento sobre o mesmo contexto, com orçamento aprovado; relatar proporções com intervalo de confiança |
| T4 | **Variação estocástica do LLM:** temperatura 1,0, `thinking_level` low, sem semente no Global PM | interna | Respostas diferentes podem surgir sem nenhuma mudança de contrato; o sucesso V2 pode ser amostral | Repetições (T3); registrar semente quando o provedor suportar; comparar com temperatura reduzida como tratamento separado |
| T5 | **Dependência de dados históricos:** inferências em 12/10 sobre a sessão de 09/10 | externa | Não há comportamento prospectivo; o modelo não decidiu em tempo real | Protocolo prospectivo (decisão antes do pregão seguinte), com dados congelados por hash antes da chamada |
| T6 | **Dependência de simulação:** carteira hipotética de R$ 100.000, preços constantes, política didática não aprovada para piloto | construto, externa | "Validação financeira" significa conformidade a regras contábeis didáticas, não viabilidade real | Manter o rótulo didático; só associar a mercado real após política de risco aprovada e piloto autorizado |
| T7 | **Dependência de entradas geradas por LLM:** pareceres de analistas e do Risk LLM podem conter erros factuais | interna, construto | O gestor herda erros (ex.: "rompimento de Bollinger" de ITUB4, vindo do Risk) | Estender o vocabulário fechado e a conferência numérica aos pareceres do Risk; rotular texto recebido como não verificado |
| T8 | **Cobertura limitada da validação textual:** o validador verifica estrutura e métricas citadas, não a argumentação | construto | `VALID_PROPOSAL` não implica fundamentação correta; a V2 ainda contém "teto regulamentar" e linguagem preditiva | Auditoria humana cega com rubrica pré-definida; ampliar o conjunto de afirmações estruturadas e verificáveis |
| T9 | **Ausência de ordens reais:** execução desabilitada | externa | Não há evidência de execução, slippage, liquidez ou rentabilidade | Fora do escopo do TCC sem nova autorização; se houver, paper trading prospectivo com custos reais modelados |
| T10 | **Seleção posterior:** a V2 foi desenhada depois de observar a falha da V1 | interna, conclusão | A melhoria é evolução orientada por diagnóstico, não confirmação independente; o contrato pode ter sido ajustado ao caso observado | Congelar o contrato V2 e testá-lo em sessões **novas**, não vistas durante o desenvolvimento; pré-registrar hipóteses e critérios |
| T11 | **Validação exercitada parcialmente:** a resposta real V2 não tinha operações | construto | Invariantes de liquidação, custódia de venda, sizing e custo só foram exercitadas em casos sintéticos | Sessões em que o gestor proponha operações; manter os casos sintéticos como teste de regressão, nunca como resultado |
| T12 | **Contabilidade incompleta de custo:** pensamento não informado; fatura não consultada | construto | O custo é só um piso; comparações de custo V1 × V2 não são confiáveis | Conciliar com o console de faturamento; registrar `thoughtsTokenCount` quando o provedor informar |
| T13 | **Dependência de artefatos locais:** registros primários fora do Git | confiabilidade | Um avaliador externo sem os registros só confere as evidências versionadas | Pacote de arquivamento com os registros não sensíveis (sem journals privados), com hashes do manifesto |
| T14 | **Viés do pesquisador na interpretação do texto livre** | construto | A classificação "sem suporte" das afirmações é manual | Segundo avaliador independente; concordância entre avaliadores |
| T15 | **Versão do modelo do provedor:** `gemini-3.8-flash` pode mudar no servidor sem mudança de nome | interna, externa | Repetições futuras podem não ser comparáveis | Registrar `modelVersion` e o ID da resposta (já gravados) e tratar mudança de versão como novo tratamento |

## O que as ameaças **não** invalidam

- Os fatos observados e verificados por hash: os pareceres do Radar, o status
  selado de cada inferência, os erros do validador e os tokens informados.
- A rejeição V1 como comportamento correto do validador V1 para aquela
  resposta.
- A conformidade da resposta V2 às invariantes do próprio tratamento V2.

## O que as ameaças impedem

- Qualquer afirmação de superioridade da V2 sobre a V1, de eficácia geral do
  novo contrato ou de taxa de conformidade.
- Qualquer afirmação sobre rentabilidade, risco futuro, alfa, drawdown ou
  benefício causal da arquitetura multiagentes.
