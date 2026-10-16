# Arquitetura e hierarquia do Radar

## Visível primeiro

1. Finalidade consultiva/histórica e seletor da execução registrada.
2. Sessão, classificação, estado e quantidade de pareceres completos.
3. Jornada Universo → Comitês → Consenso → Risk → Resultado.
4. Cards do universo; cada card separa sinal, consenso, Risk e resultado.
5. Comparação em tabela `ds-table`, com filtros por ativo/sinal/Risk/resultado.

Os filtros atuam em memória. `?run=` é mantido; `asset`, `signal`, `risk` e
`final` também sobrevivem à recarga. O detalhe é compartilhável por `asset`.
Trocar de execução aborta requisições pendentes, limpa os painéis anteriores e
invalida o preflight, preservando a proteção original contra mistura de execuções.

## Aprofundamento

O detalhe mostra resumo → indicadores recolhidos → consenso e distribuição dos
votos → cinco analistas individualmente expansíveis → Risk → evidências avançadas.
Cada voto mostra identificador, sinal, confiança, códigos/roles de evidência e
metadados. Ausência de justificativa textual é informada, sem produzir uma nova.

BBAS3 apresenta COMPRA 5/5 e VETADO com resultado MANTER. O campo
`risk_source=HARD_ASSET_VOLATILITY_RULE` determina o texto de regra determinística;
`ADVISORY_LLM` identifica os pareceres LLM. A confiança não é probabilidade de lucro.
Os estados combinam símbolo, texto e tom dos tokens existentes.

## Auditoria e operações

Histórico, incidente original, modelo/tratamento, hashes copiáveis, reservas,
custo observado por tokens, comparação de inputs e classificação ficam sob demanda.
29 chamadas registradas não são descritas como 29 votos. A tentativa original
continua selecionável como `INCIDENT_PRESERVED`, sem parecer válido substituto.

Preparar, preflight, recuperação offline e execução existentes ficam em um
`details` operacional separado. Seus endpoints, payloads, consentimento e
orçamentos permanecem. O botão pago ganhou revisão modal adicional, sem criar
um novo emissor de inferência. Radar → Carteira mantém run, seleção, sessão e modo.

Legado restante: formulário operacional, conferência dos inputs, comparação de
duas empresas e parte dos estilos de `radar.css`. UX-M4 não é declarado integralmente
concluído; a jornada de consulta foi migrada nesta versão.
