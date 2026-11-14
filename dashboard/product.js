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
  const titles={wallet:'Visão da carteira',operations:'Operações',comparison:'Comparar carteiras',dividends:'Proventos',create:'Criar carteira'},subtitles={comparison:'Compare a trajetória das carteiras do mesmo grupo com o Ibovespa e o CDI desde o início comum.',dividends:'Acompanhe dividendos e JCP dos ativos da carteira, da data-com ao pagamento.'};
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
  // DP-28 (A): cumulative return in %, read-only. Same revision + AbortController guard as personal-charts.js.
  const dm=v=>v?v.split('-').reverse().join('/'):'';
  const sp=(v,d=2)=>v==null?'Indisponível':(v>0?'+':'')+Number(v).toLocaleString('pt-BR',{minimumFractionDigits:d,maximumFractionDigits:d});
  const palette=['#3358d4','#0f8a68','#8757b4','#b07215','#ca5279']; // same order as personal-charts.js; color follows catalog order
  let cmpRev=0,cmpCtl,cmpChart;
  const getJson=async(url,signal)=>{const r=await fetch(url,{cache:'no-store',signal});const j=await r.json();if(!r.ok)throw Error(j.error||'HTTP '+r.status);return j;};
  async function compare(wallets,sel){
    const v=++cmpRev;cmpCtl?.abort();cmpCtl=new AbortController();const signal=cmpCtl.signal;
    const note=el('cmp-note'),box=el('product-comparison');cmpChart?.destroy();cmpChart=null;el('cmp-wrap').hidden=true;
    if(!wallets.length){note.textContent='';box.innerHTML='<p>Nenhuma carteira cadastrada.</p>';return;}
    const me=wallets.find(w=>w.id===sel),group=me?.comparison_group||wallets.find(w=>w.comparison_group)?.comparison_group||null;
    const inGroup=wallets.filter(w=>group&&w.comparison_group===group),ref=(inGroup.includes(me)?me:inGroup[0])?.start_date;
    const used=inGroup.filter(w=>w.start_date===ref),skipped=inGroup.filter(w=>w.start_date!==ref);
    note.textContent='Conferindo históricos e fechamentos…';box.textContent='';
    try{
      const hist=Object.fromEntries(await Promise.all(wallets.map(async w=>{try{const h=await getJson('/api/portfolio/history?'+new URLSearchParams({wallet:w.id}),signal);return [w.id,h.wallet===w.id&&h.read_only===true?h:null];}catch(e){if(e.name==='AbortError')throw e;return [w.id,null];}})));
      // ponytail: benchmark is best-effort; any failure only switches the note to "indisponível".
      let bench=null,cd=null;if(ref)try{const b=await getJson('/api/platform/market-base/benchmark?'+new URLSearchParams({since:ref}),signal);if(b.anchor&&b.rows?.length)bench=b;if(b.cdi?.anchor&&b.cdi.rows?.length>1)cd=b.cdi;}catch(e){if(e.name==='AbortError')throw e;}
      if(v!==cmpRev)return;
      const ok=used.filter(w=>hist[w.id]),anchored=ok.some(w=>hist[w.id].initial_anchor_available);
      const sessions=[...new Set(ok.flatMap(w=>hist[w.id].daily_history.map(p=>p.session)))].sort();
      const labels=[...(anchored?['Início · '+dm(ref)]:[]),...sessions.map(dm)];
      const wl=ok.map(w=>{const h=hist[w.id],cap=Number(h.initial_capital),m=Object.fromEntries(h.daily_history.map(p=>[p.session,p]));
        return {w,data:[...(anchored?[h.initial_anchor_available?0:null]:[]),...sessions.map(s=>m[s]?.state==='AVAILABLE'&&m[s].equity!=null?(Number(m[s].equity)/cap-1)*100:null)]};});
      const bm=bench&&Object.fromEntries(bench.rows.map(r=>[r.date,Number(r.close)])),a0=bench&&bm[bench.anchor];
      const ib=a0?[...(anchored?[0]:[]),...sessions.map(s=>bm[s]==null?null:(bm[s]/a0-1)*100)]:null;
      const cm=cd&&Object.fromEntries(cd.rows.map(r=>[r.date,Number(r.index)])),cdl=cd?[...(anchored?[0]:[]),...sessions.map(s=>cm[s]==null?null:(cm[s]-1)*100)]:null;
      let t=(!group?'Não há grupo comparativo cadastrado. ':!me?.comparison_group?'A carteira selecionada é pessoal e fica fora do grupo comparado (DP-19). ':'')+'Retorno acumulado sobre o capital inicial, por fechamentos B3 marcados ('+sessions.length+' pregões). ';
      const dv=ok.length>0&&ok.every(w=>hist[w.id].dividends); // DP-30: only claim dividends when every compared history carries them
      t+=ib?'Ibovespa (Yahoo ^BVSP) é referência externa ancorada no fechamento de '+dm(bench.anchor).slice(0,5)+'. ':'Ibovespa indisponível no momento. ';
      t+=dv?'As carteiras incluem proventos (recebidos e a receber, JCP líquido) desde a data-com; o Ibovespa inclui proventos reinvestidos. ':(ib?'O Ibovespa inclui proventos reinvestidos; ':'')+'as carteiras ainda não contabilizam proventos (APP-04). ';
      t+=cd?'CDI (Banco Central, série 12) acumulado desde '+dm(cd.anchor).slice(0,5)+'. ':'CDI indisponível no momento. ';
      t+='Diferença observada é descritiva, não indica superioridade.';
      if(ok.some(w=>['SMA_50_200','BOLLINGER_20_2'].includes(w.strategy)))t+=' SMA e Bollinger: mesma cesta inicial de 14/10; histórico reconstruído na inclusão, depois atualizado por regras, sem IA. Consulte as operações para distinguir reconstrução e simulação prospectiva.';
      if(skipped.length)t+=' Fora do gráfico por início diferente de '+dm(ref)+': '+skipped.map(w=>w.name).join(', ')+'.';
      note.textContent=t;
      const color=w=>palette[wallets.indexOf(w)%palette.length];
      const sets=[...wl.map(x=>({label:x.w.name,data:x.data,borderColor:color(x.w),backgroundColor:color(x.w),borderWidth:2.5,pointRadius:4,spanGaps:false,tension:0})),...(ib?[{label:'Ibovespa (referência)',data:ib,borderColor:'#58647b',backgroundColor:'transparent',pointBackgroundColor:'#58647b',borderWidth:2,borderDash:[6,4],pointRadius:3,pointStyle:'rect',spanGaps:false,tension:0}]:[]),...(cdl?[{label:'CDI (referência)',data:cdl,borderColor:'#85570c',backgroundColor:'transparent',pointBackgroundColor:'#85570c',borderWidth:2,borderDash:[2,3],pointRadius:3,pointStyle:'triangle',spanGaps:false,tension:0}]:[])];
      const any=sets.some(s=>s.data.some(x=>x!=null));
      el('cmp-wrap').hidden=!any;
      if(any){
        cmpChart=new Chart(el('cmp-chart'),{type:'line',data:{labels,datasets:sets},options:{responsive:true,maintainAspectRatio:false,animation:false,interaction:{mode:'index',intersect:false},plugins:{legend:{labels:{color:'#43516a',boxWidth:12}},tooltip:{callbacks:{label:c=>c.dataset.label+': '+(c.raw==null?'Indisponível':sp(c.raw)+'%')}}},scales:{x:{grid:{display:false},ticks:{color:'#657188',maxTicksLimit:7,maxRotation:0}},y:{grid:{color:'#e2e7f0'},ticks:{color:'#657188',callback:x=>sp(x,1)+'%'}}}}});
        el('cmp-table').innerHTML='<div class="ds-table-wrap" tabindex="0" role="region" aria-label="Retorno acumulado por sessão"><table class="ds-table"><thead><tr><th scope="col">Data</th>'+sets.map(s=>'<th scope="col">'+esc(s.label)+'</th>').join('')+'</tr></thead><tbody>'+labels.map((l,i)=>'<tr><td>'+esc(l)+'</td>'+sets.map(s=>'<td>'+(s.data[i]==null?'Indisponível':sp(s.data[i])+'%')+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';
      }
      // Wallet table: every figure comes from the stored history; "Indisponível" only when data is truly missing.
      const per=(h,k)=>h?.periods.find(p=>p.key===k),good=p=>p?.state==='AVAILABLE';
      const last=h=>h?.daily_history.filter(p=>p.state==='AVAILABLE').at(-1);
      const bh=w=>wallets.find(o=>o.strategy==='BUY_HOLD'&&o.comparison_group&&o.comparison_group===w.comparison_group);
      const ret=p=>good(p)?sp(p.return_fraction*100)+'%<small>'+dm(p.anchor_session).slice(0,5)+' → '+dm(p.end_session).slice(0,5)+'</small>':'histórico insuficiente';
      const diff=w=>{if(!w.comparison_group)return 'fora do grupo';const b=bh(w);if(!b)return '—';if(b===w)return 'referência';const x=per(hist[w.id],'inception'),y=per(hist[b.id],'inception');
        return good(x)&&good(y)&&x.anchor_session===y.anchor_session&&x.end_session===y.end_session?sp((x.return_fraction-y.return_fraction)*100)+' p.p.':'—';};
      const rows=wallets.map(w=>{const h=hist[w.id],l=last(h);return '<tr><td><a href="/?wallet='+encodeURIComponent(w.id)+'">'+esc(w.name)+'</a></td><td>'+esc(w.nature_label)+'<small>'+esc(w.comparison_group||'Pessoal; sem grupo comparativo')+'</small></td><td>'+(l?money(l.equity)+'<small>fechamento '+dm(l.session).slice(0,5)+'</small>':money(w.equity))+'</td><td>'+(h?ret(per(h,'inception')):'Indisponível')+'</td><td>'+(h?ret(per(h,'1d')):'Indisponível')+'</td><td>'+diff(w)+'</td><td>'+money(w.cash)+'</td><td>'+(w.trades?.length??0)+'</td><td>'+money(w.costs)+'</td></tr>';});
      if(ib){const n=bench.rows.at(-1),p=bench.rows.at(-2);rows.push('<tr><td>Ibovespa (referência)<small>Yahoo ^BVSP · inclui proventos</small></td><td>Índice externo</td><td>—</td><td>'+(n.date>bench.anchor?sp((Number(n.close)/a0-1)*100)+'%<small>'+dm(bench.anchor).slice(0,5)+' → '+dm(n.date).slice(0,5)+'</small>':'histórico insuficiente')+'</td><td>'+(p&&n.date>p.date?sp((Number(n.close)/Number(p.close)-1)*100)+'%<small>'+dm(p.date).slice(0,5)+' → '+dm(n.date).slice(0,5)+'</small>':'histórico insuficiente')+'</td><td>—</td><td>—</td><td>—</td><td>—</td></tr>');}
      if(cd){const n=cd.rows.at(-1),p=cd.rows.at(-2);rows.push('<tr><td>CDI (referência)<small>Banco Central · SGS 12</small></td><td>Taxa externa</td><td>—</td><td>'+sp((n.index-1)*100)+'%<small>'+dm(cd.anchor).slice(0,5)+' → '+dm(n.date).slice(0,5)+'</small></td><td>'+sp((n.index/p.index-1)*100)+'%<small>'+dm(p.date).slice(0,5)+' → '+dm(n.date).slice(0,5)+'</small>'+'</td><td>—</td><td>—</td><td>—</td><td>—</td></tr>');}
      box.innerHTML='<div class="ds-table-wrap product-compare-table" tabindex="0" role="region" aria-label="Carteiras comparadas"><table class="ds-table"><thead><tr>'+['Carteira','Natureza / grupo','Patrimônio marcado','Retorno desde o início','Dia','Diferença vs Buy & Hold','Caixa','Operações','Custos'].map(h=>'<th scope="col">'+h+'</th>').join('')+'</tr></thead><tbody>'+rows.join('')+'</tbody></table></div>';
    }catch(e){if(e.name!=='AbortError'&&v===cmpRev){note.textContent='Comparação indisponível. Nenhum valor foi estimado.';box.textContent='';}}
  }
  // DP-30: read-only proventos page; same revision + AbortController guard as compare(). Missing `dividends` is "indisponível", never zero.
  let divRev=0,divCtl;
  const KIND={DIVIDENDO:'Dividendo',JCP:'JCP líquido (15% IR)',OUTRO:'Outro provento'},SITU={RECEBIDO:'Recebido',A_RECEBER:'A receber',PREVISTO:'Anunciado'};
  const unit=v=>v==null?'Indisponível':Number(v).toLocaleString('pt-BR',{style:'currency',currency:'BRL',maximumFractionDigits:6});
  async function dividends(id){
    const v=++divRev;divCtl?.abort();divCtl=new AbortController();
    const status=el('div-status'),tiles=el('div-tiles');el('div-table').textContent='';el('div-note').textContent='';tiles.textContent='';
    if(!id){status.textContent='Crie ou selecione uma carteira para ver proventos.';return;}
    status.textContent='Conferindo proventos…';
    try{
      const h=await getJson('/api/portfolio/history?'+new URLSearchParams({wallet:id}),divCtl.signal);
      if(v!==divRev)return;
      if(h.wallet!==id||h.read_only!==true)throw Error();
      const d=h.dividends,ev=[...(d?.events||[])].sort((a,b)=>b.data_com<a.data_com?-1:b.data_com>a.data_com?1:0);
      const n=s=>ev.filter(e=>e.state===s).length;
      tiles.innerHTML=[['Recebidos (líquido)',d?.received,'RECEBIDO'],['A receber',d?.receivable,'A_RECEBER'],['Anunciados (previstos)',d?.announced,'PREVISTO']].map(([l,x,s])=>'<div class="ds-kpi"><span class="ds-kpi-label">'+l+'</span><span class="ds-kpi-value">'+money(d?x:null)+'</span><span class="ds-kpi-detail">'+(d?n(s)+' evento(s)':'integração de proventos indisponível')+'</span></div>').join('');
      if(!d){status.textContent='Integração de proventos indisponível para esta carteira. Nenhum valor foi estimado.';return;}
      status.textContent=ev.length?ev.length+' evento(s) desde o início da carteira.':'Nenhum provento desde o início da carteira.';
      if(ev.length)el('div-table').innerHTML='<div class="ds-table-wrap" tabindex="0" role="region" aria-label="Proventos da carteira"><table class="ds-table"><thead><tr>'+['Ativo','Tipo','Data-com','Pagamento','Valor por ação','Quantidade','Valor líquido','Situação'].map(x=>'<th scope="col">'+x+'</th>').join('')+'</tr></thead><tbody>'+ev.map(e=>'<tr><td>'+esc(e.ticker)+'</td><td>'+esc(KIND[e.kind]||e.kind)+'</td><td>'+dm(e.data_com)+'</td><td>'+(e.payment_date?dm(e.payment_date):'a definir')+'</td><td>'+unit(e.value_per_share)+'</td><td>'+esc(e.quantity)+(e.estimate?'<small>estimada</small>':'')+'</td><td>'+money(e.net)+'</td><td>'+esc(SITU[e.state]||e.state)+'</td></tr>').join('')+'</tbody></table></div>';
      const at=d.fetched_at?new Date(d.fetched_at).toLocaleString('pt-BR',{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'}).replace(',',''):null;
      el('div-note').textContent='Fonte: B3 (proventos em dinheiro), '+(at?'consultada em '+at:'consulta ainda não registrada')+'. Elegibilidade pela posição na data-com; JCP líquido de 15% de IR; o valor entra no caixa só na data de pagamento (DP-30).';
    }catch(e){if(e.name!=='AbortError'&&v===divRev){status.textContent='Proventos indisponíveis. Nenhum valor foi estimado.';}}
  }
  function walletsLoaded(wallets,id){
    selected=id||selected||wallets[0]?.id||'';
    if(!wallets.some(w=>w.id===selected))selected=wallets[0]?.id||'';
    picker.innerHTML=wallets.length?wallets.map(w=>`<option value="${esc(w.id)}">${esc(w.name)}</option>`).join(''):'<option value="">Nenhuma carteira</option>';
    picker.value=selected;picker.disabled=!wallets.length;
    el('product-nature').textContent=wallets.find(w=>w.id===selected)?.nature_label||'';
    carry(selected);
    if(el('product-comparison')){
      compare(wallets,selected);
    }
    if(el('div-tiles')&&view==='dividends')dividends(selected);
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
    if(subtitles[view])el('personal-subtitle').textContent=subtitles[view];
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
      // aria-current belongs to the cycle view (radar-analysis.js): the step that needs attention.
      if(currentStage&&currentStage!==name)window.dispatchEvent(new CustomEvent('hfl:analysis-stage',{detail:name}));
      currentStage=name;
    }
    window.addEventListener('hashchange',stage);stage();
  }
  // DP-31: rule backtest, read-only GET. Server computes everything; this only renders it.
  (()=>{
    const form=el('lab-bt-form');if(!form)return;
    const pct=(v,d=1)=>v==null?'—':(v*100).toLocaleString('pt-BR',{minimumFractionDigits:d,maximumFractionDigits:d})+'%';
    const num=v=>v==null?'—':v.toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2});
    const dmy=d=>d.split('-').reverse().join('/');
    const boxes=[...form.querySelectorAll('input[name=t]')],ws=[...form.querySelectorAll('.lab-bt-w')];
    let chart,seq=0;
    const sync=()=>ws.forEach((w,i)=>{w.hidden=form.mode.value!=='custom'||!boxes[i].checked;});
    form.mode.addEventListener('change',sync);boxes.forEach(b=>b.addEventListener('change',sync));
    fetch('/api/platform/market-base',{cache:'no-store'}).then(r=>r.json()).then(d=>{
      if(!d.closed||form.end.value)return;
      form.end.value=d.closed;form.end.max=d.closed;
      const s=new Date(d.closed+'T00:00:00Z');s.setUTCFullYear(s.getUTCFullYear()-10);form.start.value=s.toISOString().slice(0,10);
    }).catch(()=>{});
    const fail=m=>{const e=el('lab-bt-error');e.textContent=m;e.hidden=false;el('lab-bt-result').hidden=true;};
    form.addEventListener('submit',async ev=>{
      ev.preventDefault();el('lab-bt-error').hidden=true;
      const q=new URLSearchParams(),on=boxes.filter(b=>b.checked);
      if(!on.length)return fail('Escolha ao menos um ativo.');
      q.set('tickers',on.map(b=>b.value).join(','));
      if(form.mode.value==='custom'){
        const w=on.map(b=>Number(ws[boxes.indexOf(b)].value));
        if(Math.abs(w.reduce((a,b)=>a+b,0)-100)>0.01)return fail('Os pesos devem somar 100%.');
        q.set('weights',w.map(x=>x/100).join(','));
      }
      for(const k of ['start','end','rebalance','cost_bps'])q.set(k,form[k].value);
      const mine=++seq;el('lab-bt-status').textContent='Simulando…';
      try{
        const r=await fetch('/api/lab/backtest?'+q,{cache:'no-store'}),d=await r.json();
        if(mine!==seq)return;
        if(!r.ok)return fail(d.error||'Simulação indisponível.');
        render(d);
      }catch{if(mine===seq)fail('Simulação indisponível. Nada foi alterado.');}
      finally{if(mine===seq)el('lab-bt-status').textContent='';}
    });
    function render(d){
      const cap=d.params.capital,cum=a=>a&&a.map(v=>(v-1)*100),st=d.strategy.map(v=>(v/cap-1)*100),ib=cum(d.ibov),cd=cum(d.cdi);
      const sets=[{label:'Estratégia',data:st,borderColor:'#3358d4',backgroundColor:'transparent',borderWidth:2,pointRadius:0,tension:0}];
      if(ib)sets.push({label:'Ibovespa (referência)',data:ib,borderColor:'#58647b',backgroundColor:'transparent',borderWidth:2,borderDash:[6,4],pointRadius:0,tension:0});
      if(cd)sets.push({label:'CDI (referência)',data:cd,borderColor:'#85570c',backgroundColor:'transparent',borderWidth:2,borderDash:[2,3],pointRadius:0,tension:0});
      el('lab-bt-result').hidden=false;
      chart?.destroy();
      chart=new Chart(el('lab-bt-chart'),{type:'line',data:{labels:d.sessions.map(dmy),datasets:sets},options:{responsive:true,maintainAspectRatio:false,animation:false,interaction:{mode:'index',intersect:false},plugins:{legend:{labels:{color:'#43516a',boxWidth:12,generateLabels:c=>Chart.defaults.plugins.legend.labels.generateLabels(c).map(l=>({...l,fillStyle:'transparent'}))}},tooltip:{callbacks:{label:c=>c.dataset.label+': '+num(c.raw)+'%'}}},scales:{x:{grid:{display:false},ticks:{color:'#657188',maxTicksLimit:7,maxRotation:0}},y:{grid:{color:'#e2e7f0'},ticks:{color:'#657188',callback:v=>v+'%'}}}}});
      const M=d.metrics,s=M.strategy,i=M.ibov,c=M.cdi;
      const row=(n,f)=>'<tr><th scope="row">'+n+'</th><td class="num">'+f(s)+'</td><td class="num">'+(i?f(i):'—')+'</td><td class="num">'+(c?f(c):'—')+'</td></tr>';
      const only=(n,v)=>'<tr><th scope="row">'+n+'</th><td class="num">'+v+'</td><td class="num">—</td><td class="num">—</td></tr>';
      const dd=x=>pct(x.max_drawdown)+' ('+dmy(x.max_drawdown_peak)+' → '+dmy(x.max_drawdown_trough)+')';
      el('lab-bt-metrics').innerHTML='<div class="ds-table-wrap"><table class="ds-table"><caption class="ds-visually-hidden">Métricas da simulação</caption><thead><tr><th scope="col">Métrica</th><th scope="col" class="num">Estratégia</th><th scope="col" class="num">Ibovespa</th><th scope="col" class="num">CDI</th></tr></thead><tbody>'
        +row('Retorno total',x=>pct(x.total_return))+row('Retorno anualizado',x=>pct(x.annualized_return))+row('Volatilidade anualizada',x=>pct(x.annualized_volatility))+row('Queda máxima',dd)+row('Sharpe (CDI)',x=>x.sharpe==null?'—':num(x.sharpe))
        +only('Rebalanceamentos',s.rebalances)+only('Custos totais',money(s.total_costs))+only('Giro (negociado ÷ patrimônio médio)',num(s.turnover)+'×')+'</tbody></table></div>';
      const stale=Object.entries(d.stale_days).filter(([,n])=>n).map(([t,n])=>t+': '+n+' dia(s) sem negócio, último preço mantido');
      const miss=Object.values(M.unavailable).map(x=>'Referência indisponível: '+x);
      el('lab-bt-notes').innerHTML=[...d.data_notes,...stale,...miss].map(n=>'<li>'+esc(n)+'</li>').join('');
      el('lab-bt-table').innerHTML='<div class="ds-table-wrap"><table class="ds-table"><caption class="ds-visually-hidden">Retorno acumulado por pregão</caption><thead><tr><th scope="col">Data</th><th scope="col" class="num">Estratégia</th><th scope="col" class="num">Ibovespa</th><th scope="col" class="num">CDI</th></tr></thead><tbody>'
        +d.sessions.map((x,k)=>'<tr><td>'+dmy(x)+'</td><td class="num">'+num(st[k])+'%</td><td class="num">'+(ib?num(ib[k])+'%':'—')+'</td><td class="num">'+(cd?num(cd[k])+'%':'—')+'</td></tr>').join('')+'</tbody></table></div>';
    }
  })();
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
