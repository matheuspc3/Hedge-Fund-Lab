'use strict';
(() => {
  const el=id=>document.getElementById(id);
  if(!el('personal-equity-chart')||location.pathname!=='/'||new URLSearchParams(location.search).get('demo')==='1'||location.hash==='#audit')return;
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const money=v=>v==null?'Indisponível':Number(v).toLocaleString('pt-BR',{style:'currency',currency:'BRL'});
  const day=v=>v?v.split('-').reverse().join('/'):'Sem referência';
  const pct=v=>v==null?'Indisponível':(Number(v)*100).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2})+'%';
  const origin=x=>({MANAGER:'gestor',RULE:'regra automática'}[x.origin]||'manual');
  const colors=['#3358d4','#0f8a68','#8757b4','#b07215','#ca5279']; // dataviz validator: adjacent CVD ΔE ≥ 10, chroma ≥ 0.1
  let revision=0, controller, equityChart, allocChart, period, periodWallet; // period survives reloads of the same wallet (no storage)
  function table(headers,rows){return '<div class="ds-table-wrap" tabindex="0" role="region" aria-label="'+esc(headers.join(', '))+'"><table class="ds-table"><thead><tr>'+headers.map(h=>'<th scope="col">'+esc(h)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+r.map(c=>'<td>'+c+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';}
  function options(currency=true){return {responsive:true,maintainAspectRatio:false,animation:false,interaction:{mode:'index',intersect:false},plugins:{legend:{labels:{color:'#43516a',boxWidth:12}},tooltip:{callbacks:{label:c=>c.dataset.label+': '+(c.raw==null?'Indisponível':currency?money(c.raw):Number(c.raw).toLocaleString('pt-BR',{maximumFractionDigits:2})+'%')}}},scales:{x:{grid:{display:false},ticks:{color:'#657188',maxTicksLimit:7,maxRotation:0}},y:{grid:{color:'#e2e7f0'},ticks:{color:'#657188',callback:v=>currency?money(v):v+'%'}}}};}
  function clear(){equityChart?.destroy();equityChart=null;allocChart?.destroy();allocChart=null;el('personal-equity-wrap').hidden=true;el('personal-equity-table').textContent='Conferindo histórico…';el('personal-allocation').textContent='';}
  function render(d){
    const v=d.valuation, cards=el('personal-metrics').querySelectorAll('.ds-kpi');
    if(cards.length===3&&v.equity!=null){
      const w=window.HFLPersonalCatalog?.wallets.find(x=>x.id===d.wallet)||{}, share=x=>x==null?'':(Number(x)/Number(v.equity)*100).toLocaleString('pt-BR',{maximumFractionDigits:1})+'% do patrimônio';
      const by=Object.fromEntries(d.periods.map(p=>[p.key,p]));
      if(!by[period]||periodWallet!==d.wallet){period=by['1d']?.state==='AVAILABLE'?'1d':'inception';periodWallet=d.wallet;}
      const sgn=(f,x)=>(Number(x)>0?'+':'')+f(x);
      const line=()=>{const p=by[period];return p.label+': '+(p.state==='AVAILABLE'?sgn(money,p.change)+' ('+sgn(pct,p.return_fraction)+') · fechamentos '+day(p.anchor_session).slice(0,5)+' → '+day(p.end_session).slice(0,5):p.state==='INSUFFICIENT_HISTORY'?'histórico insuficiente — carteira iniciada em '+day(d.start_date).slice(0,5):'sem fechamento disponível');};
      cards[0].querySelector('.ds-kpi-label').textContent='Patrimônio estimado';
      cards[0].querySelector('.ds-kpi-value').textContent=money(v.equity);
      const detail=cards[0].querySelector('.ds-kpi-detail');
      detail.id='personal-period-detail';detail.setAttribute('aria-live','polite');detail.textContent=line();
      const group=document.createElement('div');group.className='stock-periods';group.setAttribute('role','group');group.setAttribute('aria-label','Período da variação');
      group.innerHTML=d.periods.map(p=>'<button type="button" data-period="'+esc(p.key)+'" aria-pressed="'+(p.key===period)+'">'+esc(p.label)+'</button>').join('');
      group.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;period=b.dataset.period;group.querySelectorAll('button').forEach(x=>x.setAttribute('aria-pressed',x===b));detail.textContent=line();});
      cards[0].querySelector('.stock-periods')?.remove();detail.before(group);
      // DP-30: cash shown includes dividends received (cash_available); without it the ledger cash is shown as before.
      const cash=v.cash_available??v.cash, got=Number(v.dividends_received)>0;
      cards[1].querySelector('.ds-kpi-value').textContent=money(cash);
      cards[1].querySelector('.ds-kpi-detail').textContent=[share(cash),got?'inclui '+money(v.dividends_received)+' de proventos recebidos':'','sem controle de liquidação'].filter(Boolean).join(' · ');
      cards[0].querySelector('#personal-receivable')?.remove();
      if(Number(v.dividends_receivable)>0)detail.insertAdjacentHTML('afterend','<div class="ds-kpi-detail" id="personal-receivable">A receber: '+money(v.dividends_receivable)+' (proventos)</div>');
      const inv=cards[2].querySelector('.ds-kpi-value'), idetail=cards[2].querySelector('.ds-kpi-detail');
      inv.textContent=v.invested_value==null?'Aguardando cotações':money(v.invested_value);
      idetail.textContent=(v.invested_value==null?'':share(v.invested_value)+' · fechamento de '+day(v.price_session)+' · ')+'Custos '+money(w.costs)+' · realizado '+money(w.realized_pnl);
    }
    // Allocation: weight = market_value / equity; null input stays "Indisponível", never 0%. Target marker only for pilot (grouped) wallets.
    const grouped=Boolean((window.HFLPersonalCatalog?.wallets.find(x=>x.id===d.wallet)||{}).comparison_group);
    const weight=x=>v.equity==null||x==null||!Number(v.equity)?null:Number(x)/Number(v.equity);
    allocChart?.destroy();allocChart=null;
    const items=[...v.positions.map((p,k)=>({n:p.ticker,w:weight(p.market_value),c:colors[k],t:grouped})),{n:'Caixa',w:weight(v.cash),c:'#d3d9e3',t:false}];
    // Pie order keeps the CVD-confusable pairs (pink/green, purple/blue) apart; cash is a light neutral, not a hue.
    // ponytail: more than 5 assets would cycle hues, so the pie is skipped (list only) until an "Outros" fold exists.
    const pie=v.positions.length<=colors.length&&items.every(x=>x.w!=null)&&items.some(x=>x.w>0);
    const pp=w=>{const x=(w-0.2)*100;return (x>0?'+':'')+x.toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2})+' p.p. vs 20%';};
    el('personal-allocation').innerHTML=v.positions.length||v.cash!=null?'<div class="alloc">'+(pie?'<div class="alloc-pie"><canvas id="personal-allocation-chart" role="img" aria-label="Distribuição do patrimônio por ativo e caixa; valores na lista ao lado"></canvas></div>':'')+'<ul class="alloc-list" aria-label="Peso de cada item no patrimônio">'+items.map(x=>'<li><i class="alloc-swatch" aria-hidden="true"'+(pie?' style="background:'+x.c+'"':'')+'></i><span>'+esc(x.n)+'</span><b>'+(x.w==null?'Indisponível':pct(x.w))+'</b><small>'+(x.t&&x.w!=null?pp(x.w):'')+'</small></li>').join('')+'</ul></div>'+(grouped?'<p class="product-note">Diferença em relação ao alvo inicial 20% por ativo. Pesos mudam com os preços.</p>':''):'';
    if(pie)allocChart=new Chart(el('personal-allocation-chart'),{type:'pie',data:{labels:items.map(x=>x.n),datasets:[{data:items.map(x=>x.w*100),backgroundColor:items.map(x=>x.c),borderColor:'#fff',borderWidth:2,hoverOffset:6}]},options:{responsive:true,maintainAspectRatio:false,animation:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>' '+c.label+': '+pct(items[c.dataIndex].w)}}}}});
    el('personal-positions').innerHTML=table(['Ativo','Quantidade','Custo médio','Custo total','Fechamento RAW / data','Valor estimado'],v.positions.map(p=>[esc(p.ticker),esc(p.quantity),money(p.average_cost),money(p.basis),p.reference_price==null?'Indisponível':money(p.reference_price)+'<small>'+day(p.price_session)+'</small>',money(p.market_value)]));
    const known=d.daily_history.filter(p=>p.equity!=null).length;
    el('personal-prices').textContent=`${known} fechamento(s) calculado(s). Posições e caixa de cada data, com as correções atuais.`+(d.initial_anchor_available?' O ponto inicial representa o capital cadastrado em '+day(d.start_date)+'.':' O início da carteira está fora da cobertura do calendário; o histórico exibido é parcial.')+(d.daily_history.some(p=>p.equity==null)?' Há datas sem fechamento: a linha permanece interrompida.':'')+(d.dividends?' Proventos recebidos e a receber (B3) entram no patrimônio; eventos não registrados não.':' Integração de proventos indisponível: proventos e eventos não registrados não entram no patrimônio.');
    const labels=[],values=[];
    if(d.initial_anchor_available){labels.push('Início · '+day(d.start_date));values.push(Number(d.initial_capital));}
    for(const p of d.daily_history){labels.push(day(p.session));values.push(p.equity==null?null:Number(p.equity));}
    el('personal-equity-wrap').hidden=!values.some(v=>v!=null);
    equityChart?.destroy();
    const off=d.initial_anchor_available?1:0, ops=d.daily_history.map(p=>{const t=p.trades||[], l=t.slice(0,4).map(x=>({BUY:'Compra',SELL:'Venda'}[x.side]||x.side)+' '+x.quantity+' '+x.ticker+' · '+origin(x));return t.length>4?[...l,'e mais '+(t.length-4)]:l;});
    const marked=i=>ops[i-off]?.length>0, opts=options();
    opts.plugins.tooltip.callbacks.footer=items=>ops[items[0].dataIndex-off]||[]; // ponytail: ops are text-only; chart marks days, table lists them
    if(values.some(v=>v!=null))equityChart=new Chart(el('personal-equity-chart'),{type:'line',data:{labels,datasets:[{label:d.wallet_name,data:values,borderColor:colors[0],backgroundColor:'#3358d412',borderWidth:2.5,pointRadius:labels.map((_,i)=>marked(i)?8:4),pointStyle:labels.map((_,i)=>marked(i)?'rectRot':'circle'),spanGaps:false,fill:true,tension:0}]},options:opts});
    const hasDiv=d.daily_history.some(p=>p.dividends_received!=null);
    el('personal-equity-table').innerHTML=table(['Data / marco','Patrimônio',...(hasDiv?['Proventos (recebidos + a receber)']:[]),'Caixa registrado','Estado','Operações'],[...(d.initial_anchor_available?[['Início · '+day(d.start_date),money(d.initial_capital),...(hasDiv?['—']:[]),money(d.initial_capital),'Capital inicial, antes das operações','—']]:[]),...d.daily_history.map((p,i)=>[day(p.session),money(p.equity),...(hasDiv?[p.dividends_received==null||p.dividends_receivable==null?'Indisponível':money(Number(p.dividends_received)+Number(p.dividends_receivable))]:[]),money(p.cash),esc({AVAILABLE:'Fechamento disponível',PENDING_CLOSE:'Fechamento pendente',MISSING_QUOTES:'Faltam cotações: '+p.missing.join(', ')}[p.state]),ops[i].length?esc(ops[i].join('; ')):'—'])]);

  }
  // Rotina do dia: read-only links and text; nothing here infers, pays or writes.
  const STATUS={PREPARED:'Análise preparada, aguardando execução',RUNNING:'Análise em execução',VALID_PROPOSAL:'Proposta pronta, aguardando sua aprovação',RECOVERY_OR_REVIEW_REQUIRED:'Análise precisa de revisão',CLAIMED_RECOVERY_ONLY:'Recuperação pendente',INTEGRITY_ERROR:'Registro da proposta não confere — consulte a auditoria',ORDER_REJECTED:'Ordem recusada na execução',EXPIRED:'Proposta expirada',NOT_EXECUTED:'Ordem sem preço oficial para executar'};
  const short=v=>day(v).slice(0,5);
  function routineMark(d){
    const ok=d.daily_history.filter(p=>p.state==='AVAILABLE').at(-1);
    const pend=d.daily_history.filter(p=>p.state!=='AVAILABLE').map(p=>p.state==='PENDING_CLOSE'?'Fechamento de '+short(p.session)+' ainda pendente':short(p.session)+': faltam cotações de '+p.missing.join(', '));
    el('routine-mark').innerHTML=(ok?'Último fechamento marcado: '+day(ok.session):'Nenhum fechamento marcado ainda')+'<br>'+(pend.length?esc(pend.slice(0,3).join('; ')+(pend.length>3?' e mais '+(pend.length-3):'')):'Nenhuma pendência de marcação.')+(pend.length?' <button type="button" id="routine-update">Atualizar dados</button>':'');
    // DP-30: payments still to come; shown only when there is at least one A_RECEBER event.
    const due=(d.dividends?.events||[]).filter(e=>e.state==='A_RECEBER'), pays=due.map(e=>e.payment_date).filter(Boolean).sort(), box=el('routine-dividends');
    box.hidden=!due.length;
    box.innerHTML=due.length?'Proventos: '+due.length+' a receber ('+money(d.dividends.receivable)+')'+(pays.length?', próximo pagamento '+short(pays[0]):', pagamento a definir')+' <a class="product-wallet-link" href="/dividends?wallet='+encodeURIComponent(d.wallet)+'">Ver proventos →</a>':'';
    el('routine-update')?.addEventListener('click',()=>document.getElementById('hfl-market-open').click());
    const last=d.daily_history.at(-1), t=last?.trades||[];
    el('routine-today').hidden=!t.length;
    el('routine-today').innerHTML=t.length?'Operações de '+day(last.session)+': '+t.map(x=>esc(({BUY:'compra',SELL:'venda'}[x.side]||x.side)+' '+x.quantity+' '+x.ticker)+' <span class="product-chip">'+origin(x)+'</span>').join(', '):'';
  }
  async function routinePolicy(w,version,signal,closed){
    const box=el('routine-policy');
    const set=h=>{if(version===revision)box.innerHTML=h;};
    const analyze='<a class="product-wallet-link" href="'+esc(el('personal-analysis')?.getAttribute('href')||'/radar')+'">Analisar carteira →</a>';
    if(w.strategy==='BUY_HOLD')return set('Política: manter as posições, sem rebalanceamento; proventos ficam em caixa.');
    if(['SMA_50_200','BOLLINGER_20_2'].includes(w.strategy)){
      const d=w.audit.filter(e=>e.kind==='RULE_DECISION').at(-1),x=w.audit.filter(e=>e.kind==='RULE_EXECUTION').at(-1);
      return set(esc(w.initialization_note)+(d?'<br>Último sinal processado: '+day(d.source.decision_session)+(x?.source.decision_session===d.source.decision_session?' · sessão seguinte conferida.':' · aguardando a abertura oficial de '+day(d.source.execution_session)+'.'):'<br>Aguardando histórico de preços completo para calcular os sinais.')+(closed&&(!d||d.source.decision_session<closed)?'<br>Processamento atrasado: falta concluir os dados/sessões até '+day(closed)+'. Use Atualizar dados.':'')+'<br><a href="/operations?wallet='+encodeURIComponent(w.id)+'">Ver operações e sinais →</a>');
    }
    const external=w.nature!=='SIMULATION'?'Carteira pessoal: análises dos agentes são apenas consultivas; nada é registrado automaticamente.<br>':'';
    try{
      const r=await fetch('/api/platform/wallet-manager/latest?'+new URLSearchParams({wallet:w.id}),{cache:'no-store',signal});
      const j=await r.json();if(!r.ok||j.wallet!==w.id)throw Error();
      const l=j.latest;
      if(!l)return set(external+'Nenhuma análise dos agentes para esta carteira.<br>'+analyze);
      const a=l.auction?' de '+short(l.auction.session):'', done=l.status==='APPLIED', t=l.trades.slice(0,5).map(x=>esc(({BUY:'Comprar',SELL:'Vender'}[x.side]||x.side)+' '+x.quantity+' '+x.ticker+' a '+money(x.price)));
      set(external+'<strong>'+esc(l.status==='PENDING_INTRADAY'?'Aprovada, aguardando preço posterior à aprovação'+a:l.status==='PENDING_AUCTION'?'Aprovada, aguardando leilão'+a:l.status==='EXECUTED'?(l.auction?.leg==='INTRADAY'?'Simulação intradiária executada':'Executada no leilão')+a:done?'Proposta aplicada'+(l.applied_at?' em '+new Date(l.applied_at).toLocaleDateString('pt-BR',{day:'2-digit',month:'2-digit'}):''):STATUS[l.status]||l.status)+'</strong><br>Dia-alvo '+short(l.target_date)+' · preços de referência de '+short(l.reference_session)+(t.length?'<ul>'+t.map(x=>'<li>'+x+'</li>').join('')+(l.trades.length>5?'<li>e mais '+(l.trades.length-5)+'</li>':'')+'</ul>':(l.status==='VALID_PROPOSAL'||done?'<br>Manter posições (sem operações)':''))+'<br><a class="product-wallet-link" href="'+esc(l.results_url)+'">Revisar proposta →</a>');
    }catch(e){if(e.name!=='AbortError')set(external+'Consulta da proposta indisponível.');}
  }
  // Side-by-side only for wallets of the same comparison group with identical inception dates; never summed.
  async function compare(me,d,catalog,version,signal){
    const others=me.comparison_group?catalog.wallets.filter(w=>w.id!==me.id&&w.comparison_group===me.comparison_group):[];
    const mine=d.periods.find(p=>p.key==='inception');
    const lines=await Promise.all(others.map(async o=>{
      try{
        const r=await fetch('/api/portfolio/history?'+new URLSearchParams({wallet:o.id}),{cache:'no-store',signal});
        const j=await r.json();if(!r.ok||j.wallet!==o.id||j.read_only!==true)throw Error();
        const b=j.periods.find(p=>p.key==='inception');
        if(mine?.state!=='AVAILABLE'||b?.state!=='AVAILABLE')return 'Comparação com '+o.name+' indisponível: sem fechamento.';
        if(mine.anchor_session!==b.anchor_session||mine.end_session!==b.end_session)return 'Comparação com '+o.name+' indisponível: datas de fechamento diferentes.';
        const diff=(Number(mine.return_fraction)-Number(b.return_fraction))*100;
        return 'Desde o início ('+short(mine.anchor_session)+' → '+short(mine.end_session)+'): '+me.name+' '+pct(mine.return_fraction)+' · '+o.name+' '+pct(b.return_fraction)+' · diferença '+(diff>0?'+':'')+diff.toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2})+' p.p.';
      }catch(e){return e.name==='AbortError'?null:'Comparação indisponível.';}
    }));
    if(version===revision&&!lines.includes(null))el('personal-compare').innerHTML=lines.map(l=>'<p class="product-note">'+esc(l)+'</p>').join('');
  }
  async function load(catalog){
    const selected=catalog.wallets.find(w=>w.id===catalog.selected), version=++revision;
    controller?.abort();controller=new AbortController();clear();el('personal-chart-error').hidden=true;el('routine-mark').textContent='Conferindo fechamentos…';el('routine-policy').textContent='';el('routine-today').hidden=true;el('routine-dividends').hidden=true;el('personal-compare').textContent='';
    if(!selected){el('personal-prices').textContent='Crie ou selecione uma carteira para acompanhar a evolução.';el('routine-mark').textContent='Sem carteira selecionada.';return;}
    el('personal-prices').textContent='Conferindo posições históricas e fechamentos RAW…';
    try{
      const response=await fetch('/api/portfolio/history?'+new URLSearchParams({wallet:selected.id}),{cache:'no-store',signal:controller.signal});
      const d=await response.json();if(version!==revision)return;
      if(!response.ok||d.wallet!==selected.id||d.wallet_revision!==selected.revision||d.read_only!==true)throw Error('A carteira mudou ou o histórico não pôde ser verificado. Use Atualizar consulta.');
      render(d);routineMark(d);routinePolicy(selected,version,controller.signal,d.last_closed);compare(selected,d,catalog,version,controller.signal);
    }catch(e){if(e.name==='AbortError'||version!==revision)return;el('personal-chart-error').textContent=e.message;el('personal-chart-error').hidden=false;el('personal-prices').textContent='Histórico indisponível. Nenhum preço foi estimado para preencher lacunas.';el('routine-mark').textContent='Marcação indisponível.';}
  }
  window.addEventListener('hfl:wallets',e=>load(e.detail));
  if(window.HFLPersonalCatalog)load(window.HFLPersonalCatalog);
})();
