'use strict';
// DP-23: presentation/context only. Financial writes remain in the existing APIs.
(() => {
  const el=id=>document.getElementById(id), picker=el('product-wallet');
  if(!picker)return;
  const params=new URLSearchParams(location.search), route=location.pathname;
  const historical=params.get('demo')==='1'||(route==='/'&&location.hash==='#audit')||/^\/(legacy(?:\/|$)|paper(?:\.html|\/|$)|h2(?:\.html|\/|$)|index\.html$|portfolio(?:\.html|\/|$)|laboratory$|logs(?:\.html|\/|$))/.test(route);
  const esc=v=>String(v??'Indisponível').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const money=v=>v==null?'Indisponível':Number(v).toLocaleString('pt-BR',{style:'currency',currency:'BRL'});
  const view={'/operations':'operations','/comparison':'comparison','/dividends':'dividends','/wallets/new':'create','/laboratory':'laboratory'}[route]||'wallet';
  const titles={wallet:'Visão da carteira',operations:'Operações',comparison:'Comparar carteiras',dividends:'Proventos',create:'Criar carteira'};
  let selected=params.get('wallet')||'';
  function carry(id){
    document.querySelectorAll('.hfl-primary a,.hfl-archive a,.product-wallet-link').forEach(a=>{
      const u=new URL(a.getAttribute('href'),location.origin);
      // Legacy and laboratory ledgers have their own wallet identities.
      if(['/','/operations','/comparison','/dividends','/wallets/new','/radar','/data','/market'].includes(u.pathname)){
        if(id)u.searchParams.set('wallet',id);else u.searchParams.delete('wallet');
        a.href=u.pathname+u.search+u.hash;
      }
    });
  }
  function walletsLoaded(wallets,id){
    selected=id||selected||wallets[0]?.id||'';
    if(!wallets.some(w=>w.id===selected))selected=wallets[0]?.id||'';
    picker.innerHTML=wallets.length?wallets.map(w=>`<option value="${esc(w.id)}">${esc(w.name)}</option>`).join(''):'<option value="">Nenhuma carteira</option>';
    picker.value=selected;picker.disabled=!wallets.length;
    el('product-nature').textContent=wallets.find(w=>w.id===selected)?.nature_label||'';
    carry(selected);
    if(el('product-comparison')){
      el('product-comparison').innerHTML=wallets.length?`<div class="ds-table-wrap product-compare-table" tabindex="0" role="region" aria-label="Carteiras comparadas"><table class="ds-table"><thead><tr><th>Carteira</th><th>Natureza / grupo</th><th>Capital inicial</th><th>Caixa econômico</th><th>Patrimônio marcado</th><th>Posições</th></tr></thead><tbody>${wallets.map(w=>`<tr><td><a href="/?wallet=${encodeURIComponent(w.id)}">${esc(w.name)}</a></td><td>${esc(w.nature_label)}<small>${esc(w.comparison_group||'Pessoal; sem grupo comparativo')}</small></td><td>${money(w.capital)}</td><td>${money(w.cash)}</td><td>${money(w.equity)}</td><td>${w.positions.length}</td></tr>`).join('')}</tbody></table></div>`:'<p>Nenhuma carteira cadastrada.</p>';
    }
  }
  picker.addEventListener('change',()=>{
    const u=new URL(location.href);u.searchParams.set('wallet',picker.value);
    // Navigation intentionally clears any unconfirmed operation/paid consent.
    location.assign(u.pathname+u.search+u.hash);
  });
  window.addEventListener('hfl:wallets',e=>walletsLoaded(e.detail.wallets,e.detail.selected));
  if(window.HFLPersonalCatalog)walletsLoaded(window.HFLPersonalCatalog.wallets,window.HFLPersonalCatalog.selected);
  window.addEventListener('popstate',()=>carry(picker.value));
  if(historical){
    picker.innerHTML='<option>Contexto independente</option>';picker.disabled=true;
    el('product-nature').textContent=params.get('demo')==='1'?'Demonstração sintética':'Acervo / laboratório';
  }
  if(el('personal-portfolios')){
    document.body.dataset.productView=view;
    if(titles[view]){el('personal-title').textContent=titles[view];document.title=titles[view]+' · Hedge Fund Lab';}
    const laboratory=el('home-laboratory');
    laboratory.hidden=view!=='laboratory'&&location.hash!=='#audit';
    if(view==='laboratory'||location.hash==='#audit'){laboratory.open=true;el('personal-portfolios').hidden=true;}
    document.querySelectorAll('[data-personal-view]').forEach(n=>{n.hidden=n.dataset.personalView!==view;});
    if(view==='create')el('personal-create').hidden=false;
    if(params.get('demo')!=='1'&&view!=='laboratory')el('home-portfolio').hidden=true;
    el('product-buy')?.addEventListener('click',()=>setSide('BUY'));
    el('product-sell')?.addEventListener('click',()=>setSide('SELL'));
    function setSide(side){const input=el('trade-form').elements.namedItem('side');input.value=side;input.dispatchEvent(new Event('change',{bubbles:true}));document.querySelectorAll('[data-side]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.side===side)));}
    el('trade-form').elements.namedItem('side').addEventListener('change',e=>document.querySelectorAll('[data-side]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.side===e.target.value))));
  }else if(!historical){
    fetch('/api/portfolio/manual',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error();return r.json();}).then(d=>walletsLoaded(d.wallets)).catch(()=>{picker.innerHTML='<option value="">Carteiras indisponíveis</option>';picker.disabled=true;});
  }
  if(el('new-analysis')){
    let currentStage;
    function stage(){
      const name={'#new-analysis':'setup','#analysis-workflow':'workflow','#analysis-results':'results'}[location.hash]||(params.get('run')?'results':'setup');
      document.body.dataset.agentStage=name;
      document.querySelectorAll('[data-agent-screen]').forEach(n=>{n.hidden=n.dataset.agentScreen!==name;});
      document.querySelectorAll('[data-agent-stage]').forEach(n=>{if(n.dataset.agentStage===name)n.setAttribute('aria-current','step');else n.removeAttribute('aria-current');});
      if(currentStage&&currentStage!==name)window.dispatchEvent(new CustomEvent('hfl:analysis-stage',{detail:name}));
      currentStage=name;
    }
    window.addEventListener('hashchange',stage);stage();
  }
  if(!el('product-data-body'))return;
  async function loadData(){
    el('product-data-status').textContent='Conferindo a execução e os dados registrados…';
    el('product-data-error').hidden=true;
    try{
      const r=await fetch('/api/platform/radar-runs',{cache:'no-store'}),registry=await r.json();if(!r.ok)throw Error(registry.error);
      const run=registry.runs.find(x=>x.id===registry.runner);
      if(!run)throw Error('Nenhuma execução operacional disponível. Crie uma análise na área Agentes.');
      const q=new URLSearchParams({run:run.id,session:run.session,tickers:run.universe.join(',')});
      const response=await fetch('/api/platform/radar-readiness?'+q,{cache:'no-store'}),d=await response.json();if(!response.ok)throw Error(d.error);
      el('product-data-status').textContent=`Dados dos agentes até ${d.session.split('-').reverse().join('/')} · ${d.inputs_ready}/${d.items.length} ativos preparados.`;
      el('product-data-run').textContent=run.id;
      el('product-data-body').innerHTML=d.items.map(i=>`<tr><td><strong>${esc(i.ticker)}</strong></td><td><span class="product-health ${i.input_state==='FROZEN'?'':i.input_state==='PREPARING'?'neutral':'warn'}">${esc({FROZEN:'Preparado',PREPARING:'Preparando',BLOCKED_DATA:'Dados incompletos',PREPARATION_REQUIRED:'Ainda não preparado',INTEGRITY_ERROR:'Revisão necessária',UNRESOLVED_DIVERGENCE:'Divergência'}[i.input_state]||i.input_state)}</span></td><td>${esc(i.input?.mode==='synthetic'?'Sintética':i.input?'B3 + ajuste Yahoo':'B3 + ajuste Yahoo · preparo pendente')}</td><td>${esc(i.action)}${i.error?`<small>${esc(i.error)}</small>`:''}</td></tr>`).join('');
    }catch(e){el('product-data-error').textContent=e.message||'Não foi possível consultar os dados.';el('product-data-error').hidden=false;el('product-data-status').textContent='Consulta indisponível. Nenhuma coleta foi iniciada.';}
  }
  el('product-data-refresh').addEventListener('click',loadData);
  el('product-data-prepare').addEventListener('click',()=>el('hfl-market-open').click());
  loadData();
})();
