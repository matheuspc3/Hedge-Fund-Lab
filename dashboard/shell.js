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
    shell.classList.toggle('is-open', open);
    document.body.classList.toggle('hfl-shell-is-open', open);
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
    const areaSections = secondary.filter((a) => !a.hidden).length;
    shell.querySelector('.hfl-secondary').hidden = areaSections < 2;
    const areaEyebrow = shell.querySelector('.hfl-eyebrow--area');
    if (areaEyebrow) areaEyebrow.hidden = areaSections < 2;
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

// Shared market-base update (DP-27): local B3/Yahoo price base only; never runs agents.
(() => {
  const el=id=>document.getElementById(id), open=el('hfl-market-open');
  if(!open)return;
  const dialog=el('hfl-market-dialog'), start=el('hfl-market-start'), status=el('hfl-market-status'), reload=el('hfl-market-reload'), scope=el('hfl-market-scope'), list=el('hfl-market-coverage');
  let view=null, working=false, loading=false, timer=null;
  const day=v=>v.split('-').reverse().join('/');
  // COTAHIST_D15102026.ZIP -> 15/10 ; COTAHIST_A2026.ZIP -> arquivo anual 2026
  const fileLabel=f=>{const m=/_D(\d\d)(\d\d)\d{4}/.exec(f),y=/_A(\d{4})/.exec(f);return m?m[1]+'/'+m[2]:y?'arquivo anual '+y[1]:f;};
  async function call(url,post){
    const r=await fetch(url,post?{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':view?.csrf_token||''},body:'{}'}:{cache:'no-store'}),d=await r.json();
    if(!r.ok)throw Error(d?.error||'Consulta indisponível.');return d;
  }
  function busy(on){working=on;open.textContent=on?'Atualizando dados…':'Atualizar dados da bolsa';dialog.setAttribute('aria-busy',on?'true':'false');}
  function fail(e){busy(false);loading=false;start.disabled=false;status.textContent='Não foi possível atualizar: '+e.message;}
  function render(){
    const cov=view.coverage||{}, ts=Object.keys(cov), lasts=ts.filter(t=>cov[t]).map(t=>cov[t].last).sort(), base=lasts[0]||null;
    const current=!!base&&lasts.length===ts.length&&base>=view.closed;
    scope.textContent=(base?'Base local: dados até '+day(base):'Base local: sem dados ainda')+' · Último pregão fechado: '+day(view.closed)+'.';
    list.replaceChildren(...ts.map(t=>{const li=document.createElement('li');li.textContent=t+' · '+(cov[t]?'desde '+day(cov[t].first)+' · até '+day(cov[t].last):'sem dados ainda');return li;}));
    start.disabled=working||current;
    if(!working)status.textContent=(current?'Base em dia. ':'')+(view.last?summary(view.last):'');
  }
  function summary(l){
    const res=l.results||[], got=res.filter(r=>r.status==='ACQUIRED').length, miss=res.filter(r=>r.status==='NOT_PUBLISHED'), bad=res.filter(r=>r.status==='FAILED');
    const yahoo=Object.entries(l.yahoo||{}).filter(([,v])=>v!=='OK');
    return [(got===1?'1 arquivo novo':got+' arquivos novos')+' da B3.',
      miss.length?'B3 ainda não publicou: '+miss.map(r=>fileLabel(r.file)).join(', ')+'.':'',
      bad.length?'Falha: '+bad.map(r=>fileLabel(r.file)+' ('+r.error+')').join('; ')+'.':'',
      yahoo.length?'Yahoo: '+yahoo.map(([t,v])=>t+' ('+v+')').join('; ')+'.':'',
      'Nenhum agente foi executado.'].filter(Boolean).join(' ');
  }
  function follow(){
    if(view.running){busy(true);render();status.textContent='Atualização em andamento. Acompanhando…';timer=setTimeout(poll,1500);return;}
    const was=working;busy(false);render();
    // Finished: the existing "Atualizar esta visualização" button reloads the open page's data.
    if(was){reload.hidden=false;if(view.error)status.textContent='Não foi possível atualizar: '+view.error;}
  }
  async function poll(){try{view=await call('/api/platform/market-base');follow();}catch(e){fail(e);}}
  async function inspect(){
    if(loading||working)return;
    loading=true;reload.hidden=true;start.disabled=true;scope.textContent='Consultando a base local…';status.textContent='';
    try{view=await call('/api/platform/market-base');follow();}catch(e){fail(e);}finally{loading=false;}
  }
  open.addEventListener('click',()=>{dialog.showModal();inspect();});
  // ponytail: closing only stops polling; the server keeps updating and the next open follows it.
  dialog.addEventListener('close',()=>{clearTimeout(timer);busy(false);});
  el('hfl-market-close').addEventListener('click',()=>dialog.close());
  reload.addEventListener('click',()=>location.reload());
  start.addEventListener('click',async()=>{
    if(working||loading||!view||start.disabled)return;
    busy(true);start.disabled=true;reload.hidden=true;status.textContent='Atualizando a base local…';
    try{view=await call('/api/platform/market-base/update',true);follow();}catch(e){fail(e);}
  });
  window.addEventListener('pagehide',()=>clearTimeout(timer));
})();
