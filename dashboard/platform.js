'use strict';
(() => {
  const el=id=>document.getElementById(id),esc=v=>String(v??'N/D').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const money=v=>v==null?'N/D':Number(v).toLocaleString('pt-BR',{style:'currency',currency:'BRL'}),pct=v=>v==null?'N/D':(Number(v)*100).toLocaleString('pt-BR',{maximumFractionDigits:2})+'%',stamp=v=>v?new Date(v).toLocaleString('pt-BR',{timeZone:'America/Sao_Paulo'}):'N/D',day=v=>v?v.slice(0,10).split('-').reverse().join('/'):'N/D';
  const pill=(state,text=state)=>`<span class="hfl-state" data-state="${esc(state)}">${esc(text)}</span>`,empty=text=>`<p class="hfl-empty">${esc(text)}</p>`;
  function legacyRoute(){
    const historical={readiness:'sala',wallets:'carteiras'}[location.hash.slice(1)];
    if(historical)location.replace('/legacy/paper'+location.search+'#'+historical);
    return Boolean(historical);
  }
  if(legacyRoute())return;
  window.addEventListener('hashchange',legacyRoute);
  const data=x=>x?.available?x.data:null;
  // PAPER-02: presentation only. Every price, period, weight and base100 value
  // comes from the verified Python read model, never a second financial engine.
  const root=el('home-portfolio'),params=new URLSearchParams(location.search);
  let pilotRevision=0,pilotChart,pilotController,pilotCatalogLoaded=false;
  const selected={wallet:params.get('wallet')||'',session:params.get('session')||'',period:params.get('period')||'since_start'};
  const percent=v=>v==null?'Indisponível':Number(v).toLocaleString('pt-BR',{maximumFractionDigits:2})+'%';
  const table=(headers,rows,message)=>rows.length?`<div class="ds-table-wrap" tabindex="0" role="region" aria-label="${esc(headers[0])}"><table class="ds-table"><thead><tr>${headers.map(h=>`<th scope="col">${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>`<tr>${row.map(v=>`<td>${v}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`:`<p class="ds-empty">${esc(message)}</p>`;
  function clearPilot(){
    el('pilot-content').hidden=true;pilotChart?.destroy();pilotChart=null;
    ['pilot-equity','pilot-variation','pilot-anchor','pilot-kpis','pilot-cash','pilot-assets','pilot-positions','pilot-decision','pilot-trades','pilot-chart-table'].forEach(id=>el(id).replaceChildren());
  }
  function showPilot(d){
    pilotCatalogLoaded=true;
    el('pilot-wallet').innerHTML=d.wallets.map(w=>`<option value="${esc(w.id)}">${esc(w.label)}</option>`).join('');
    el('pilot-wallet').value=d.wallet;
    el('pilot-session').innerHTML=d.sessions.map(s=>`<option value="${esc(s)}">${day(s)}${s>d.last_reconciled_session?' · indisponível':''}</option>`).join('');
    el('pilot-session').value=d.session;el('pilot-period').value=d.period;
    el('pilot-scenario').textContent=`Cenário sintético de ${day(d.scenario.start)} a ${day(d.scenario.end)} · agentes roteirizados. As datas não são sessões reais observadas pelo piloto.`;
    selected.wallet=d.wallet;selected.session=d.session;selected.period=d.period;
    history.replaceState(null,'','/?'+new URLSearchParams({demo:'1',...selected}));
    if(d.status==='SESSION_UNAVAILABLE'){
      el('pilot-status').textContent=`Sessão ${day(d.session)} indisponível. Última reconciliada: ${day(d.last_reconciled_session)}. Nenhum saldo substituído.`;return;
    }
    const s=d.summary,metric=d.periods[d.period],labels={day:'Variação da sessão',since_start:'Desde o início',month:'Mês corrente',year:'Ano corrente',last_12_months:'Últimos 12 meses'};
    el('pilot-content').hidden=false;
    el('pilot-status').textContent=`${d.label} · marca reconciliada de ${day(d.session)}${d.pending_session?' · sessão '+day(d.pending_session)+' pendente':''}`;
    el('pilot-equity').textContent=money(s.equity);
    el('pilot-variation').textContent=metric.status==='AVAILABLE'?`${labels[d.period]}: ${money(metric.change_brl)} · ${percent(metric.change_pct)}`:metric.status==='UNAVAILABLE'?'Variação indisponível · há lacuna no período.':'Histórico insuficiente para o período completo.';
    el('pilot-anchor').textContent=metric.status==='AVAILABLE'?`Âncora: ${day(metric.anchor_session)} → ${day(d.session)}`:metric.partial?`${metric.partial.label} em ${day(metric.partial.anchor_session)}: ${money(metric.partial.change_brl)} · ${percent(metric.partial.change_pct)}`:'Sem retorno calculável para esta seleção.';
    const kpis=[['Caixa liquidado',money(s.cash.settled)],['Caixa disponível',money(s.cash.available)],['Valor investido',money(s.invested)],['Posições',s.position_count]];
    el('pilot-kpis').innerHTML=kpis.map(([label,value])=>`<article class="ds-kpi"><span class="ds-kpi-label">${label}</span><strong class="ds-kpi-value">${esc(value)}</strong></article>`).join('');
    el('pilot-cash').innerHTML=table(['Componente','Valor'],[['Reservas',money(s.cash.reserved)],['Recebíveis',money(s.cash.receivable)],['Custos acumulados',money(s.costs)],['Resultado realizado',money(s.realized_pnl)],['Resultado não realizado',money(s.unrealized_pnl)]],'Sem detalhes de caixa.');
    el('pilot-assets').innerHTML=d.assets.map(a=>`<article class="ds-card home-asset"><div class="home-asset-head"><h3>${esc(a.ticker)}</h3><span class="home-caption">${a.position?'Em carteira':'Sem posição'}</span></div><strong>${money(a.close)}</strong><p>Preço por ação · sessão ${day(a.price_session)}</p><p class="home-price-change">${a.price_change?`${money(a.price_change.change_brl)} · ${percent(a.price_change.change_pct)}`:'Histórico insuficiente para variação do preço'}</p><span class="home-caption">${a.price_change?'Preço versus '+day(a.previous_session):'Sem preço anterior reconciliado'}</span>${a.position?`<div class="home-asset-position"><span>Posição: ${money(a.position.market_value)}</span><span>Peso atual: ${pct(a.position.weight)}</span>${a.initial_target?`<span>Alvo inicial: ${pct(a.initial_target)}</span>`:''}</div>`:''}</article>`).join('');
    el('pilot-positions').innerHTML=table(['Posição','Quantidade','Preço de referência','Valor','Peso atual','Custo médio','Não realizado','Mudança de valor da posição'],d.assets.filter(a=>a.position).map(a=>[esc(a.ticker),esc(a.position.quantity),money(a.position.raw_mark),money(a.position.market_value),pct(a.position.weight),money(a.position.average_cost),money(a.position.unrealized_pnl),a.position_status==='NEW_POSITION'?'Nova posição':a.position_value_change==null?'Indisponível':money(a.position_value_change)]),'Esta carteira está em caixa, sem posições registradas.');
    el('pilot-decision-title').textContent=d.decision?d.decision.action==='HOLD'?'Manter carteira':'Alterar posições':'Nenhuma decisão registrada';
    el('pilot-decision').innerHTML=d.decision?`<p>${d.decision.action==='HOLD'?'HOLD explícito, sem novas ordens.':'Proposta roteirizada; operações dependem de validação e autorização de teste.'}</p><p>Sessão da decisão: <strong>${day(d.decision.session)}</strong><br>Abertura-alvo sintética: ${day(d.decision.target_session)}</p><p class="home-caption">${esc(d.decision.producer)} · sem deliberação de agentes reais</p>`:'<p>Ausência de decisão não significa HOLD.</p>';
    el('pilot-trades').innerHTML=table(['Sessão','Ativo / movimento','Quantidade','Preço','Custo','D+2'],d.trades.slice().reverse().map(t=>[day(t.session),esc(t.ticker)+' · '+(t.side==='BUY'?'Compra':'Venda'),esc(t.quantity),money(t.price),money(t.cost),day(t.due_session)]),'Nenhuma compra ou venda nesta carteira até a sessão selecionada.');
    el('pilot-source').textContent=`${d.source}. Integridade: verificada por replay. Artefato ${d.integrity.artifact_sha256}.`;
    const c=d.comparison;
    el('pilot-chart-note').textContent=c.status==='AVAILABLE'?`Base 100 em ${day(c.anchor_session)} · até ${day(d.session)}. Carteira selecionada em destaque.`:'Histórico insuficiente: uma observação é uma base, não uma curva de desempenho.';
    el('pilot-chart-table').innerHTML=table(['Sessão',...c.series.map(x=>x.label+' · base 100 / patrimônio')],c.sessions.map((session,i)=>[day(session),...c.series.map(x=>x.points[i].value==null?'Indisponível':`${Number(x.points[i].value).toLocaleString('pt-BR',{maximumFractionDigits:5})} / ${money(x.points[i].equity)}`)]),'Nenhum ponto reconciliado comum.');
    el('pilot-chart').parentElement.hidden=c.status!=='AVAILABLE';
    if(c.status==='AVAILABLE'){
      const styles=getComputedStyle(document.documentElement),colors=['--accent','--state-synthetic'];
      pilotChart=new Chart(el('pilot-chart'),{
        type:'line',
        data:{labels:c.sessions.map(day),datasets:c.series.map((x,i)=>({
          label:(x.id===d.wallet?'Selecionada · ':'')+x.label,
          data:x.points.map(p=>p.value==null?null:Number(p.value)),
          borderColor:styles.getPropertyValue(colors[i]).trim(),
          backgroundColor:styles.getPropertyValue(colors[i]).trim(),
          borderWidth:x.id===d.wallet?3:1.5,borderDash:x.id===d.wallet?[]:[5,4],
          pointRadius:x.id===d.wallet?4:3,spanGaps:false,tension:0
        }))},
        options:{responsive:true,maintainAspectRatio:false,animation:false,
          interaction:{mode:'index',intersect:false},
          plugins:{legend:{labels:{color:styles.getPropertyValue('--text').trim(),boxWidth:12}},
            tooltip:{callbacks:{afterLabel:ctx=>money(c.series[ctx.datasetIndex].points[ctx.dataIndex].equity)}}},
          scales:{x:{ticks:{color:styles.getPropertyValue('--muted').trim(),maxTicksLimit:6},grid:{display:false}},
            y:{ticks:{color:styles.getPropertyValue('--muted').trim()},grid:{color:styles.getPropertyValue('--line').trim()}}}
        }
      });
    }
  }
  async function refreshPilot(){
    const version=++pilotRevision;pilotController?.abort();pilotController=new AbortController();
    clearPilot();el('pilot-error').hidden=true;el('pilot-status').textContent='Carregando demonstração verificada…';root.setAttribute('aria-busy','true');
    const query=new URLSearchParams({demo:'1',period:selected.period});
    if(selected.wallet)query.set('wallet',selected.wallet);if(selected.session)query.set('session',selected.session);
    try{
      const r=await fetch('/api/portfolio/pilot?'+query,{cache:'no-store',signal:pilotController.signal});
      const d=await r.json();if(version!==pilotRevision)return;
      if(!r.ok)throw Error('Seleção inválida ou consulta indisponível. Confira carteira, sessão e período.');
      if(!d.available)throw Error(d.message||'Demonstração indisponível.');
      if(d.classification!=='SYNTHETIC_TEST'||d.read_only!==true)throw Error('Classificação demonstrativa inválida.');
      showPilot(d);
    }catch(e){if(version===pilotRevision){clearPilot();if(!pilotCatalogLoaded){el('pilot-wallet').innerHTML='<option value="">Indisponível</option>';el('pilot-session').innerHTML='<option value="">Indisponível</option>';}el('pilot-error').textContent=e.message;el('pilot-error').hidden=false;el('pilot-status').textContent='Consulta indisponível · nenhum saldo apresentado.';}}
    finally{if(version===pilotRevision)root.setAttribute('aria-busy','false');}
  }
  if(params.get('demo')==='1'){
    el('pilot-not-started').hidden=true;el('pilot-demo').hidden=false;
    el('pilot-period').value=selected.period;
    ['wallet','session','period'].forEach(key=>el('pilot-'+key).addEventListener('change',()=>{selected[key]=el('pilot-'+key).value;refreshPilot();}));
    el('pilot-refresh').addEventListener('click',refreshPilot);refreshPilot();
  }
  function render(d){
    el('platform-updated').textContent='Consulta '+stamp(d.observed_at)+' BRT · registros multiativos';
    homeState(d);
    const v5=data(d.synthetic_v5);
    el('platform-integrity').innerHTML=`<div class="hfl-row">${pill(v5?.integrity?.ok?'COMPLETED':'BLOCKED','Demonstração V5: '+(v5?.integrity?.ok?'íntegra':'indisponível'))}</div><p class="muted small">Integridade da demonstração multiativos. Dados ausentes não comprovam prontidão oficial.</p>`;
    const jobs=data(d.jobs)||[],last=jobs.find(j=>j.state==='COMPLETED');
    el('platform-jobs').innerHTML=`<p class="muted small">Último processo bem-sucedido registrado: ${last?esc(last.module+' / '+last.command)+' · '+stamp(last.finished_at):'N/D'}. Recuperação não remove claims nem repete chamadas incertas.</p>`+(jobs.length?`<div class="table-scroll" tabindex="0" role="region" aria-label="Processos registrados, tabela rolável"><table><thead><tr><th>Processo</th><th>Estado comum / runner</th><th>Etapa</th><th>Início / conclusão BRT</th><th>Chamadas reservadas / gravadas</th><th>Custo observado</th><th>Continuar</th></tr></thead><tbody>${jobs.map(j=>`<tr><td>${esc(j.module)} · ${esc(j.command)}</td><td>${pill(j.state)}<br>${esc(j.native_state)}</td><td>${esc(j.result_state||j.stage||j.error||'Registro local')}</td><td>${stamp(j.started_at)}<br>${stamp(j.finished_at)}</td><td>${esc(j.calls_reserved)} / ${esc(j.calls_recorded)}</td><td>${j.cost_usd==null?'N/D':'US$ '+esc(j.cost_usd)}</td><td><a href="${esc(j.href)}">Consultar →</a></td></tr>`).join('')}</tbody></table></div>`:empty('Nenhum job registrado. A consulta não inicializa processos.'));
  }
  // "Estado do laboratório": only facts present in /api/platform/overview; missing data
  // is shown as unavailable, never inferred from the existence of a file.
  function homeState(d){
    const S=(code,o)=>window.HFL?window.HFL.state(code,o):esc(code),H=id=>window.HFL?window.HFL.help(id):'';
    const runs=data(d.radar_runs),run=runs?.runs?.find(r=>r.id===d.radar_run_selected),runHref='/radar'+(d.radar_run_selected?'?run='+encodeURIComponent(d.radar_run_selected):'');
    document.querySelectorAll('[data-run-link]').forEach(a=>{const u=new URL(a.getAttribute('href'),location.origin);if(d.radar_run_selected)u.searchParams.set('run',d.radar_run_selected);a.href=u.pathname+u.search+u.hash;});
    const real=d.global_records.filter(r=>r.mode==='CONSULTATIVE_SANDBOX'&&r.validation_status),synthetic=d.global_records.filter(r=>r.mode==='SYNTHETIC_DEMO').length;
    const closed=id=>id?.endsWith('-V1');
    const selection=data(d.official_selection);
    const kpi=(label,help,value,detail,href,cta)=>`<article class="ds-kpi"><span class="ds-kpi-label">${label} ${help}</span><span class="ds-kpi-value">${value}</span><span class="ds-kpi-detail">${detail}</span>${href?`<a href="${esc(href)}">${cta} →</a>`:''}</article>`;
    el('home-state').innerHTML=[
      kpi('Radar oficial',H('radar'),run?S(run.state==='COMPLETED'?'COMPLETED':run.state,{label:run.state==='COMPLETED'?'Execução concluída':run.state}):S('UNAVAILABLE'),
        run?`${esc(run.id)} · sessão ${day(run.session)} · ${selection?esc(selection.opinions_complete)+'/'+esc(selection.items.length)+' pareceres oficiais':'pareceres indisponíveis'}`:'Registro de execuções indisponível.',runHref,'Consultar pareceres'),
      kpi('Gestor Global',H('gestor-global'),real.length?real.map(r=>`<span class="home-record">${S(r.validation_status)} <small>${esc(r.identity.replace('HFL-MULTIASSET-GLOBAL-PM-',''))}${closed(r.identity)?' · encerrado':''}</small></span>`).join(''):S('UNAVAILABLE',{label:'Nenhuma inferência real'}),
        `${real.length} inferência(s) real(is) · ${synthetic} demonstração(ões) sintética(s), separadas. V1 encerrado para novas inferências; V2 somente pelo CLI.`,'/portfolio#global-workflow','Consultar propostas'),
    ].join('');
  }
  let running=false;
  async function refresh(){if(running)return;running=true;el('platform-refresh').disabled=true;el('platform-error').hidden=true;try{const r=await fetch('/api/platform/overview',{cache:'no-store'});if(!r.ok)throw Error('Consulta indisponível; confira o servidor e os registros locais.');render(await r.json());}catch(e){el('platform-error').innerHTML=`<p class="hfl-warning">${esc(e.message)} Use “Atualizar visão” para consultar novamente.</p>`;el('platform-error').hidden=false;el('platform-updated').textContent='Estado indisponível · nenhuma ação foi iniciada.';}finally{running=false;el('platform-refresh').disabled=false;}}
  el('platform-refresh').addEventListener('click',refresh);
  const laboratory=el('home-laboratory');let laboratoryLoaded=false;
  function labRoute(){const target=location.hash?document.getElementById(location.hash.slice(1)):null;if(target&&laboratory.contains(target)){laboratory.open=true;target.scrollIntoView();}if(laboratory.open&&!laboratoryLoaded){laboratoryLoaded=true;refresh();}}
  laboratory.addEventListener('toggle',labRoute);window.addEventListener('hashchange',labRoute);labRoute();
})();
