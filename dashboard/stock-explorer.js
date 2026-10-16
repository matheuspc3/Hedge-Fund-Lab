'use strict';
(() => {
  const el=id=>document.getElementById(id);
  if(!el('personal-stock-chart')||location.pathname!=='/'||new URLSearchParams(location.search).get('demo')==='1'||location.hash==='#audit')return;
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const day=v=>v?.split('-').reverse().join('/')||'—';
  // Intraday stamps are "YYYY-MM-DD HH:MM"; a bare date among them marks a session without bars.
  const when=v=>v?.length>10?day(v.slice(0,10))+' '+v.slice(11):day(v);
  const money=v=>v==null?'Indisponível':Number(v).toLocaleString('pt-BR',{style:'currency',currency:'BRL'});
  const percent=v=>(v>=0?'+':'')+v.toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2})+'%';
  const colors=['#3358d4','#16846e','#8757b4','#b07215','#ca5279'];
  const BAR_NAMES={'1m':'1 min','5m':'5 min','15m':'15 min','1h':'1 hora'}, BAR_ORDER=['1m','5m','15m','1h'];
  let wallet='', source, csrf, chart, version=0, controller, refreshing=false, selected=new Set(), period='1y', rows=[], selection=null, drag=null;
  let intraday=null, loadingIntraday='', collecting=false, issue='', bars=null;
  const symbols=()=>source?.tickers.filter(t=>selected.has(t))||[];
  const color=t=>colors[source.tickers.indexOf(t)%colors.length];
  const basis=()=>el('personal-stock-basis').value;
  const price=(row,t)=>row?.values[t]??null;
  function error(message=''){el('personal-stock-error').textContent=message;el('personal-stock-error').hidden=!message;}
  function dates(){return [...new Set(symbols().flatMap(t=>(source.series[t]?.rows||[]).map(r=>r.date)))].sort();}
  const sessionsIn=(start,end)=>[...dates(),...(source?.today?[source.today]:[])].filter(d=>(!start||d>=start)&&(!end||d<=end));
  // ponytail: about 400 points per series at most; longer ranges, and the dividend-adjusted series, stay daily.
  function resolution(start,end){
    if(basis()!=='close')return null;
    const n=sessionsIn(start,end).length;
    return n<=1?'1m':n<=5?'5m':n<=15?'15m':n<=60?'1h':null;
  }
  async function fetchIntraday(key,start,end,interval){
    el('personal-stock-note').textContent='Carregando barras intradiárias…';
    if(loadingIntraday===key)return;
    loadingIntraday=key;const current=version;
    try{
      const r=await fetch('/api/portfolio/stock-history/intraday?'+new URLSearchParams({wallet,from:start,to:end,interval}),{cache:'no-store'}),d=await r.json();
      if(current!==version||loadingIntraday!==key)return;
      if(!r.ok||d.identity!=='HFL-STOCK-INTRADAY-YAHOO-V1'||d.wallet!==wallet)throw Error();
      intraday={key,data:d};
    }catch{if(current!==version||loadingIntraday!==key)return;intraday={key,data:{series:{},live:{},errors:{},failed:true}};}
    loadingIntraday='';draw();
  }
  async function collect(){
    if(!wallet||!csrf||collecting)return;
    collecting=true;const id=wallet;
    try{
      const r=await fetch('/api/portfolio/stock-history/intraday/refresh',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:JSON.stringify({wallet:id})}),d=await r.json();
      if(!r.ok)throw Error();
      issue=Object.entries(d.refresh_errors||{}).map(([t,e])=>t+': '+e).join(' ');
    }catch{issue='Não foi possível atualizar as barras intradiárias agora; o acervo local foi preservado.';}
    finally{collecting=false;}
    if(id===wallet&&source){intraday=null;if(drag==null)draw();}
  }
  function setPeriod(next){
    period=next;const all=dates();if(!all.length){draw();return;}
    const sessions=source.today&&['1d','5d','1mo'].includes(next)?[...all,source.today]:all;
    const end=sessions.at(-1), from=new Date(end+'T12:00:00Z');
    if(next==='1mo'||next==='6mo'){
      const original=from.getUTCDate();from.setUTCDate(1);from.setUTCMonth(from.getUTCMonth()-(next==='1mo'?1:6));
      const last=new Date(Date.UTC(from.getUTCFullYear(),from.getUTCMonth()+1,0)).getUTCDate();from.setUTCDate(Math.min(original,last));
    }else if(next==='1y'||next==='5y'){
      const month=from.getUTCMonth();from.setUTCFullYear(from.getUTCFullYear()-(next==='1y'?1:5));if(from.getUTCMonth()!==month)from.setUTCDate(0);
    }else if(next==='ytd'){from.setUTCMonth(0,1);}
    el('personal-stock-from').value=next==='max'?all[0]:next==='1d'?end:next==='5d'?sessions.slice(-5)[0]:from.toISOString().slice(0,10);
    el('personal-stock-to').value=end;selection=null;draw();
  }
  function assets(){
    el('personal-stock-assets').innerHTML=source.tickers.map(t=>`<label><input type="checkbox" value="${esc(t)}" ${selected.has(t)?'checked':''}><span style="color:${color(t)}">●</span>${esc(t)}</label>`).join('');
    el('personal-stock-all').textContent=selected.size===source.tickers.length?'Limpar ações':'Selecionar todas';
  }
  function summary(){
    const start=selection?Math.min(...selection):0, end=selection?Math.max(...selection):rows.length-1;
    const a=rows[start],z=rows[end];
    el('personal-stock-clear').hidden=!selection;
    el('personal-stock-interval').textContent=a&&z?`${selection?'Intervalo selecionado':'Período exibido'} · ${when(a.date)} → ${when(z.date)} · ${rows.length} ${bars?'barras':'sessões'} no gráfico`:'Selecione ações e um período com dados.';
    el('personal-stock-summary').innerHTML=symbols().map(t=>{
      const first=price(a,t),last=price(z,t),valid=first!=null&&last!=null;
      const delta=valid?last-first:null,change=valid?(last/first-1)*100:null;
      return `<article style="--series-color:${color(t)}"><span>${esc(t)}</span><strong>${money(last)}</strong>${valid?`<span class="${delta>=0?'stock-positive':'stock-negative'}">${delta>=0?'+':''}${money(delta)} (${percent(change)})</span><small>${money(first)} → ${money(last)}</small>`:'<small>Falta preço em uma das datas selecionadas.</small>'}</article>`;
    }).join('');
  }
  function table(){
    if(!el('personal-stock-details').open){el('personal-stock-table').textContent='Abra para consultar os valores do período.';return;}
    const tickers=symbols();
    el('personal-stock-table').innerHTML='<div class="ds-table-wrap" tabindex="0" role="region" aria-label="Preços históricos Yahoo"><table class="ds-table"><thead><tr><th scope="col">Data</th>'+tickers.map(t=>'<th scope="col">'+esc(t)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr><td>'+when(r.date)+'</td>'+tickers.map(t=>'<td>'+money(price(r,t))+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';
  }
  const selectionPlugin={id:'stockInterval',afterDatasetsDraw(c){
    if(!selection||!rows.length)return;
    const [a,z]=[Math.min(...selection),Math.max(...selection)],ctx=c.ctx,area=c.chartArea,x=c.scales.x;
    const left=x.getPixelForValue(a),right=x.getPixelForValue(z);
    ctx.save();ctx.fillStyle='#3358d41a';ctx.fillRect(left,area.top,right-left,area.bottom-area.top);
    ctx.strokeStyle='#3358d4';ctx.lineWidth=1;ctx.setLineDash([4,3]);
    for(const px of [left,right]){ctx.beginPath();ctx.moveTo(px,area.top);ctx.lineTo(px,area.bottom);ctx.stroke();}ctx.restore();
  }};
  function draw(){
    chart?.destroy();chart=null;rows=[];bars=null;error();
    el('personal-stock-wrap').hidden=true;
    document.querySelectorAll('[data-stock-period]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.stockPeriod===period)));
    const start=el('personal-stock-from').value,end=el('personal-stock-to').value;
    if(start&&end&&start>end){error('A data inicial deve ser anterior ou igual à final.');summary();table();return;}
    const tickers=symbols(), field=basis();
    if(!tickers.length){el('personal-stock-note').textContent='Selecione pelo menos uma ação para explorar o histórico.';summary();table();return;}
    const wanted=resolution(start,end), key=[wallet,start,end,wanted].join('|');
    if(wanted&&intraday?.key!==key){fetchIntraday(key,start,end,wanted);return;}
    const found=wanted&&tickers.some(t=>intraday.data.series[t]?.rows.some(r=>r[1]!=null))?intraday.data:null;
    let missing=[];
    if(found){
      bars=wanted;
      const maps=Object.fromEntries(tickers.map(t=>[t,new Map(found.series[t]?.rows||[])]));
      missing=sessionsIn(start,end).filter(d=>!tickers.some(t=>found.series[t]?.resolution[d]));
      const stamps=[...new Set([...tickers.flatMap(t=>[...maps[t].keys()]),...missing])].sort();
      rows=stamps.map(date=>({date,values:Object.fromEntries(tickers.map(t=>[t,maps[t].get(date)??null]))}));
    }else{
      const days=dates().filter(d=>(!start||d>=start)&&(!end||d<=end));
      const maps=Object.fromEntries(tickers.map(t=>[t,new Map((source.series[t]?.rows||[]).map(r=>[r.date,r[field]]))]));
      rows=days.map(date=>({date,values:Object.fromEntries(tickers.map(t=>[t,maps[t].get(date)??null]))}));
    }
    summary();table();
    const snapshots=tickers.map(t=>source.series[t]).filter(Boolean);
    const gaps=rows.filter(r=>tickers.some(t=>price(r,t)==null)).length;
    if(found){
      const used=new Set(tickers.flatMap(t=>Object.values(found.series[t]?.resolution||{})));
      const coarser=BAR_ORDER.filter(b=>used.has(b)&&BAR_ORDER.indexOf(b)>BAR_ORDER.indexOf(wanted));
      const live=Object.values(found.live||{})[0];
      el('personal-stock-note').textContent=`Yahoo Finance · intradiário · barras de ${BAR_NAMES[wanted]}${coarser.length?' (dias antigos só existem em '+coarser.map(b=>BAR_NAMES[b]).join(' / ')+')':''} · preço sem ajuste · ${rows.length} barras${gaps?' · '+gaps+' com lacunas':''}${missing.length?' · '+missing.length+' pregão(ões) sem barras guardadas':''}${live?.last_bar?` · hoje: última barra ${live.last_bar}, consultada às ${new Date(live.fetched_at).toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'})}; o Yahoo atrasa cerca de 15 min`:''}. Uso exploratório; não altera o patrimônio da carteira.${issue?' '+issue:''}`;
    }else el('personal-stock-note').textContent=(wanted?(intraday?.data.failed?'Barras intradiárias indisponíveis agora; mostrando o diário. ':'Sem barras intradiárias guardadas neste período; mostrando o diário. '):'')+(snapshots.length?`Yahoo Finance · diário · ${field==='close'?'fechamento ajustado por desdobramentos, sem ajuste adicional por proventos':'fechamento ajustado por proventos e desdobramentos'} · ${rows.length} sessões exibidas${gaps?' · '+gaps+' com lacunas':''}. Cópia local atualizada em ${new Date(snapshots.map(s=>s.fetched_at).sort()[0]).toLocaleString('pt-BR')}. Uso exploratório; não altera o patrimônio da carteira.`:'Sem histórico local para as ações selecionadas. Use Atualizar histórico Yahoo.');
    const failures={...source?.errors,...source?.refresh_errors,...(found?.errors||{})};
    if(Object.keys(failures).length)error(Object.entries(failures).map(([t,e])=>t+': '+e).join(' '));
    if(!rows.some(r=>tickers.some(t=>price(r,t)!=null)))return;
    const normalized=el('personal-stock-mode').value==='change';
    const settings={responsive:true,maintainAspectRatio:false,animation:false,interaction:{mode:'index',intersect:false},plugins:{legend:{display:false},tooltip:{callbacks:{title:c=>when(rows[c[0]?.dataIndex]?.date),label:c=>c.dataset.label+': '+(normalized?percent(c.raw):money(c.raw))}}},scales:{x:{grid:{display:false},ticks:{maxTicksLimit:8,maxRotation:0,color:'#657188'}},y:{grid:{color:'#e2e7f0'},ticks:{color:'#657188',callback:v=>normalized?v+'%':money(v)}}}};
    el('personal-stock-wrap').hidden=false;
    chart=new Chart(el('personal-stock-chart'),{type:'line',plugins:[selectionPlugin],data:{labels:rows.map(r=>!bars||r.date.length===10?day(r.date):start===end?r.date.slice(11):day(r.date.slice(0,10)).slice(0,5)+' '+r.date.slice(11)),datasets:tickers.map(t=>{
      const anchor=price(rows[0],t);
      return {label:t,data:rows.map(r=>{const v=price(r,t);return v==null?null:normalized?(anchor==null?null:(v/anchor-1)*100):v;}),borderColor:color(t),backgroundColor:color(t)+'12',borderWidth:2,pointRadius:rows.length<40?3:0,pointHoverRadius:5,spanGaps:false,tension:0,fill:tickers.length===1};
    })},options:settings});
    if(normalized&&tickers.some(t=>price(rows[0],t)==null))el('personal-stock-note').textContent+=' A série percentual exige preço no primeiro dia exibido; escolha outra data inicial para ativos sem esse preço.';
  }
  function accept(d){
    source=d;csrf=d.csrf_token||csrf;
    selected=new Set([...selected].filter(t=>d.tickers.includes(t)));
    if(!selected.size&&d.tickers.length)selected.add(d.tickers.includes('PETR4')?'PETR4':d.tickers[0]);
    assets();if(period)setPeriod(period);else {selection=null;draw();}
  }
  async function load(catalog){
    wallet=catalog.selected||'';const current=++version;
    controller?.abort();controller=new AbortController();chart?.destroy();chart=null;source=null;selection=drag=null;intraday=null;loadingIntraday='';issue='';
    el('personal-stock-wrap').hidden=true;el('personal-stock-summary').textContent='';el('personal-stock-table').textContent='';el('personal-stock-interval').textContent='';error();
    el('personal-stock-note').textContent='Conferindo histórico local…';
    if(!wallet){el('personal-stock-note').textContent='Crie ou selecione uma carteira.';return;}
    try{
      const r=await fetch('/api/portfolio/stock-history?'+new URLSearchParams({wallet}),{cache:'no-store',signal:controller.signal}),d=await r.json();
      if(current!==version)return;
      if(!r.ok||d.wallet!==wallet||d.identity!=='HFL-STOCK-EXPLORER-YAHOO-V1')throw Error('Não foi possível conferir o histórico local. Atualize a consulta.');
      accept(d);collect();
    }catch(e){if(e.name!=='AbortError'&&current===version){error(e.message);el('personal-stock-note').textContent='Histórico indisponível.';}}
  }
  el('personal-stock-assets').addEventListener('change',e=>{if(!source)return;e.target.checked?selected.add(e.target.value):selected.delete(e.target.value);selection=null;el('personal-stock-all').textContent=selected.size===source.tickers.length?'Limpar ações':'Selecionar todas';if(period)setPeriod(period);else draw();});
  el('personal-stock-all').addEventListener('click',()=>{if(!source)return;selected=selected.size===source.tickers.length?new Set():new Set(source.tickers);assets();selection=null;if(period)setPeriod(period);else draw();});
  document.querySelectorAll('[data-stock-period]').forEach(b=>b.addEventListener('click',()=>{if(source)setPeriod(b.dataset.stockPeriod);}));
  el('personal-stock-range').addEventListener('submit',e=>{e.preventDefault();if(source){period='';selection=null;draw();}});
  for(const id of ['personal-stock-mode','personal-stock-basis'])el(id).addEventListener('change',()=>{if(source){selection=null;draw();}});
  el('personal-stock-clear').addEventListener('click',()=>{selection=null;summary();chart?.draw();});
  el('personal-stock-details').addEventListener('toggle',table);
  const canvas=el('personal-stock-chart');
  function point(e){
    if(!chart||!rows.length)return null;
    const r=canvas.getBoundingClientRect(),x=(e.clientX-r.left)*chart.width/r.width,y=(e.clientY-r.top)*chart.height/r.height,a=chart.chartArea;
    if(drag==null&&(x<a.left||x>a.right||y<a.top||y>a.bottom))return null;
    return Math.max(0,Math.min(rows.length-1,Math.round(chart.scales.x.getValueForPixel(x))));
  }
  canvas.addEventListener('pointerdown',e=>{if(e.button!==0)return;const i=point(e);if(i==null)return;drag=i;selection=[i,i];canvas.setPointerCapture(e.pointerId);if(e.pointerType==='mouse')e.preventDefault();summary();chart.draw();});
  canvas.addEventListener('pointermove',e=>{if(drag==null)return;const i=point(e);if(i==null)return;selection=[drag,i];summary();chart.draw();});
  canvas.addEventListener('pointerup',e=>{if(drag==null)return;drag=null;if(canvas.hasPointerCapture(e.pointerId))canvas.releasePointerCapture(e.pointerId);summary();chart?.draw();});
  canvas.addEventListener('pointercancel',()=>{drag=null;selection=null;summary();chart?.draw();});
  el('personal-stock-refresh').addEventListener('click',async()=>{
    if(!wallet||!csrf||refreshing)return;
    const current=version,id=wallet,button=el('personal-stock-refresh');refreshing=true;button.disabled=true;button.textContent='Buscando histórico máximo…';error();
    try{
      const r=await fetch('/api/portfolio/stock-history/refresh',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:JSON.stringify({wallet:id})}),d=await r.json();
      if(current!==version)return;
      if(!r.ok||d.wallet!==id)throw Error(d.error==='stock_history_refresh_already_running'?'Já existe uma atualização em andamento. Aguarde e atualize a consulta.':'Não foi possível atualizar. A cópia anterior foi preservada.');
      accept(d);await collect();if(current===version&&issue)error(issue);
    }catch(e){if(current===version)error(e.message);}
    finally{refreshing=false;button.disabled=false;button.textContent='Atualizar histórico Yahoo';}
  });
  // ponytail: a 2-min poll only while the range reaches the open session and the tab is visible;
  // Yahoo's ~15 min delay makes faster polling pointless.
  setInterval(()=>{if(source?.today&&el('personal-stock-to').value>=source.today&&document.visibilityState==='visible'&&drag==null&&!refreshing)collect();},120000);
  window.addEventListener('hfl:wallets',e=>load(e.detail));
  if(window.HFLPersonalCatalog)load(window.HFLPersonalCatalog);
})();
