# Acessibilidade

Referência WCAG 2.2 AA; não se declara certificação integral.

Verificado em Chrome real: desktop 1440×900, notebook 1280×800, tablet 768×1024 e mobile 390×844 sem overflow horizontal da página. Tabelas rolam dentro de regiões focáveis com rótulo e cabeçalhos. Links das áreas usam ativação nativa por teclado e `aria-current`; voltar à lista restaura foco. Ajuda usa popover existente e Escape devolve foco ao botão. Estados têm texto/código/ícone. Valores/legendas dos gráficos também aparecem em tabelas. Erros têm `role=alert`, carregamento `aria-busy`, valores antigos ficam ocultos ao trocar fonte.

Cores seguem tokens contrastados existentes; teste de contraste V7.6.2 passou na regressão direcionada. Botões de área têm mínimo de 44px, seletor cabe em viewport estreito e foco segue o design system. Cards secundários usam divulgação progressiva. Inspeção visual corrigiu sobreposição da watchlist e reduziu a sequência mobile.

Limites: o teste de 720×450 avalia **reflow equivalente ao espaço útil de 200%**, não comprova zoom nativo do navegador. Sem leitor de tela real, auditoria completa de contraste de canvas, medição exaustiva de todos os alvos legados ou validação humana integral. Pendências UX-M8. Áreas operacionais H2 anteriores ainda aguardam migração completa UX-M6.
