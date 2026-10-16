'use strict';
(() => {
  const $=id=>document.getElementById(id), M=window.HFLMarket;
  let version=0, controller=new AbortController();
  async function get(path) {
    const r=await fetch('/api/platform/'+path,{signal:controller.signal});
    const d=await r.json(); if(!r.ok) throw Error(d.error || 'Consulta indisponível'); return d;
  }
  async function load() {
    const current=++version; controller.abort(); controller=new AbortController();
    $('market-error').hidden=true; $('market-room').hidden=true;
    $('market-asset').disabled=true; $('market-coverage').textContent='Consultando a cobertura da execução…'; $('market-to-radar').href='/radar';
    $('market-assets').innerHTML='<p class="ds-loading">Lendo ativos da execução…</p>';
    $('market-overview').replaceChildren();
    const q=new URLSearchParams(location.search);
    try {
      const registry=await get('radar-runs'); if(current!==version)return;
      const run=q.get('run') || registry.selected, asset=q.get('asset') || '';
      $('market-run').innerHTML=registry.runs.map(r=>`<option value="${M.esc(r.id)}">${M.esc(r.id)} · ${M.esc(r.state)}</option>`).join('');
      if(!registry.runs.some(r=>r.id===run))throw Error('Execução desconhecida. Selecione uma execução registrada.');
      $('market-run').value=run;
      const d=await get('radar-view?'+new URLSearchParams({run})); if(current!==version)return;
      const r=d.run;
      $('market-asset').innerHTML='<option value="">Todos os ativos</option>'+r.universe.map(t=>`<option>${M.esc(t)}</option>`).join('');
      if(asset && !r.universe.includes(asset))throw Error('Ativo fora do universo desta execução.');
      $('market-asset').value=asset;
      $('market-asset').disabled=false;
      history.replaceState(null,'',M.link('/market',run,asset));
      window.dispatchEvent(new PopStateEvent('popstate'));
      $('market-back').href=M.link('/market',run);
      $('market-to-radar').href=M.link('/radar',run,asset);
      $('market-overview').innerHTML=[['Sessão de referência',r.session],['Estado da execução',r.state],['Origem',r.classification],['Cobertura',r.universe.length+' ativos']].map(([label,value])=>`<article class="ds-kpi"><span class="ds-kpi-label">${label}</span><strong class="ds-kpi-value">${M.esc(value)}</strong></article>`).join('');
      $('market-coverage').textContent=`Cobertura limitada ao universo registrado: ${r.universe.join(', ')}. Fonte: ${r.source}. Sessão ${r.session}; consulta histórica, sem atualização automática de cotações.`;
      const rows=r.universe.filter(t=>!asset||asset===t).map(t=>d.items.find(i=>i.ticker===t && i.session===r.session) || {ticker:t,session:r.session,status:'NONE'});
      $('market-assets').innerHTML=rows.length ? rows.map(row=>M.summary(row,run)).join('') : '<p class="ds-empty">Nenhum ativo disponível nesta execução.</p>';
      if(asset) {
        const row=rows[0];
        const detail=row.status==='NONE'||row.status==='INTEGRITY_ERROR' ? row : await get('radar-detail?'+new URLSearchParams({run,ticker:asset,session:r.session}));
        if(current!==version)return;
        $('market-detail').innerHTML=M.detail(detail,run); $('market-room').hidden=false;
        $('market-room-title').focus();
      }
    } catch(e) {
      if(e.name==='AbortError'||current!==version)return;
      $('market-error').textContent=`Não foi possível consultar esta seleção: ${e.message}. Escolha outra execução ou atualize a consulta.`;
      $('market-error').hidden=false; $('market-assets').replaceChildren(); $('market-to-radar').href='/radar';
    }
  }
  function select() { const run=$('market-run').value, asset=$('market-asset').value; history.pushState(null,'',M.link('/market',run,asset)); load(); }
  $('market-run').addEventListener('change',()=>{ $('market-asset').value=''; select(); });
  $('market-asset').addEventListener('change',select);
  $('market-refresh').addEventListener('click',load);
  window.addEventListener('popstate',e=>{if(e.isTrusted)load();});
  load();
})();
