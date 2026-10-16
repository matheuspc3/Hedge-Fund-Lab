'use strict';
(() => {
  const el = id => document.getElementById(id), root = el('personal-portfolios');
  if (!root) return;
  if(location.pathname==='/laboratory'||location.hash==='#audit'){root.hidden=true;return;}
  if (new URLSearchParams(location.search).get('demo') === '1') { root.hidden = true; return; }
  el('home-portfolio').hidden = true;
  const esc = v => String(v ?? 'Indisponível').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const money = v => v == null ? 'Indisponível' : Number(v).toLocaleString('pt-BR', {style:'currency',currency:'BRL'});
  const day = v => v.split('-').reverse().join('/');
  const stamp = v => new Date(v).toLocaleString('pt-BR', {timeZone:'America/Sao_Paulo'});
  const table = (headers, rows, empty) => rows.length ? `<div class="ds-table-wrap" tabindex="0" role="region" aria-label="${esc(headers[0])}"><table class="ds-table"><thead><tr>${headers.map(h=>`<th scope="col">${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${r.map(c=>`<td>${c}</td>`).join('')}</tr>`).join('')}</tbody></table></div>` : `<p>${esc(empty)}</p>`;
  const walletForm = el('wallet-form'), tradeForm = el('trade-form');
  const input = (form, name) => form.elements.namedItem(name);
  let wallets = [], wallet, csrf, preview, correction = null, busy = false, creationId;
  let selected = new URLSearchParams(location.search).get('wallet') || '';
  const today = new Intl.DateTimeFormat('sv-SE', {timeZone:'America/Sao_Paulo'}).format(new Date());
  for (const [form, name] of [[walletForm,'start_date'],[tradeForm,'economic_date']]) {
    input(form,name).value = today; input(form,name).max = today;
  }
  root.querySelectorAll('[data-error]').forEach(node => {
    node.id = node.closest('form').id + '-error-' + node.dataset.error;
    const field = input(node.closest('form'), node.dataset.error);
    field.setAttribute('aria-describedby', node.id);
  });
  function clearErrors() {
    el('personal-error').hidden = true;
    root.querySelectorAll('[data-error]').forEach(n=>{ n.textContent=''; });
    root.querySelectorAll('[aria-invalid]').forEach(n=>n.removeAttribute('aria-invalid'));
  }
  function failure(e, form) {
    el('personal-error').textContent = e.message; el('personal-error').hidden = false;
    const field = form && input(form,e.field), note = form?.querySelector(`[data-error="${e.field}"]`);
    if (note && field) { note.textContent=e.message; field.setAttribute('aria-invalid','true'); field.focus(); }
    el('personal-status').textContent = 'O registro não foi confirmado. Confira o erro e tente novamente.';
  }
  async function api(suffix='', payload) {
    const r = await fetch('/api/portfolio/manual'+suffix, payload ? {
      method:'POST', headers:{'Content-Type':'application/json','X-CSRF-Token':csrf}, body:JSON.stringify(payload)
    } : {cache:'no-store'});
    const d = await r.json();
    if (!r.ok) { const e = new Error(d.error || 'Consulta indisponível. Atualize a página.'); e.field=d.field; throw e; }
    return d;
  }
  async function action(fn, form) {
    if (busy) return;
    busy=true; clearErrors(); root.setAttribute('aria-busy','true');
    const controls=[...root.querySelectorAll('input,select,button')];
    controls.forEach(n=>{n.disabled=true;});
    try { await fn(); } catch(e) { failure(e,form); }
    finally { busy=false; controls.forEach(n=>{n.disabled=false;}); root.setAttribute('aria-busy','false');
      const invalid=form?.querySelector('[aria-invalid="true"]');
      if (invalid) invalid.focus(); else if (preview) el('personal-confirm').focus(); }
  }
  function dismiss() { preview=null; el('personal-preview').hidden=true; }
  function resetCorrection() {
    correction=null; dismiss(); input(tradeForm,'reason').value=''; input(tradeForm,'reason').required=false;
    el('correction-reason').hidden=true; el('personal-cancel').hidden=true; el('personal-void').hidden=true;
    el('operation-title').textContent='Registrar operação';
  }
  function render(w) {
    wallet=w; el('personal-detail').hidden=!w;
    if (!w) return;
    el('personal-name').textContent=w.name;
    el('personal-operations').href='/operations?'+new URLSearchParams({wallet:w.id});
    el('personal-analysis').href='/radar?'+new URLSearchParams({wallet:w.id})+'#new-analysis';
    el('personal-nature').textContent=`${w.nature_label} · início ${day(w.start_date)} · capital inicial ${money(w.capital)} · ${w.comparison_group?'base inicial comum · '+({BUY_HOLD:'Buy & Hold',MULTIAGENT:'Multiagentes'}[w.strategy]||w.strategy):'fora do grupo comparativo do piloto'}`+(w.initialization_note?'\n'+w.initialization_note:'');
    el('personal-metrics').innerHTML=[['Patrimônio total',w.equity==null?'Aguardando cotações':money(w.equity),w.equity==null?'Marcação diária ainda não integrada':'Carteira em caixa'],['Caixa econômico',money(w.cash),'Sem controle de liquidação'],['Custos registrados',money(w.costs),'Resultado realizado: '+money(w.realized_pnl)]].map(([label,v,detail])=>`<article class="ds-kpi"><span class="ds-kpi-label">${label}</span><strong class="ds-kpi-value">${v}</strong><span class="ds-kpi-detail">${detail}</span></article>`).join('');
    el('personal-prices').textContent=w.positions.length?'Preços de referência ausentes: faltam cotação, data e origem para '+w.positions.map(p=>p.ticker).join(', ')+'. Patrimônio investido e retorno indisponíveis. Custo médio é contábil, não cotação.':'Carteira em caixa. Não há preços de ativos nem série diária para calcular evolução ou retorno.';
    el('personal-positions').innerHTML=table(['Ativo','Quantidade','Custo médio','Custo total','Cotação / valor de mercado'],w.positions.map(p=>[esc(p.ticker),esc(p.quantity),Number(p.average_cost).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:8}),money(p.basis),'Indisponível']),'Sem posições. Registre uma compra abaixo.');
    el('personal-trades').innerHTML=table(['Data econômica','Ativo / movimento','Quantidade','Preço executado','Custos','Cadastrada em','Revisar'],w.trades.slice().reverse().map(t=>[day(t.economic_date),esc(t.ticker)+' · '+(t.side==='BUY'?'Compra':'Venda'),esc(t.quantity),money(t.price),money(t.costs),stamp(t.recorded_at),`<button type="button" data-correct="${esc(t.id)}">Corrigir</button>`]),'Esta carteira ainda não tem operações. Registre a primeira abaixo.');
    const replaced=new Map(w.audit.filter(e=>e.kind==='CORRECTION').map(e=>[e.target,e.trade?'Corrigido':'Anulado']));
    el('personal-audit').innerHTML=table(['Cadastrada em','Data econômica / operação preservada','Estado','Motivo'],w.audit.map(e=>[stamp(e.recorded_at),e.trade?`${day(e.trade.economic_date)} · ${esc(e.trade.ticker)} · ${e.trade.side==='BUY'?'Compra':'Venda'} · ${esc(e.trade.quantity)} × ${money(e.trade.price)} · custos ${money(e.trade.costs)}`:'Anulação de lançamento anterior',replaced.get(e.id)||(e.trade?'Vigente':'Anulação registrada'),e.source?`<a href="/radar?${new URLSearchParams({run:e.source.run,wallet:w.id,proposal:e.source.proposal})}#analysis-results">Gestor · referência ${day(e.source.reference_session)} · custo ${esc(e.source.cost_rate_pct)}%</a>`:esc(e.reason||'Registro original')]),'Sem lançamentos ou correções.');
    el('operation-origin').textContent=w.nature==='EXTERNAL'?'Registrar operação já executada externamente, declarada por você. A plataforma apenas contabiliza o negócio informado.':'Registrar simulação manual. Esta operação não pertence ao piloto dos agentes.';
    input(tradeForm,'economic_date').min=w.start_date;
  }
  async function load(message) {
    dismiss(); resetCorrection(); el('personal-detail').hidden=true;
    const d=await api(); csrf=d.csrf_token; wallets=d.wallets;
    const baseline=wallets.find(w=>w.strategy==='BUY_HOLD'&&w.comparison_group&&wallets.some(other=>other.strategy==='MULTIAGENT'&&other.comparison_group===w.comparison_group));
    if(baseline)el('personal-pilot').textContent='Base inicial comum cadastrada para Buy & Hold e Multiagentes. Consulte as operações e posições no seletor. Em Agentes → Resultados, o gestor propõe quantidades e permite aprovar uma cesta simulada aos preços de referência. O piloto prospectivo continua pendente.';
    const missing=Boolean(selected&&!wallets.some(w=>w.id===selected));
    if(missing)selected='';
    selected=selected || wallets[0]?.id || '';
    el('personal-wallet').innerHTML=wallets.length?wallets.map(w=>`<option value="${esc(w.id)}">${esc(w.name)} · ${esc(w.nature_label)}</option>`).join(''):'<option value="">Nenhuma carteira cadastrada</option>';
    el('personal-wallet').value=selected; render(wallets.find(w=>w.id===selected));
    el('personal-create').hidden=location.pathname!=='/wallets/new'&&Boolean(wallets.length);
    el('personal-status').textContent=message || (missing&&selected?'Carteira anterior indisponível. Exibindo '+wallet.name+'.':wallets.length?'Carteira consultada dos registros persistidos.':'Nenhuma carteira. Preencha o cadastro para começar.');
    if (selected) history.replaceState(null,'',location.pathname+'?'+new URLSearchParams({wallet:selected})+location.hash);
    window.HFLPersonalCatalog={wallets,selected};
    window.dispatchEvent(new CustomEvent('hfl:wallets',{detail:window.HFLPersonalCatalog}));
  }
  async function saved(d, message) {
    selected=d.wallet.id; dismiss(); resetCorrection();
    try { await load(message); }
    catch {
      // A committed receipt must never be presented as an unsuccessful write.
      wallets=[...wallets.filter(w=>w.id!==selected),d.wallet];
      el('personal-wallet').innerHTML=wallets.map(w=>`<option value="${esc(w.id)}">${esc(w.name)} · ${esc(w.nature_label)}</option>`).join('');
      el('personal-wallet').value=selected;render(d.wallet);
      history.replaceState(null,'',location.pathname+'?'+new URLSearchParams({wallet:selected}));
      window.dispatchEvent(new CustomEvent('hfl:wallets',{detail:{wallets,selected}}));
      el('personal-status').textContent=message+' A atualização do catálogo falhou; use Atualizar consulta.';
    }
  }
  function operationRequest(annul=false) {
    const values=Object.fromEntries(new FormData(tradeForm));
    const t={}; ['ticker','side','quantity','price','costs','economic_date'].forEach(k=>{t[k]=values[k];});
    return correction ? {kind:'CORRECTION',wallet:wallet.id,target:correction,reason:values.reason,trade:annul?null:t} : {kind:'TRADE',wallet:wallet.id,trade:t};
  }
  async function showPreview(r) {
    const d=await api('/preview',{request:r});
    preview={request:r,command_id:crypto.randomUUID(),preview_token:d.preview_token,confirm:true};
    el('personal-preview-note').textContent=r.kind==='CORRECTION'?(r.trade?'Correção: o original será preservado e substituído no cálculo.':'Anulação: o original será preservado e retirado do cálculo.'):'Registro de '+(r.trade.side==='BUY'?'compra':'venda')+' de '+r.trade.quantity+' '+r.trade.ticker+' em '+day(r.trade.economic_date)+'.';
    const all=[...new Set([...d.before.positions,...d.after.positions].map(p=>p.ticker))];
    const rows=[['Caixa econômico',money(d.before.cash),money(d.after.cash)],['Custos acumulados',money(d.before.costs),money(d.after.costs)]];
    for (const t of all) {
      const before=d.before.positions.find(p=>p.ticker===t), after=d.after.positions.find(p=>p.ticker===t);
      rows.push([t+' · quantidade',esc(before?.quantity||'0'),esc(after?.quantity||'0')],
        [t+' · custo médio',before?esc(before.average_cost):'Sem posição',after?esc(after.average_cost):'Sem posição']);
    }
    el('personal-effect').innerHTML=table(['Efeito ao final do histórico','Antes','Depois'],rows,'');
    el('personal-preview').hidden=false; el('personal-confirm').focus();
    el('personal-preview').scrollIntoView({block:'nearest'});
  }
  // Capture form values before disabling controls (FormData excludes disabled fields).
  walletForm.addEventListener('submit',e=>{
    e.preventDefault(); const values=Object.fromEntries(new FormData(walletForm));
    const r={kind:'CREATE',...values}; creationId ||= crypto.randomUUID();
    action(async()=>{const d=await api('/confirm',{request:r,command_id:creationId,preview_token:null,confirm:true});
      creationId=null; await saved(d,'Carteira criada. Registre sua primeira operação.');
      if(location.pathname==='/wallets/new')location.assign('/operations?'+new URLSearchParams({wallet:d.wallet.id}));},walletForm);
  });
  walletForm.addEventListener('input',()=>{if(!busy)creationId=null;});
  input(walletForm,'nature').addEventListener('change',()=>{input(walletForm,'capital').value=input(walletForm,'nature').value==='SIMULATION'?'100000':'';});
  tradeForm.addEventListener('submit',e=>{e.preventDefault(); const r=operationRequest(); action(()=>showPreview(r),tradeForm);});
  el('personal-void').addEventListener('click',()=>{if(!tradeForm.reportValidity())return;const r=operationRequest(true);action(()=>showPreview(r),tradeForm);});
  tradeForm.addEventListener('input',dismiss); tradeForm.addEventListener('change',dismiss);
  el('personal-dismiss').addEventListener('click',()=>{dismiss();input(tradeForm,'ticker').focus();});
  el('personal-confirm').addEventListener('click',()=>{if(!preview)return;const payload=preview;
    action(async()=>{const d=await api('/confirm',payload);await saved(d,'Registro confirmado e persistido. Caixa, posições e histórico atualizados.');},tradeForm);});
  el('personal-cancel').addEventListener('click',()=>{resetCorrection();clearErrors();});
  el('personal-trades').addEventListener('click',e=>{
    const button=e.target.closest('[data-correct]'); if(!button||busy)return;
    resetCorrection(); clearErrors(); correction=button.dataset.correct;
    const t=wallet.trades.find(t=>t.id===correction);
    ['ticker','side','quantity','price','costs','economic_date'].forEach(k=>{input(tradeForm,k).value=t[k];});
    input(tradeForm,'side').dispatchEvent(new Event('change',{bubbles:true}));
    el('operation-title').textContent='Corrigir operação preservando o original';
    el('correction-reason').hidden=false;input(tradeForm,'reason').required=true;
    el('personal-cancel').hidden=false;el('personal-void').hidden=false;input(tradeForm,'reason').focus();
  });
  el('personal-wallet').addEventListener('change',()=>{selected=el('personal-wallet').value;action(()=>load());});
  el('personal-refresh').addEventListener('click',()=>action(()=>load()));
  action(()=>load());
})();
