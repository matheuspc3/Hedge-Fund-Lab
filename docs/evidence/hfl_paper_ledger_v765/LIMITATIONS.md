# Limitações e próximos passos

Implementado e exercitado: identidade própria, envelope versionado, SQLite transacional temporário, eventos auditáveis, idempotência, reserva/cancelamento/fill, compras/vendas/custos, custódia/recebíveis/D+2, proveniência de preços, marcação, reconciliação, série de sessões, GET com filtros/páginas e dashboard com opt-in sintético. Referências V1/V2 são somente consultivas.

**Somente fixtures:** propostas, pareceres/risco, autorizações, fills e confirmações de custódia; fonte de referência sintética; fixture do formato RAW B3 para valorização. Todos os bancos graváveis são temporários externos. O servidor normal consulta uma exportação de qualificação verificada, não cria nem evolui banco. Não há carteira oficial ativa. Histórico demonstra o mecanismo, não performance científica prospectiva.

**Bloqueios explícitos:** calendário fora de 2026/01..08 verificado; sessão sem preços completos; estado financeiro divergente; proposta rejeitada, expirada ou sem operações; autorização ausente/estranha; veto; caixa/custódia insuficientes; IDs duplicados/chaves conflitantes; corrupção/schema/fingerprint divergente. Datas de outubro não são cobertas pelo adaptador novo. Motor/contratos antigos permanecem como selados.

Limitações: uma cesta pendente por carteira, fills integrais; BRL/ações inteiras; custos didáticos 0,1%, sem imposto; drawdown por pico de eventos V5; corporate actions não têm adaptador novo (qualificação evita essas datas/eventos); não há ingestão/licença/feed oficial ativo, abertura causal t+1/slippage, autenticação humana oficial, scheduler, atualização diária automática, backups/restauração de disco, cadeia externamente assinada/ancorada ou persistência multi-host. Replay é O(n) e exportação inclui contextos completos. UI não oferece edição/execução do ledger.

## NEXT_STEPS

1. Revisão humana do contrato operacional e de seus limites didáticos; definir tratamento científico independente e capital virtual próprio.
2. Validar calendário prospectivo e ingestão RAW B3, proveniência/licença/cache, tipos OPEN/CLOSE, corporate actions e fontes de confirmação de custódia.
3. Congelar regras causais decisão t → autorização antes da abertura → preço observado t+1, limites/slippage, cancelamentos/expiração; não converter decisões antigas em ordens.
4. Implementar autorização humana autenticada por campanha/carteira/proposta/estado/quantidades/prazo. H2 e autorizações de inferência não são reutilizáveis.
5. Qualificar caminho prospectivo com novas fixtures, revisão independente, backup e ancoragem de cadeia. Só depois autorizar criação de raiz persistente oficial e escrita explícita, separada de GET.
6. Revisar pendência backend V1 em processo próprio e apresentação do pending original H2, sem alterar política científica retroativamente.

Não se espera cobrança de inferência nos testes offline; nenhuma chamada paga foi feita. Custos futuros de modelos, dados/licença e infraestrutura dependerão das escolhas e orçamento aprovados; nenhum valor foi estimado/inventado aqui. Principais riscos científicos: misturar RAW/ajustado, considerar validação como autorização, preencher retrospectivamente com preço já conhecido, reutilizar contexto/autorização vencidos ou apresentar fixture como resultado oficial. Guardas desta entrega bloqueiam essas transições no novo escritor; ativação futura exige revisão adicional.
