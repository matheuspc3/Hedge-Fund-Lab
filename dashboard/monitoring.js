'use strict';
// Read-only presentation shared by Portfolio and H2. Financial values come from Python.
(() => {
  const root = document.querySelector('#monitoring');
  if (!root) return;
  const el = id => document.getElementById(id);
  const esc = v => String(v ?? 'Indisponível').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const money = v => v == null ? 'Indisponível' : Number(v).toLocaleString('pt-BR', {style:'currency',currency:'BRL'});
  const pct = v => v == null ? 'Indisponível' : (Number(v)*100).toLocaleString('pt-BR',{maximumFractionDigits:2})+'%';
  const stamp = v => v ? new Date(v).toLocaleString('pt-BR',{timeZone:'America/Sao_Paulo'})+' BRT' : 'Horário não publicado';
  const help = id => `<button class="ds-help" data-help="${id}"></button>`;
  const details = (title, data) => `<details><summary>${esc(title)}</summary><pre>${esc(JSON.stringify(data,null,2))}</pre></details>`;
  const table = (headers, rows, empty) => rows.length ? `<div class="ds-table-wrap" tabindex="0" role="region" aria-label="${esc(headers[0])}"><table><thead><tr>${headers.map(h=>`<th scope="col">${h}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${r.map(v=>`<td>${v}</td>`).join('')}</tr>`).join('')}</tbody></table></div>` : `<p class="ds-empty">${esc(empty)}</p>`;
  let catalog, revision=0, decisionRevision=0, catalogRevision=0, curveChart, allocationChart, eventPage;
  const paper=['/paper','/paper/','/paper.html','/legacy/paper','/legacy/paper/'].includes(location.pathname);
  if(el('monitor-demo'))el('monitor-demo').checked=new URLSearchParams(location.search).get('demo')==='1';
  function timeline(rows) {
    el('monitor-timeline').innerHTML=table(['Evento','Sessão','Data / hora','Status','Evidência'],rows.map(t=>[esc(t.kind),esc(t.session),stamp(t.at),esc(t.status),`<a href="${esc(t.evidence)}">Fonte</a>${t.sha256?`<small class="monitor-hash">${esc(t.sha256)}</small>`:''}`]),'Nenhum evento comprovado.');
  }
  function pagination(p) {
    eventPage=p;
    if(!el('monitor-pagination'))return;
    el('monitor-pagination').hidden=!p;
    if(p){el('monitor-prev').disabled=p.offset===0;el('monitor-next').disabled=p.next_offset==null;el('monitor-page-label').textContent=`Eventos ${Math.min(p.offset+1,p.total)}–${Math.min(p.offset+p.limit,p.total)} de ${p.total}`;}
  }
  function ledgerQuery(resource) {
    const q={demo:'1',wallet:el('monitor-wallet').value,limit:'10'};
    const session=new URLSearchParams(location.search).get('session');
    if(session)q.session=session;
    if(resource)q.resource=resource;
    return q;
  }
  async function loadEvents(offset) {
    const version=++revision;
    try {
      const p=await get('/api/portfolio/ledger?'+new URLSearchParams({...ledgerQuery('events'),offset:String(offset)}));
      if(version!==revision)return;
      timeline(p.items.map(e=>({kind:e.kind,session:e.session,at:e.effective_at,status:'SYNTHETIC_TEST',evidence:'/api/portfolio/ledger?'+new URLSearchParams(ledgerQuery('events')),sha256:e.sha256})));
      pagination(p);
    }catch(e){if(version===revision)fail(e);}
  }
  async function get(path) {
    const r = await fetch(path,{cache:'no-store'});
    const d = await r.json();
    if (!r.ok) throw Error('Não foi possível ler os registros. Confira a integridade e consulte novamente.');
    return d;
  }
  function fail(error) { el('monitor-error').hidden=false; el('monitor-error').textContent=error.message; }
  function urlParam(key, value) {
    const u = new URL(location.href);
    if (value) u.searchParams.set(key,value); else u.searchParams.delete(key);
    history.replaceState(null,'',u.pathname+u.search+u.hash);
  }
  function route() {
    if (!el('portfolio-views')) return;
    const aliases = {'ai-proposal':'simulador','carteira-contabil':'simulador','audit-title':'simulador'};
    let view = aliases[location.hash.slice(1)] || location.hash.slice(1) || (new URLSearchParams(location.search).has('analysis')?'global-workflow':'visao-geral');
    if (!['visao-geral','posicoes','global-workflow','simulador','evidencias'].includes(view)) view='visao-geral';
    document.querySelectorAll('[data-portfolio-view]').forEach(p=>p.hidden=p.dataset.portfolioView!==view);
    document.querySelectorAll('#portfolio-views a').forEach(a=>a.hash==='#'+view?a.setAttribute('aria-current','page'):a.removeAttribute('aria-current'));
    root.hidden=!['visao-geral','posicoes','evidencias'].includes(view);
    if (view==='simulador') window.dispatchEvent(new Event('resize'));
  }
  window.addEventListener('hashchange', route);
  function render(d) {
    curveChart?.destroy(); curveChart=null; allocationChart?.destroy(); allocationChart=null;
    el('monitor-content').hidden=!d.available;
    el('monitor-identity').innerHTML=`<span class="ds-badge">${d.classification==='H2_PAPER_LEDGER'?'Carteira paper H2 · registros persistentes':d.classification==='SYNTHETIC_TEST'?'DEMONSTRAÇÃO — DADOS SINTÉTICOS':'Gestor Global · carteira hipotética'}</span><h2>${esc(d.label)}</h2><p><a href="${esc(d.source)}">Consultar fonte persistida</a></p><p class="ds-alert">${esc(d.limitation)}</p>${details('Identidade e classificação',{identity:d.identity,id:d.id,classification:d.classification})}`;
    if (!d.available) return;
    const s=d.summary;
    const metrics=[['Capital inicial',money(s.initial_capital),'capital-alocado'],['Patrimônio verificável',money(s.equity),'patrimonio'],['Caixa disponível',money(s.cash),'caixa-disponivel'],['Caixa reservado',money(s.reserved),'caixa-reservado'],['Recebíveis',money(s.receivable),'recebivel'],['Valor investido',money(s.invested ?? (d.positions.length===0?0:null)),'capital-alocado'],['Exposição',pct(s.exposure),'exposicao'],['Posições',d.positions.length,'peso-atual'],['Resultado realizado',money(s.realized_pnl),'pnl-realizado'],['Resultado não realizado',money(s.unrealized_pnl),'pnl-nao-realizado'],['Custos acumulados',money(s.costs),'custos'],['Volatilidade',pct(s.volatility),'volatilidade'],['Giro da carteira',pct(s.turnover),'turnover'],['Resultado acumulado líquido de custos',money(s.pnl),'pnl-realizado'],['Drawdown',s.drawdown==null?'Histórico insuficiente':pct(s.drawdown),'drawdown']];
    const metric=([label,value,id])=>`<article class="ds-card"><span>${esc(label)} ${help(id)}</span><strong>${esc(value)}</strong></article>`;
    el('monitor-summary').innerHTML=metrics.filter((_,i)=>[1,2,6,7].includes(i)).map(metric).join('');
    el('monitor-secondary').innerHTML=metrics.filter((_,i)=>![1,2,6,7].includes(i)).map(metric).join('');
    el('monitor-status').innerHTML=`<p><strong>Situação operacional:</strong> <code>${esc(d.operation_status)}</code> ${help('execucao-paper')}</p><p>Autorização: ${esc(d.authorization_status)}</p><p>Última marcação: <strong>${esc(d.mark?.session)}</strong> · ${money(d.mark?.close)} ${help('marcacao-mercado')}</p><p>${d.classification==='H2_PAPER_LEDGER'?'Preço ajustado local para marcação H2; não é cotação em tempo real. Preço de execução somente no histórico de operações.':'Marcas do snapshot: '+esc(d.mark?.source)+' · '+esc(d.mark?.basis)+'. Não são cotações em tempo real.'}</p><p>Interface atualizada em ${stamp(d.observed_at)}. Consultar não avança o pregão.</p>`;
    el('monitor-positions').innerHTML=table(['Ticker','Total','Disponível','Reservada','Em liquidação '+help('d-mais-2'),'Preço médio '+help('custo-medio'),'Última marca','Valor','Peso atual '+help('peso-atual'),'Não realizado','Realizado','Sessão / origem'],d.positions.map(p=>[esc(p.ticker),esc(p.quantity),esc(p.available),esc(p.reserved),esc(p.unsettled),money(p.average_cost),money(p.raw_mark),money(p.market_value),pct(p.weight),money(p.unrealized_pnl),money(p.realized_pnl),esc(d.mark?.session)+' / '+esc(d.classification)]),'Esta carteira ainda não possui posições registradas.');
    el('monitor-allocation').innerHTML=table(['Alocação atual · '+(d.persistent_execution?'ledger paper':'snapshot hipotético'),'Valor','Peso'],d.allocation.filter(p=>Number(p.value)>0).map(p=>[esc(p.asset),money(p.value),pct(p.weight)]),'Sem composição verificável.');
    const allocation=d.allocation.filter(p=>Number(p.value)>0);
    const composition=d.positions.length>0&&allocation.length>1;
    el('monitor-composition').hidden=!composition;el('monitor-composition').parentElement.hidden=!composition;
    if(composition)allocationChart=new Chart(el('monitor-composition'),{type:'doughnut',data:{labels:allocation.map(p=>p.asset),datasets:[{data:allocation.map(p=>p.value),backgroundColor:['--accent','--state-info','--state-synthetic','--state-warn','--state-neutral'].map(t=>getComputedStyle(document.documentElement).getPropertyValue(t))}]},options:{responsive:true,animation:false}});
    el('monitor-trades').innerHTML=table(['Data','Ticker','Movimento','Quantidade','Preço de execução','Custos','Liquidação','Origem / decisão','Status'],d.trades.map(t=>[esc(t.session),esc(t.ticker),esc(t.type),esc(t.quantity),money(t.price),money(t.cost),esc(t.settlement),`<a href="${esc(t.source)}">Ledger</a> · ${esc(t.decision_session)}`,esc(t.status)]),'Nenhuma compra ou venda paper registrada nesta fonte.');
    el('monitor-curve-table').innerHTML=table(['Sessão reconciliada','Patrimônio','Caixa','Valor investido','Resultado acumulado'],d.curve.map(p=>[esc(p.session),money(p.equity),money(p.cash),money(p.invested),money(p.pnl)]),'Nenhuma série prospectiva reconciliada. O snapshot não é histórico de desempenho.');
    el('monitor-curve-note').textContent=d.curve.length<2?'Histórico insuficiente. Uma observação não representa desempenho histórico.':d.classification==='SYNTHETIC_TEST'?'Pontos somente nas sessões reconciliadas; sem interpolação entre pregões ausentes. Selecione uma sessão para consultar seu caixa, posições e liquidações. Demonstração sintética sem benchmark científico.':'Pontos somente nas sessões reconciliadas; sem interpolação entre pregões ausentes. Caixa e valor investido históricos não publicados permanecem indisponíveis. Benchmark: consultar sua carteira independente.';
    el('monitor-curve').hidden=d.curve.length<2;
    if(d.curve.length>=2) curveChart=new Chart(el('monitor-curve'),{type:'line',data:{labels:d.curve.map(p=>p.session),datasets:[{label:'Patrimônio (R$)',data:d.curve.map(p=>p.equity),showLine:false,pointRadius:5,borderColor:getComputedStyle(document.documentElement).getPropertyValue('--accent')}]},options:{responsive:true,animation:false,plugins:{legend:{display:true}}}});
    timeline(d.timeline);pagination(d.pagination?.events);
    if(el('monitor-session-controls')){
      el('monitor-session-controls').hidden=d.classification!=='SYNTHETIC_TEST';
      const selected=new URLSearchParams(location.search).get('session')||'';
      el('monitor-session').innerHTML='<option value="">Último estado / todas as sessões</option>'+(d.sessions_available||[]).map(s=>`<option value="${esc(s)}">${esc(s)}</option>`).join('');
      el('monitor-session').value=selected;
    }
    if(d.last_reconciliation)el('monitor-status').insertAdjacentHTML('beforeend',`<p>Última reconciliação: <strong>${esc(d.last_reconciliation.session)}</strong> · ${esc(d.last_reconciliation.status)}</p>`);
    if(d.unavailable_sessions?.length)el('monitor-status').insertAdjacentHTML('beforeend',details('Sessões com marcação indisponível',d.unavailable_sessions));
    el('monitor-future').innerHTML=d.future.length?d.future.map(e=>`<p><strong>${esc(e.kind)}</strong> · sessão ${esc(e.target_session)} · prazo ${stamp(e.deadline)}</p>`).join(''):'<p>Nenhum evento futuro operacional publicado. Intenções expiradas não geram ordens retroativas.</p>';
    const dec=d.decision, sup=d.supervision;
    const decisionSummary=dec?.result?.response;
    el('monitor-last').innerHTML=dec ? `${decisionSummary?'<p>'+esc(decisionSummary.summary)+'</p>':''}<p>Última decisão · sessão ${esc(dec.valuation_session||dec.session)} · ${esc(dec.portfolio?.decision||dec.status)}${decisionSummary?' · caixa-alvo '+pct(decisionSummary.target_cash_weight):' · alvo '+pct(dec.portfolio?.target_weight??dec.target_weight)}</p>${dec.consensus?`<p>Consenso: ${esc(dec.consensus.technical_outcome)} · Risk: ${esc(dec.risk?.verdict)} · agentes: ${esc(dec.committee?.responded)}</p>`:''}${sup?`<p>Supervisão: <code>${esc(sup.order_state)}</code> · prazo ${stamp(sup.deadline)} · execução: ${sup.outcome?'consultar resultado persistido':'nenhum resultado registrado'}</p>`:''}${dec.id?`<a href="/portfolio?analysis=${esc(dec.id)}#global-workflow">Consultar proposta e validação →</a>`:''}${details('Última decisão e referências',dec)}`:'<p>Nenhuma decisão registrada para esta estratégia.</p>';
    el('monitor-evidence').innerHTML=details('Identidade, preços e registros consultados',{id:d.id,source:d.source,mark:d.mark,read_only:d.read_only,persistent_execution:d.persistent_execution,observed_at:d.observed_at,reconciliations:d.reconciliations,unavailable_sessions:d.unavailable_sessions});
    route();
  }
  async function refresh() {
    const version=++revision, selected=el('monitor-wallet').value;
    el('monitor-error').hidden=true; el('monitor-content').hidden=true;
    el('monitor-identity').textContent='Lendo registros persistidos…';
    el('monitoring').setAttribute('aria-busy','true');
    try { const d=await get(selected==='synthetic-v765'?'/api/portfolio/ledger?'+new URLSearchParams(ledgerQuery()):'/api/portfolio/monitoring?'+new URLSearchParams({wallet:selected})); if(version===revision){render(d);urlParam('wallet',selected);} }
    catch(e){if(version===revision)fail(e);} finally{if(version===revision)el('monitoring').setAttribute('aria-busy','false');}
  }
  async function loadDecision(id) {
    const version=++decisionRevision;
    el('decision-detail').textContent='Lendo inferência selada…';
    try {
      const d=await get('/api/platform/global?'+new URLSearchParams({id}));
      if(version!==decisionRevision)return;
      if(d.mode!=='CONSULTATIVE_SANDBOX')throw Error('Demonstrações estão disponíveis somente no Simulador.');
      const r=d.result, p=r?.response, v=r?.validation, projected=v?.valid&&v.financial_validation?.valid?v.financial_validation.projected:null;
      const cost=d.usage_accounting;
      el('decision-detail').innerHTML=`<a href="#global-workflow" id="decision-back">← Voltar para a lista</a><p>${window.HFL.state(d.validation_status||d.status)}</p><h2>${v?.valid?'Proposta validada':'Resposta rejeitada'}</h2><p class="lead">${esc(p?.summary||'Sem resposta registrada')}</p><p>${esc(d.identity)} · <code>${esc(d.id)}</code></p><div class="monitor-dates"><p>Sessão de mercado: <strong>${esc(d.valuation_session)}</strong></p><p>Gemini deliberou: <strong>${stamp(r?.completed_at)}</strong></p><p>Interface consultada: <strong>${stamp(new Date().toISOString())}</strong></p></div><p class="ds-alert">Proposta consultiva. Validação não é autorização nem execução. ${v?.valid?'':'Resposta rejeitada: consultável apenas como evidência.'}</p>${details('Raciocínio global registrado',p?.global_reasoning)}<p>Carteira de origem: snapshot hipotético ${esc(d.portfolio?.portfolio_id)} · ${money(d.portfolio?.equity)}. ${help('proposta-consultiva')}</p>${table(['Ativo','Peso no snapshot','Peso-alvo '+help('peso-alvo'),'Peso projetado','Motivo'],Object.keys(d.opinions||{}).map(t=>[esc(t),pct(d.current_weights?.[t]),pct(p?.target_weights?.[t]),projected?pct(projected.positions[t]?.weight??0):'Indisponível',esc(p?.asset_reasoning?.[t]?.reasoning)]),'Nenhum parecer vinculado.')}<p>Caixa no snapshot: ${pct(d.portfolio?.cash_weight)} · caixa-alvo: ${pct(p?.target_cash_weight)} · caixa projetado: ${projected?pct(projected.cash_weight):'Indisponível'}.</p><p>Validação global: ${esc(v?.status)} ${help('proposta-validada')} · validação financeira: ${help('validacao-financeira')} ${v?.financial_validation?v.financial_validation.valid?'aprovada':'rejeitada':'indisponível'}.</p><h3>Operações propostas ${help('proposta-consultiva')}</h3>${table(['Ticker','Movimento','Quantidade','Motivo'],(p?.operations||[]).map(o=>[esc(o.ticker),esc(o.side),esc(o.quantity),esc(o.reasoning)]),'Nenhuma operação proposta. Nenhuma execução financeira.')}<p>Condições de liquidação ${help('liquidacao')}: ${(p?.settlement_deferred_operations||p?.deferred_opportunities||[]).length?'consultar contrato registrado':'nenhuma operação de liquidação adiada registrada'}.</p><h3>Ativos em observação</h3>${table(['Ticker','Observação','Condição para reavaliação'],(p?.watchlist_candidates||[]).map(w=>[esc(w.ticker),esc(w.observation),esc(w.reassessment_condition)]),'Nenhuma watchlist publicada neste contrato.')}<p>Não selecionados: ${esc(p?.not_selected?.join(', '))}</p><h3>Riscos registrados</h3><ul>${(p?.risks||[]).map(s=>`<li>${esc(s)}</li>`).join('')}</ul><p>Custo de API: ${cost?moneyUsd(cost.usd_estimated):moneyUsd(r?.cost_usd)} · mínimo observado ${moneyUsd(cost?.usd_observed_lower_bound)} · reserva ${moneyUsd(cost?.usd_reserved)} · cobrança não confirmada.</p><p>Validade do contexto: ${stamp(d.expires_at)}. Status selado da validação permanece ${esc(d.validation_status)}.</p><a href="/api/platform/global?id=${esc(id)}">Evidência primária verificada (JSON)</a>${details('Pareceres, contexto, projeção, liquidação e hashes',d)}`;
      el('decision-detail').hidden=false;el('decision-list').hidden=true;urlParam('analysis',id);
      el('decision-back').addEventListener('click',e=>{e.preventDefault();++decisionRevision;el('decision-detail').hidden=true;el('decision-list').hidden=false;urlParam('analysis',null);el('workflow-record').focus();});
    } catch(e){if(version!==decisionRevision)return;el('decision-detail').textContent=e.message;el('decision-detail').hidden=false;el('decision-list').hidden=false;}
  }
  function moneyUsd(v) { return v==null?'Desconhecido (USD)':'US$ '+Number(v).toFixed(6); }
  async function start() {
    const version=++catalogRevision; ++revision; ++decisionRevision;
    el('monitor-content').hidden=true;el('monitor-error').hidden=true;
    const next=await get('/api/portfolio/monitoring');
    if(version!==catalogRevision)return;catalog=next;
    let list=catalog.wallets.filter(w=>paper?w.id.startsWith('h2:'):w.id.startsWith('global:'));
    if(el('monitor-demo')?.checked){const demo=await get('/api/portfolio/ledger?demo=1');if(version!==catalogRevision)return;list=demo.wallets;}
    el('monitor-wallet').innerHTML=list.map(w=>`<option value="${esc(w.id)}">${esc(w.label)}</option>`).join('');
    const requested=new URLSearchParams(location.search).get('wallet');
    if(!paper&&requested?.startsWith('h2:')){location.replace('/paper?'+new URLSearchParams({wallet:requested})+'#acompanhamento');return;}
    if(requested&&!list.some(w=>w.id===requested))throw Error('Carteira do link não encontrada nesta linha de pesquisa. Selecione uma carteira disponível.');
    if(requested)el('monitor-wallet').value=requested;
    if(!list.length){el('monitor-identity').textContent='Nenhuma carteira disponível nesta origem. Execução paper oficial desabilitada.';return;}
    await refresh();
    if(version!==catalogRevision||!el('workflow-record'))return;
    const records=catalog.records;
    el('workflow-record').innerHTML='<option value="">Selecionar inferência oficial</option>'+records.map(r=>`<option value="${esc(r.id)}">${esc(r.identity)} · ${esc(r.validation_status||r.native_state)}</option>`).join('');
    el('decision-list').innerHTML=table(['Identidade / registro','Contexto preparado','Validação','Consulta'],records.map(r=>[esc(r.identity)+'<small class="monitor-hash">'+esc(r.id)+'</small>',stamp(r.created_at),esc(r.validation_status||r.native_state),`<button data-decision="${esc(r.id)}" data-action="read">Abrir proposta</button>`]),'Nenhuma inferência oficial disponível.');
    const id=new URLSearchParams(location.search).get('analysis');
    if(id){el('workflow-record').value=id;await loadDecision(id);}
  }
  el('decision-list')?.addEventListener('click',e=>{const b=e.target.closest('[data-decision]');if(b){el('workflow-record').value=b.dataset.decision;loadDecision(b.dataset.decision);}});
  el('workflow-record')?.addEventListener('change',()=>{if(el('workflow-record').value)loadDecision(el('workflow-record').value);});
  el('monitor-wallet').addEventListener('change',()=>{++catalogRevision;refresh();});
  el('monitor-demo')?.addEventListener('change',()=>{urlParam('demo',el('monitor-demo').checked?'1':null);urlParam('wallet',null);urlParam('session',null);el('monitor-session').value='';start().catch(fail);});
  el('monitor-session')?.addEventListener('change',()=>{urlParam('session',el('monitor-session').value);refresh();});
  el('monitor-next')?.addEventListener('click',()=>{if(eventPage?.next_offset!=null)loadEvents(eventPage.next_offset);});
  el('monitor-prev')?.addEventListener('click',()=>{if(eventPage)loadEvents(Math.max(0,eventPage.offset-eventPage.limit));});
  el('monitor-refresh').addEventListener('click',()=>start().catch(fail));
  route();start().catch(fail);
})();
