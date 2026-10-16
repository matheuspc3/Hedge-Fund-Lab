'use strict';
(() => {
  const el=id=>document.getElementById(id);
  if(!el('personal-equity-chart')||location.pathname!=='/'||new URLSearchParams(location.search).get('demo')==='1'||location.hash==='#audit')return;
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const money=v=>v==null?'Indisponível':Number(v).toLocaleString('pt-BR',{style:'currency',currency:'BRL'});
  const day=v=>v?v.split('-').reverse().join('/'):'Sem referência';
  const pct=v=>v==null?'Indisponível':(Number(v)*100).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2})+'%';
  const colors=['#3358d4','#16846e','#8757b4','#b07215','#ca5279'];
  let revision=0, controller, equityChart;
  function table(headers,rows){return '<div class="ds-table-wrap" tabindex="0" role="region" aria-label="'+esc(headers.join(', '))+'"><table class="ds-table"><thead><tr>'+headers.map(h=>'<th scope="col">'+esc(h)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+r.map(c=>'<td>'+c+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';}
  function options(currency=true){return {responsive:true,maintainAspectRatio:false,animation:false,interaction:{mode:'index',intersect:false},plugins:{legend:{labels:{color:'#43516a',boxWidth:12}},tooltip:{callbacks:{label:c=>c.dataset.label+': '+(c.raw==null?'Indisponível':currency?money(c.raw):Number(c.raw).toLocaleString('pt-BR',{maximumFractionDigits:2})+'%')}}},scales:{x:{grid:{display:false},ticks:{color:'#657188',maxTicksLimit:7,maxRotation:0}},y:{grid:{color:'#e2e7f0'},ticks:{color:'#657188',callback:v=>currency?money(v):v+'%'}}}};}
  function clear(){equityChart?.destroy();equityChart=null;el('personal-equity-wrap').hidden=true;el('personal-equity-table').textContent='Conferindo histórico…';}
  function render(d){
    const v=d.valuation, first=el('personal-metrics').querySelector('.ds-kpi');
    if(first&&v.equity!=null){
      first.querySelector('.ds-kpi-label').textContent='Patrimônio estimado';
      first.querySelector('.ds-kpi-value').textContent=money(v.equity);
      first.querySelector('.ds-kpi-detail').textContent=(v.positions.length?'Posições atuais · fechamento de '+day(v.price_session):'Carteira em caixa')+' · desde o início: '+money(v.change)+' ('+pct(v.return_fraction)+')';
    }
    el('personal-positions').innerHTML=table(['Ativo','Quantidade','Custo médio','Custo total','Fechamento RAW / data','Valor estimado'],v.positions.map(p=>[esc(p.ticker),esc(p.quantity),money(p.average_cost),money(p.basis),p.reference_price==null?'Indisponível':money(p.reference_price)+'<small>'+day(p.price_session)+'</small>',money(p.market_value)]));
    const known=d.daily_history.filter(p=>p.equity!=null).length;
    el('personal-prices').textContent=`${known} fechamento(s) calculado(s). Posições e caixa de cada data, com as correções atuais.`+(d.initial_anchor_available?' O ponto inicial representa o capital cadastrado em '+day(d.start_date)+'.':' O início da carteira está fora da cobertura do calendário; o histórico exibido é parcial.')+(d.daily_history.some(p=>p.equity==null)?' Há datas sem fechamento: a linha permanece interrompida.':'')+' Proventos e eventos não registrados ainda não entram no patrimônio.';
    const labels=[],values=[];
    if(d.initial_anchor_available){labels.push('Início · '+day(d.start_date));values.push(Number(d.initial_capital));}
    for(const p of d.daily_history){labels.push(day(p.session));values.push(p.equity==null?null:Number(p.equity));}
    el('personal-equity-wrap').hidden=!values.some(v=>v!=null);
    equityChart?.destroy();
    if(values.some(v=>v!=null))equityChart=new Chart(el('personal-equity-chart'),{type:'line',data:{labels,datasets:[{label:d.wallet_name,data:values,borderColor:colors[0],backgroundColor:'#3358d412',borderWidth:2.5,pointRadius:4,spanGaps:false,fill:true,tension:0}]},options:options()});
    el('personal-equity-table').innerHTML=table(['Data / marco','Patrimônio','Caixa registrado','Estado'],[...(d.initial_anchor_available?[['Início · '+day(d.start_date),money(d.initial_capital),money(d.initial_capital),'Capital inicial, antes das operações']]:[]),...d.daily_history.map(p=>[day(p.session),money(p.equity),money(p.cash),esc({AVAILABLE:'Fechamento disponível',PENDING_CLOSE:'Fechamento pendente',MISSING_QUOTES:'Faltam cotações: '+p.missing.join(', ')}[p.state])])]);

  }
  async function load(catalog){
    const selected=catalog.wallets.find(w=>w.id===catalog.selected), version=++revision;
    controller?.abort();controller=new AbortController();clear();el('personal-chart-error').hidden=true;
    if(!selected){el('personal-prices').textContent='Crie ou selecione uma carteira para acompanhar a evolução.';return;}
    el('personal-prices').textContent='Conferindo posições históricas e fechamentos RAW…';
    try{
      const response=await fetch('/api/portfolio/history?'+new URLSearchParams({wallet:selected.id}),{cache:'no-store',signal:controller.signal});
      const d=await response.json();if(version!==revision)return;
      if(!response.ok||d.wallet!==selected.id||d.wallet_revision!==selected.revision||d.read_only!==true)throw Error('A carteira mudou ou o histórico não pôde ser verificado. Use Atualizar consulta.');
      render(d);
    }catch(e){if(e.name==='AbortError'||version!==revision)return;el('personal-chart-error').textContent=e.message;el('personal-chart-error').hidden=false;el('personal-prices').textContent='Histórico indisponível. Nenhum preço foi estimado para preencher lacunas.';}
  }
  window.addEventListener('hfl:wallets',e=>load(e.detail));
  if(window.HFLPersonalCatalog)load(window.HFLPersonalCatalog);
})();
