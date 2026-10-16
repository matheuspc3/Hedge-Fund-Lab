# Acessibilidade — escopo Mercado/Radar

Referência WCAG 2.2 AA; não é certificação de conformidade integral.

| Verificação | Evidência / limite |
|---|---|
| Status sem depender de cor | Ícones e rótulos COMPRA/VENDA/MANTER/APROVADO/VETADO; fonte do Risk em texto |
| Contraste | Tokens e bordas V7.6.2 reutilizados; teste `test_tokens_meet_contrast` preservado e aprovado |
| Filtros | Selects nativos com labels; operação real por teclado no Chrome |
| Detalhes | `details`/`summary` nativos; cinco votos recolhidos inicialmente |
| Ajuda | Componente único; abertura, Escape e retorno de foco testados |
| Mobile | Menu abre, fecha por Escape e restaura foco; popover dentro do viewport |
| Tabela | Caption, scopes, região rolável focável; overflow contido |
| Cópia | Botão nomeado e confirmação; leitura real do clipboard no teste |
| Reflow | Mercado e Radar em 1440, 1280, 768 e 390 CSS px, sem overflow da página |
| Ampliação 200% | Emulação de desktop com viewport CSS 720×450 e raster 1440×900; reflow aprovado. Não é uso manual do menu de zoom do Chrome |
| Modal de custo | `dialog` nativo, foco inicial em Cancelar, Escape, consentimento e confirmação testados |
| Gráficos novos | Medidores nativos de votos/RSI e contagem textual equivalente; nenhuma série fictícia |

As capturas foram inspecionadas quanto a hierarquia, cartões, espaçamento,
legibilidade e sobreposição. Leitor de tela real não foi executado: não há
sessão de NVDA/VoiceOver configurada no ambiente utilizado. A avaliação semântica
do DOM não equivale à experiência falada. Contraste de cada pixel dos gráficos
legados, espaçamento de texto personalizado e auditoria integral das outras
páginas ficam para UX-M8. O formulário operacional antigo permanece identificado
como legado, sem alegação de migração completa.
