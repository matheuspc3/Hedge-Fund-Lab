'use strict';
// Shared shell (V7.6.2): one global navigation rendered by the server from AREAS; this
// script only marks the current area/section from path + hash, keeps the breadcrumb and
// environment strip in sync, carries ?run= between Radar and Carteira, and drives the
// responsive menu. The separate block below provides the explicit shared data update.
(() => {
  const shell = document.querySelector('.hfl-shell');
  if (!shell) return;
  const menu = shell.querySelector('.hfl-menu'), links = shell.querySelector('.hfl-links');
  const primary = [...shell.querySelectorAll('.hfl-primary a,.hfl-archive a')], secondary = [...shell.querySelectorAll('.hfl-secondary a')];
  const ALIASES = { '/index.html': '/legacy/backtests', '/paper': '/legacy/paper', '/paper/': '/legacy/paper', '/paper.html': '/legacy/paper', '/h2': '/legacy/h2', '/h2/': '/legacy/h2', '/h2.html': '/legacy/h2', '/platform.html': '/', '/legacy/': '/legacy' };
  const norm = (p) => { p = ALIASES[p] || p.replace(/\.html$/, '').replace(/\/$/, ''); return p || '/'; };
  //: Pages that understand ?run=<radar run id>; the parameter is carried between them.
  const RUN_PAGES = new Set(['/market', '/radar', '/portfolio']);
  //: Hashes a page resolves to another view (mirrors paper.js VIEWS/LEGACY; '' = default view).
  const HASH_ALIASES = { '/portfolio': { '': '#visao-geral', '#ai-proposal': '#simulador', '#carteira-contabil': '#simulador' }, '/legacy/paper': { '': '#visao', '#supervisao': '#sala', '#room': '#sala', '#wallets': '#carteiras' } };

  function setMenu(open) {
    menu.setAttribute('aria-expanded', String(open));
    links.classList.toggle('is-open', open);
  }
  menu.addEventListener('click', () => setMenu(menu.getAttribute('aria-expanded') !== 'true'));
  shell.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && menu.getAttribute('aria-expanded') === 'true') { setMenu(false); menu.focus(); }
  });

  function carryRun() {
    const run = new URLSearchParams(location.search).get('run');
    [...primary, ...secondary].forEach((a) => {
      const url = new URL(a.getAttribute('href'), location.origin);
      if (!RUN_PAGES.has(norm(url.pathname))) return;
      if (run) url.searchParams.set('run', run); else url.searchParams.delete('run');
      a.href = url.pathname + url.search + url.hash;
    });
  }

  function active() {
    const path = norm(location.pathname), hash = (HASH_ALIASES[path] || {})[location.hash] ?? location.hash;
    const target = (a) => { const u = new URL(a.href, location.origin); return [norm(u.pathname), u.hash]; };
    const fallback = shell.dataset.defaultArea;
    // Exact section (path + hash), then a section of the same page without hash, then the
    // first section of this page inside the server's default area, then the area itself.
    let section = secondary.find((a) => { const [p, h] = target(a); return p === path && h === hash; })
      || secondary.find((a) => { const [p, h] = target(a); return p === path && !h && !hash; })
      || (hash ? null : secondary.find((a) => a.dataset.area === fallback && target(a)[0] === path));
    let area = section?.dataset.area
      || primary.find((a) => { const [p, h] = target(a); return p === path && h === hash; })?.dataset.area
      || fallback;
    if (!section && hash) section = secondary.find((a) => a.dataset.area === area && target(a)[0] === path) || null;
    const areaLink = primary.find((a) => a.dataset.area === area);
    primary.forEach((a) => (a === areaLink ? a.setAttribute('aria-current', 'true') : a.removeAttribute('aria-current')));
    secondary.forEach((a) => {
      a.hidden = a.dataset.area !== area;
      a === section ? a.setAttribute('aria-current', 'page') : a.removeAttribute('aria-current');
    });
    shell.querySelector('.hfl-secondary').hidden = secondary.filter((a) => !a.hidden).length < 2;
    const crumbArea = shell.querySelector('[data-crumb=area]'), crumbPage = shell.querySelector('[data-crumb=page]');
    if (areaLink) {
      crumbArea.innerHTML = '';
      const link = document.createElement('a');
      link.href = areaLink.href;
      link.textContent = areaLink.textContent;
      crumbArea.appendChild(link);
      shell.querySelector('.hfl-env').textContent = areaLink.dataset.env || '';
    }
    crumbPage.hidden = !section;
    crumbPage.textContent = section ? section.textContent : '';
  }
  carryRun();
  active();
  window.addEventListener('hashchange', active);
  window.addEventListener('popstate', () => { carryRun(); active(); });

  // Scrollable tables become focusable, labelled regions (keyboard and screen readers).
  function tables(root) {
    const list = [...(root.matches?.('.scroll,.table-scroll,.table-container,.ds-table-wrap') ? [root] : []), ...root.querySelectorAll('.scroll,.table-scroll,.table-container,.ds-table-wrap')];
    list.forEach((e) => {
      e.tabIndex = 0;
      if (!e.hasAttribute('role')) e.setAttribute('role', 'region');
      if (!e.hasAttribute('aria-label')) e.setAttribute('aria-label', e.closest('.card,article,section')?.querySelector('h2,h3')?.textContent || 'Tabela rolável');
    });
  }
  tables(document);
  new MutationObserver((changes) => changes.forEach((c) => c.addedNodes.forEach((n) => { if (n.nodeType === 1) tables(n); }))).observe(document.querySelector('main') || document.body, { childList: true, subtree: true });
})();

// Shared data update: reuses the registered Radar runner and its existing POST gates.
(() => {
  const el=id=>document.getElementById(id), open=el('hfl-market-open');
  if(!open)return;
  const dialog=el('hfl-market-dialog'), start=el('hfl-market-start'), status=el('hfl-market-status'), reload=el('hfl-market-reload');
  let view=null, working=false, loading=false, timer=null, trackedJob=null;
  const messages={radar_busy_or_stale_lock:'Há uma operação ativa ou um bloqueio que precisa de revisão no Radar.',radar_run_header_mismatch_reload_page:'A execução operacional mudou. Feche e abra este painel novamente.',run_not_accepting_new_calls:'Esta execução está preservada somente para consulta.',local_origin_required:'Abra o dashboard pelo endereço local do servidor.',invalid_csrf:'A conexão com o servidor mudou. Feche e abra este painel novamente.'};
  async function get(url){const r=await fetch(url,{cache:'no-store'}),d=await r.json();if(!r.ok)throw Error(messages[d?.error]||d?.error||'Consulta indisponível.');return d;}
  function fail(e){working=false;loading=false;start.disabled=true;open.textContent='Atualizar dados da bolsa';dialog.setAttribute('aria-busy','false');status.textContent='Não foi possível atualizar: '+e.message+' Consulte o Radar antes de tentar novamente.';}
  async function inspect(){
    if(loading||working)return;
    loading=true;view=null;start.disabled=true;reload.hidden=true;trackedJob=null;
    el('hfl-market-scope').textContent='Consultando a execução operacional…';
    status.textContent='Consultando registros locais…';
    try{
      const registry=await get('/api/platform/radar-runs');
      if(!registry.runner)throw Error('Nenhuma execução operacional disponível.');
      view=await get('/api/platform/radar-view?'+new URLSearchParams({run:registry.runner}));
      const r=view.run;
      el('hfl-market-scope').textContent=`Sessão ${r.session.split('-').reverse().join('/')} · ${r.universe.join(', ')} · B3 oficial + fator ajustado.`;
      el('hfl-market-radar').href='/radar?'+new URLSearchParams({run:r.id});
      if(!view.mutation_available||r.mode!=='CONSULTATIVE_SANDBOX')throw Error('Execução disponível somente para consulta.');
      if(view.job?.status==='RUNNING'&&view.job.command==='prepare'){
        working=true;trackedJob=view.job.id;open.textContent='Atualizando dados…';dialog.setAttribute('aria-busy','true');status.textContent='Atualização de dados em andamento. Acompanhando a preparação já iniciada, sem duplicá-la.';timer=setTimeout(poll,500);
      }else if(view.job?.status==='RUNNING'){
        status.textContent='Já há uma operação em andamento. Acompanhe pelo Radar; nenhuma nova atualização foi iniciada.';
      }else{
        status.textContent='A atualização grava dados de referência. Não chama agentes nem cria operações financeiras.'+(view.last_closed_session&&r.session<view.last_closed_session?' Há uma sessão encerrada mais recente; escolha a execução correspondente no Radar para prepará-la.':'');
        start.disabled=false;
      }
    }catch(e){fail(e);}finally{loading=false;}
  }
  async function poll(){
    try{
      const current=await get('/api/platform/radar-view?'+new URLSearchParams({run:view.run.id})), job=current.job;
      if(!job||job.id!==trackedJob)throw Error('O registro da atualização mudou; confira seu resultado no Radar.');
      if(job.status==='RUNNING'){timer=setTimeout(poll,1500);return;}
      working=false;open.textContent='Atualizar dados da bolsa';dialog.setAttribute('aria-busy','false');reload.hidden=false;
      if(job.status!=='COMPLETED')throw Error('A preparação não foi concluída ('+job.status+').');
      const items=job.items||[], blocked=items.filter(i=>i.status==='BLOCKED');
      const ready=items.filter(i=>['PREPARED','EXISTING','COMPLETED'].includes(i.status));
      status.textContent=blocked.length?`Atualização com bloqueios: ${blocked.map(i=>i.ticker).join(', ')}. Consulte o diagnóstico no Radar.`:ready.length===view.run.universe.length?`Dados de referência disponíveis para os ${ready.length} ativos na sessão ${view.run.session.split('-').reverse().join('/')}. Registros já congelados são preservados. Nenhum agente foi executado.`:'Preparação concluída; confira a cobertura e os estados de cada ativo no Radar.';
    }catch(e){fail(e);}
  }
  open.addEventListener('click',()=>{dialog.showModal();if(!working)inspect();});
  el('hfl-market-close').addEventListener('click',()=>dialog.close());
  reload.addEventListener('click',()=>location.reload());
  start.addEventListener('click',async()=>{
    if(working||loading||!view||start.disabled)return;
    working=true;start.disabled=true;reload.hidden=true;open.textContent='Atualizando dados…';dialog.setAttribute('aria-busy','true');status.textContent='Atualizando preços e histórico… Você pode fechar este painel; a preparação continua no servidor.';
    try{
      const r=await fetch('/api/radar/prepare',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':view.csrf_token,'X-HFL-Radar-Run':view.run.id},body:JSON.stringify({tickers:view.run.universe,session:view.run.session,mode:'live'})});
      const job=await r.json();if(!r.ok)throw Error(messages[job?.error]||job?.error||'Preparação recusada.');
      trackedJob=job.id;timer=setTimeout(poll,500);
    }catch(e){fail(e);}
  });
  window.addEventListener('pagehide',()=>clearTimeout(timer));
})();
