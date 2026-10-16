# Próximos passos — não iniciados

- **UX-M2 parcial:** custo compartilhado e tabela do Radar adotados; migrar tabelas
  e confirmações das outras páginas conforme seus contratos próprios.
- **UX-M4 parcial:** exploração, comparação e detalhe de consulta implementados;
  controles operacionais e conferência de inputs ainda usam parte do legado.
  Séries temporais exigem escolher uma API de leitura oficial/versionada; não
  derivar preços absolutos ou séries fictícias das razões do contrato LLM.
- **UX-M5 pendente:** separar Carteira hipotética, registros do Gestor Global e
  demonstrações. Começar por consultas: consolidar V1 rejeitada/encerrada e V2
  validada sem confundir tratamento, resultado e autorização de ordem.
  `BACKEND_V1_CLOSURE_PENDING_APPROVAL` continua sendo decisão humana específica.
- **UX-M6 pendente:** Operação diária/H2/Pesquisa; adotar o diálogo somente após
  rastrear preflight e consentimento existentes. Final Test permanece bloqueado.
- **UX-M7 pendente:** auditoria dedicada, logs, configurações e ajuda ampliada.
- **UX-M8 pendente:** leitor de tela real, zoom manual, contraste dos gráficos e
  auditoria integral das telas restantes; validação com usuários.

Recomendação para UX-M5: migrar primeiro o histórico de propostas com o design
system compartilhado e testes somente de leitura; aprovar o gate V1 no serviço
não selado separadamente. Não criar um atalho pago V2 no painel por consequência
da migração visual.
