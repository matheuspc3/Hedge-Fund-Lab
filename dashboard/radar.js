'use strict';
const $ = id => document.getElementById(id);
const escape = value => String(value ?? '—').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const M = window.HFLMarket;
let viewVersion=0, aborter=new AbortController(), runs=null;
const query=new URLSearchParams(location.search);
const runId=()=>$('radar-run').value;
const synthetic=()=>state?.run?.mode==='SYNTHETIC_DEMO';
const isolated=()=>synthetic()||state?.network_isolation===true;
const readonly=()=>!state||state.mutation_available!==true;
function transfer(){ $('radar-to-global').href='/portfolio?'+new URLSearchParams({run:runId(),tickers:chosen().join(','),session:$('session').value,mode:state?.run?.mode||''})+'#global-workflow'; $('radar-to-market').href=M.link('/market',runId()); }
let state = null, csrf = '', selected = new Set(), report = null, poll = null, budgetPosting = false, guided = null;
const cash = value => value == null ? '—' : Number(value).toFixed(4);
const dateTime = value => value ? new Date(value).toLocaleString('pt-BR', {timeZone:'America/Sao_Paulo'}) : '—';
const chosen = () => [...selected];
const selection = () => ({tickers:chosen(), session:$('session').value, max_usd:Number($('budget').value), replay:$('replay').checked});
const messages = {invalid_or_duplicate_ticker:'Ticker inválido ou já selecionado. Use um código de ação da B3, como PETR4.',select_one_to_five_tickers:'Selecione de um a cinco ativos.',aggregate_budget_below_exposure:'O teto informado não cobre a exposição agregada atual. Refaça o preflight.',invalid_aggregate_budget:'Informe um teto agregado positivo em USD.',budget_changed_review_again:'As reservas mudaram. Refaça o preflight e revise os valores novamente.',explicit_budget_authorization_required:'Revise os valores e marque o consentimento de orçamento.',invalid_budget:'Informe um orçamento maior que zero e de até US$ 5.',explicit_paid_authorization_required:'Autorize explicitamente o custo deste lote antes de executar.',preflight_or_confirmation_changed:'A seleção ou os dados mudaram. Faça um novo preflight.',radar_busy_or_stale_lock:'O radar está ocupado ou tem uma execução interrompida. Consulte o status antes de continuar.',registry_unavailable:'Registro de execuções Radar ausente: nenhuma execução é selecionada automaticamente e todas as operações ficam bloqueadas.',registry_corrupted:'Registro de execuções Radar corrompido: nenhuma execução é selecionada automaticamente e todas as operações ficam bloqueadas.',unknown_radar_run:'Execução Radar desconhecida. Escolha uma execução do registro.',run_not_accepting_new_calls:'Esta execução não aceita novas chamadas.',runner_not_a_registered_run:'O servidor não tem execução operacional registrada: preparo e execução bloqueados.',radar_run_header_mismatch_reload_page:'A execução operacional do servidor mudou. Recarregue a página.',selection_outside_run_identity:'Sessão ou ativos fora da identidade desta execução.',aggregate_budget_authorization_required:'Exposição agregada acima do limite local: exige autorização de orçamento separada (CLI) antes de qualquer lote pago.',run_budget_exceeded:'Reserva acima do orçamento desta execução.',network_isolation_not_qualified_restart_server:'Servidor sem isolamento de rede qualificado: reinicie-o antes de qualquer execução paga.'};
function error(exc) { if(exc?.name==='AbortError')return; $('error').textContent = messages[exc.message] || exc.message || String(exc); $('error').hidden = false; }
function invalidate() { $('budget-review').hidden=true; $('budget-consent').checked=false; viewVersion++; transfer(); report = null; $('confirmation').hidden = true; $('paid').checked = false; $('preflight-result').textContent = 'Preflight necessário para confirmar este lote.'; }
window.addEventListener('hfl:analysis-stage',event=>{if(event.detail!=='workflow')invalidate();});
async function api(path, payload) {
  if(payload!==undefined && readonly())throw Error('Execução somente leitura nesta visualização.');
  let url='/api/radar/'+path;
  const run=encodeURIComponent(runId());
  if(path==='budget')url='/api/platform/radar-budget?run='+run;
  if(path==='budget-authorization')url='/api/platform/radar-budget-authorization';
  if(path==='status')url='/api/platform/radar-view?run='+run;
  if(path.startsWith('detail?'))url='/api/platform/radar-detail?run='+run+'&'+path.slice(7);
  const response = await fetch(url, payload === undefined ? {signal:aborter.signal} : {method:'POST', signal:aborter.signal, headers:{'Content-Type':'application/json','X-CSRF-Token':csrf,'X-HFL-Radar-Run':state.run.id}, body:JSON.stringify(payload)});
  const value = await response.json();
  if (!response.ok) throw new Error(value.error || 'Falha ao consultar radar.');
  return value;
}
const modeLabel = value => value === 'synthetic' ? 'SINTÉTICO · OFFLINE' : 'B3 · AJUSTADO';
const runStates = {INCIDENT_PRESERVED:'Incidente preservado',INPUTS_READY:'Inputs prontos · orçamento agregado exige autorização separada',AWAITING_AUTHORIZATION:'Inputs prontos · aguardando autorização paga',RUNNING:'Em execução',COMPLETED:'Concluída',PARTIAL:'Parcial',RECOVERY_REQUIRED:'Recuperação offline necessária',BLOCKED:'Bloqueada',INTEGRITY_ERROR:'Integridade divergente'};
const authLabels = {VALID:'autorização de orçamento registrada',ABSENT:'autorização de orçamento ausente',STALE:'autorização anterior não cobre a exposição atual',NOT_REQUIRED:'dentro do limite agregado',INTEGRITY_ERROR:'autorização com integridade divergente'};
const forensic = value => ({LOCAL_BLOCK_BEFORE_CONNECT_BILLING_UNCONFIRMED:'bloqueio local antes da conexão · cobrança no provedor não confirmada',SETTLED:'liquidada por resultados gravados'}[value] || 'resultado incerto · cobrança desconhecida');
function runOption(r){ return `${r.id} · ${r.session} · ${runStates[r.state]||r.state} · ${r.opinions}/${r.universe.length} pareceres${r.incident?' · INCIDENTE':''}${r.selected?' · padrão':''}`; }
function renderRun() {
  const r = state.run, money = r.budget;
  $('run-card').dataset.state = r.state;
  const others = money ? money.runs.filter(x => x.run !== r.id && x.usd_reserved > 0) : [];
  $('run-card').innerHTML = `<h2>${escape(r.id)}</h2>`
    + (r.incident ? `<p class="run-incident"><strong>${escape(r.incident.classification)}</strong><br>${escape(r.incident.id)} · ${escape(r.incident.billing)} Evidência: ${escape(r.incident.evidence)}</p>` : '')
    + `<div><span>Sessão</span><strong>${escape(r.session)}</strong></div><div><span>Origem</span><strong>${escape(r.source)}</strong></div><div><span>Estado</span><strong>${escape(runStates[r.state]||r.state)}</strong>${r.reasons.length?`<small class="warning">${r.reasons.map(escape).join(' · ')}</small>`:''}</div><div><span>Pareceres completos</span><strong>${r.opinions}/${r.universe.length}</strong></div>`
    + `<div><span>Classificação</span><strong>${escape(r.classification)}${r.same_treatment_as?' · mesma identidade de tratamento de '+escape(r.same_treatment_as):''}</strong></div><div><span>Preparação</span><strong>${escape(dateTime(r.prepared_at))}</strong></div><div><span>Inputs / claims / falhas</span><strong>${r.inputs} / ${r.claims} / ${r.failures}</strong></div><div><span>Chamadas reservadas / respostas</span><strong>${r.calls_reserved} / ${r.responses_recorded}</strong></div>`
    + (money ? `<p class="run-budget">Orçamento próprio US$ ${cash(r.budget_usd)} · reservado US$ ${cash(r.usd_reserved)} (incerto US$ ${cash(r.usd_reserved_uncertain)}) · custo observado pelos tokens US$ ${cash(r.usd_observed_provider_tokens)} · faturado confirmado: não disponível.<br>${others.map(x => `Outra execução ${escape(x.run)}${x.incident?' ('+escape(x.incident)+')':''}: reserva US$ ${cash(x.usd_reserved)} · ${x.reservations.map(b => escape(forensic(b.forensic))).join(', ')} · não liberada.`).join('<br>')}${others.length?'<br>':''}Próximo lote: até ${money.planned.calls_max} chamadas (${money.planned.calls_planned} planejadas) · reserva US$ ${cash(money.planned.usd_reserved)} · exposição agregada conservadora US$ ${cash(money.aggregate_exposure_usd)} / limite local US$ ${cash(money.aggregate_cap_usd)} · ${escape(authLabels[money.authorization.state]||money.authorization.state)}.</p>` : '<p class="run-budget">Execução sintética: sem provedor e sem orçamento.</p>')
    + `<p>Tratamento <code>${escape(r.treatment?.identity)}</code> · modelo ${escape(r.treatment?.model)}</p><div class="market-hashes">${M.copy('Manifesto do tratamento',r.treatment?.manifest_sha256)}</div>`
    + (r.comparison ? `<p class="run-budget">Comparação econômica com ${escape(r.comparison.reference)}: ${r.comparison.material?'<strong class="warning">divergência material · bloqueada</strong>':'equivalente'} (${r.comparison.items.map(i=>escape(i.ticker+' '+i.status)).join(' · ')})</p>` : '');
}
function renderUniverse() {
  $('universe-count').innerHTML = `${state.universe.length} <small>/ 5 ativos</small>`;
  $('universe').innerHTML = state.universe.length ? state.universe.map(ticker => {
    const latest = state.items.filter(i => i.ticker === ticker).sort((a,b) => b.session.localeCompare(a.session))[0];
    return `<article class="asset"><div class="asset-top"><label><input type="checkbox" data-ticker="${escape(ticker)}" ${selected.has(ticker) ? 'checked' : ''}>${escape(ticker)}</label><button class="remove" ${readonly()?'disabled':''} data-remove="${escape(ticker)}" aria-label="Remover ${escape(ticker)}">×</button></div><small>${latest ? 'Dados: ' + escape(latest.session) + '<br>' + modeLabel(latest.mode) : 'Sem dados preparados'}</small></article>`;
  }).join('') : '<p class="muted">Nenhum ativo no universo desta execução.</p>';
  $('prepare').disabled = $('preflight').disabled = readonly() || !selected.size || !!state.job && state.job.status === 'RUNNING';
}
function renderResults() {
  const rows = state.items.filter(row => (!query.get('asset') || row.ticker===query.get('asset')) && (!$('filter-signal').value || M.available(row) && row.technical_signal?.signal===$('filter-signal').value) && (!$('filter-risk').value || M.available(row) && row.risk?.verdict===$('filter-risk').value) && (!$('filter-final').value || M.available(row) && row.recommendation===$('filter-final').value));
  $('filter-count').textContent = `${rows.length} de ${state.items.length} análises · filtros somente de leitura`;
  $('results').innerHTML = rows.length ? rows.map(row => { const ok=M.available(row), c=row.consensus; return `<tr><th scope="row"><button class="ds-btn" data-detail="${escape(row.ticker)}|${escape(row.session)}" ${row.status==='INTEGRITY_ERROR' ? 'disabled' : ''}>${escape(row.ticker)}</button><small>${escape(row.session)}</small></th><td>${M.badge(ok ? row.technical_signal?.signal : null)}<small>Confiança: ${ok ? M.number(row.technical_signal?.confidence,3) : '—'}</small></td><td>${ok && c ? `${escape(c.counts[c.winning_signal])}/${escape(c.total_analysts)} · ${c.consensus_reached ? 'atingido' : 'não atingido'}` : 'Indisponível'}</td><td>${M.badge(ok ? row.risk?.verdict : null)}<small>${row.risk_source==='HARD_ASSET_VOLATILITY_RULE' ? 'Regra determinística' : row.risk_source==='ADVISORY_LLM' ? 'Parecer LLM' : 'Origem indisponível'}</small></td><td>${M.badge(ok ? row.recommendation : null)}</td><td>${escape(row.status)}</td></tr>`; }).join('') : '<tr><td colspan="6" class="ds-empty">Nenhuma análise corresponde aos filtros ou não há parecer registrado. Limpe os filtros para conferir o universo.</td></tr>';
  const options = '<option value="">Selecione</option>' + state.items.filter(i => i.status === 'COMPLETED').map(i => `<option value="${escape(i.ticker)}|${escape(i.session)}">${escape(i.ticker)} · ${escape(i.session)} · ${modeLabel(i.mode)}</option>`).join('');
  ['compare-a','compare-b'].forEach(id => { const previous = $(id).value; $(id).innerHTML = options; $(id).value = previous; });
}
async function refresh(first=false) {
  const version=viewVersion,next=await api('status');if(version!==viewVersion)return;state=next;csrf=state.csrf_token;
  state.universe = state.run.universe; // the run's registered identity, not the operational universe.json
  if (first) {
    const requested=(query.get('tickers')||'').split(',').filter(Boolean);
    if(requested.length>5||requested.some(t=>!/^([A-Z]{4}[3-8])$/.test(t))||new Set(requested).size!==requested.length)throw Error('Seleção inválida.');
    // A run has one session and one universe; other tickers are outside its identity.
    selected = new Set((requested.length?requested:state.run.universe).filter(t=>state.run.universe.includes(t)));
    $('ticker-options').innerHTML = state.examples.map(t => `<option value="${escape(t)}"></option>`).join('');
  }
  $('session').value = state.run.session; $('session').disabled = true;
  $('mode').value = synthetic() ? 'synthetic' : 'live'; $('mode').disabled = true;
  $('budget').max = state.run.budget_usd; if(first) $('budget').value = state.run.budget_usd;
  $('closed').textContent = state.last_closed_session;
  $('budget-used').innerHTML = synthetic() ? 'US$ 0 <small>sintético</small>' : `${cash(state.run.usd_reserved)} <small>/ ${cash(state.run.budget_usd)}</small>`;
  $('job').textContent = state.job ? `${state.job.command} · ${state.job.outcome ? state.job.outcome.summary : state.job.status}` : 'Nenhuma execução ativa';
  $('job').classList.toggle('warning', !!state.job?.outcome && state.job.outcome.state !== 'COMPLETED');
  $('radar-source').textContent = (synthetic() ? 'DEMONSTRAÇÃO SINTÉTICA · resultados fixos · sem chamadas ou gravações.' : 'CONSULTIVO COM GEMINI · registros desta execução apenas.') + (readonly() ? ` Somente leitura: execução operacional do servidor é ${state.runner || 'nenhuma'}.` : ' Execução operacional do servidor.') + (isolated() ? '' : ' Servidor sem isolamento de rede por requisição: reinicie-o antes de qualquer execução paga.');
  $('add-form').querySelectorAll('input,button').forEach(e=>e.disabled=readonly());
  transfer();renderRun();renderUniverse(); renderResults();
  $('radar-overview').innerHTML = [['Sessão de referência '+M.help('sessao-referencia'),escape(state.run.session)],['Origem '+M.help('parecer-oficial'),escape(state.run.classification)],['Estado',escape(runStates[state.run.state]||state.run.state)],['Pareceres completos',`${state.run.opinions}/${state.run.universe.length}`]].map(([label,value])=>`<article class="ds-kpi"><span class="ds-kpi-label">${label}</span><strong class="ds-kpi-value">${value}</strong></article>`).join('');
  $('radar-assets').innerHTML=state.run.universe.map(t=>M.summary(state.items.find(i=>i.ticker===t && i.session===state.run.session)||{ticker:t,session:state.run.session,status:'NONE'},runId(),'/radar')).join('');
  $('filter-asset').innerHTML='<option value="">Todos</option>'+state.run.universe.map(t=>`<option>${escape(t)}</option>`).join(''); $('filter-asset').value=query.get('asset')||'';
  if (state.job?.status === 'RUNNING' && !poll) poll = setInterval(() => refresh().catch(error), 2000);
  if (state.job?.status !== 'RUNNING' && poll) { clearInterval(poll); poll = null; }
  if (state.job?.command === 'prepare' && state.job.status === 'RUNNING') {
    report=null; $('confirmation').hidden=true; $('paid').checked=false;
    $('preflight-result').textContent='Preparação em andamento. Aguarde sua conclusão antes de verificar os requisitos.';
  }
  $('error').hidden=true;
  if (!readonly() && !(state.job?.command === 'prepare' && state.job.status === 'RUNNING') && state.last_prepare?.items.some(i => i.status === 'BLOCKED')) {
    const blocked=state.last_prepare.items.filter(i=>i.status==='BLOCKED');
    $('error').textContent = 'Preparo de ' + dateTime(state.last_prepare.generated_at) + ' bloqueado para '+blocked.map(i=>i.ticker).join(', ')+': '+[...new Set(blocked.map(i=>i.error))].join(' · ')+'. Ver diagnóstico por ativo abaixo. Nenhum agente foi executado.'; $('error').hidden = false;
  }
  await inputs(version);
  if(version!==viewVersion)return;
  if ($('guided-check')) $('guided-check').disabled=readonly()||!selected.size||state.job?.status==='RUNNING';
  if(guided?.run===runId()) {
    if(state.job?.status==='RUNNING') $('guided-status').textContent='Preparando os dados. Aguarde a coleta e a validação; nenhuma chamada de IA foi feita.';
    else {
      guided=null;
      await reviewPreflight();
      $('guided-status').textContent=report?.ready?'Dados prontos. Revise o custo e as autorizações abaixo.':'Os dados ainda não estão prontos. Confira o diagnóstico abaixo; nenhum agente foi executado.';
      if($('diagnostic-details'))$('diagnostic-details').open=!report?.ready;
    }
  }
  if(first && query.get('asset')) {
    const row=state.items.find(i=>i.ticker===query.get('asset') && i.session===state.run.session);
    if(row) await openDetail(row.ticker,row.session);
  }
}
const pct = v => (Number(v) * 100).toLocaleString('pt-BR', {maximumFractionDigits: 1}) + '%';
const inputLabels = {FROZEN:'Input congelado', PREPARING:'Preparo em andamento', PREPARATION_REQUIRED:'Preparação necessária', UNRESOLVED_DIVERGENCE:'Divergência não resolvida', BLOCKED_DATA:'Dados bloqueados', INTEGRITY_ERROR:'Integridade divergente'};
const opinionLabels = {PENDING:'Parecer pendente', COMPLETED:'Parecer concluído', RECOVERY_REQUIRED:'Recuperação offline', NONE:'Sem parecer'};
const outcomeLabels = {COMMITTEE_COMPLETED:'Comitê concluído', COMMITTEE_PARTIAL:'Comitê parcial', RECOVERABLE_OFFLINE:'Falha recuperável offline', NO_RECOVERABLE_ENVELOPE:'Falha sem envelope recuperável', UNCERTAIN_CALLS:'Chamada de resultado incerto'};
const billingLabels = {PROVIDER_USAGE_RECORDED:'uso registrado pelo provedor', SYNTHETIC_NO_PROVIDER:'sintético, sem provedor', NO_SEND_EVIDENCE:'bloqueio local antes da conexão; cobrança a confirmar no provedor', UNKNOWN:'cobrança desconhecida'};
const preflightLabels = {READY:'pronto', PREPARING:'aguardar preparo', INPUT_REQUIRED:'preparar dados', gemini_api_key_missing:'chave Gemini ausente no servidor', inference_already_reserved_replay_only:'já reservado · só recuperação'};
function normalization(input) {
  if (!input) return '—';
  const n = input.normalization;
  return n.state === 'NORMALIZED_CONFIRMED_EVENT' ? 'Normalizado: ' + n.events.map(e => `bonificação ${escape(e.ex_date)} ×${escape(e.yfinance_split_ratio)} (${escape(e.b3_especi)}, DISMES ${escape(e.b3_dismes.join('→'))})`).join('; ') : 'Sem normalização necessária';
}
function riskCell(row) {
  const r = row.input?.risk;
  if (!r) return '—';
  const text = `Vol. 21d ${pct(r.asset_volatility_21)} · limite ${pct(r.limit)}`;
  return (r.restricted ? `<strong class="warning">Restrição individual</strong><small>${text}; veto determinístico esperado</small>` : `<span>Sem restrição</span><small>${text}</small>`) + `<small>${row.risk_verdict ? 'Risk: ' + escape(row.risk_verdict) : 'Risk ainda não avaliado'}</small>`;
}
async function inputs(version) {
  const box = $('input-check');
  if (!selected.size) { box.hidden = true; return; }
  const response = await fetch('/api/platform/radar-readiness?' + new URLSearchParams({run: runId(), session: $('session').value, tickers: chosen().join(',')}), {signal:aborter.signal});
  const d = await response.json();
  if (version !== viewVersion) return;
  if (!response.ok) { box.innerHTML = '<p class="warning">Conferência dos inputs indisponível.</p>'; box.hidden = false; return; }
  box.innerHTML = `<p><strong>Conferência dos inputs · ${escape(d.summary)}</strong> · execução ${escape(d.run)} · sessão ${escape(d.session)} · Gestor Global ${d.global_pm_ready ? 'elegível' : 'bloqueado até existirem todos os pareceres'}</p><div class="table-scroll input-check" tabindex="0" role="region" aria-label="Conferência dos inputs, tabela rolável"><table><thead><tr><th>Ativo</th><th>Input</th><th>Dados</th><th>Parecer</th><th>Risco individual</th><th>Preflight / próxima ação</th></tr></thead><tbody>${d.items.map(i => `<tr><td data-label="Ativo"><strong>${escape(i.ticker)}</strong></td><td data-label="Input">${escape(inputLabels[i.input_state] || i.input_state)}${i.input ? `<small>${i.input.bars} barras desde ${escape(i.input.history_start)} · ${modeLabel(i.input.mode)}</small><small>SHA ${escape(i.input.input_sha256.slice(0, 12))}…</small>` : ''}</td><td data-label="Dados">${normalization(i.input)}${i.input ? `<small>Bruto R$ ${escape(i.input.raw_close)} · ajustado R$ ${escape(i.input.adjusted_close)}</small>` : ''}${i.error ? `<small class="warning">${escape(i.error)}</small>` : ''}</td><td data-label="Parecer">${escape(opinionLabels[i.opinion] || i.opinion)}${i.outcome && i.outcome.state !== 'COMMITTEE_COMPLETED' ? `<small class="warning">${escape(outcomeLabels[i.outcome.state] || i.outcome.state)} · ${escape(i.outcome.calls_reserved)} chamadas reservadas</small><small>${escape(billingLabels[i.outcome.billing] || i.outcome.billing)}</small>` : ''}</td><td data-label="Risco individual">${riskCell(i)}</td><td data-label="Preflight">${escape(preflightLabels[i.preflight] || i.preflight || '—')}<small>${escape(i.action)}</small></td></tr>`).join('')}</tbody></table></div><p class="muted small">Preparar dados e executar análises são ações independentes: preparar é gratuito e não chama Gemini. Input íntegro não é parecer favorável; o Risk só existe após o comitê. Preparo pelo CLI: <code>${escape(d.prepare_command)}</code></p>`;
  box.hidden = false;
  return d;
}
function guarded(handler) { return async event => { $('error').hidden = true; try { await handler(event); } catch(exc) { error(exc); } }; }
$('add-form').addEventListener('submit', guarded(async event => {
  event.preventDefault(); const ticker = $('ticker-search').value.toUpperCase().replace(/\.SA$/, '');
  await api('universe', {tickers:[...state.universe,ticker]}); selected.add(ticker); $('ticker-search').value = ''; invalidate(); await refresh();
}));
let searchTimer;
$('ticker-search').addEventListener('input', () => { clearTimeout(searchTimer); searchTimer = setTimeout(async () => { try { const result = await api('search?q=' + encodeURIComponent($('ticker-search').value)); $('ticker-options').innerHTML = result.tickers.map(t => `<option value="${escape(t)}"></option>`).join(''); $('catalog-note').textContent = result.note; } catch(exc) { error(exc); } }, 350); });
$('universe').addEventListener('change', event => { const ticker=event.target.dataset.ticker; if(ticker) { event.target.checked ? selected.add(ticker) : selected.delete(ticker); invalidate(); renderUniverse(); inputs(viewVersion).catch(error); } });
$('universe').addEventListener('click', guarded(async event => { const ticker=event.target.closest('[data-remove]')?.dataset.remove; if(ticker) { await api('universe',{tickers:state.universe.filter(t=>t!==ticker)}); selected.delete(ticker); invalidate(); await refresh(); } }));
['budget','replay'].forEach(id => $(id).addEventListener('change', invalidate));
$('prepare').addEventListener('click', guarded(async () => { invalidate(); await api('prepare',{tickers:chosen(),session:$('session').value,mode:$('mode').value}); await refresh(); }));
$('guided-check')?.addEventListener('click',guarded(async()=>{
  if(readonly()||!selected.size||state.job?.status==='RUNNING')return;
  invalidate();$('guided-check').disabled=true;
  $('guided-status').textContent='Iniciando a preparação dos dados; esta etapa não executa agentes.';
  try{await api('prepare',{tickers:chosen(),session:$('session').value,mode:$('mode').value});guided={run:runId()};await refresh();}
  catch(e){guided=null;$('guided-check').disabled=false;throw e;}
}));
function budgetBlocked() { const a = state?.run?.budget?.authorization; return !!a && a.required && a.state !== 'VALID'; }
async function reviewPreflight() {
  const version=viewVersion, readiness=await inputs(version);if(version!==viewVersion)return;
  if(readiness?.items.some(i=>i.input_state==='PREPARING')) {
    report=null; $('confirmation').hidden=true; $('paid').checked=false;
    $('preflight-result').textContent='Preparação em andamento. Aguarde sua conclusão antes de verificar os requisitos.';
    return;
  }
  const reasons=new Map((readiness?.items||[]).filter(i=>['BLOCKED_DATA','UNRESOLVED_DIVERGENCE','PREPARATION_REQUIRED'].includes(i.input_state)).map(i=>[i.ticker,[i.error,i.action].filter(Boolean).join(' · ')]));
  const [next,money]=await Promise.all([api('preflight',selection()),api('budget')]);if(version!==viewVersion)return;report=next;state.run.budget=money;
  const old = money ? money.runs.filter(x => x.run !== state.run.id && x.usd_reserved > 0) : [];
  $('preflight-result').innerHTML = `<p><strong>${report.ready ? budgetBlocked()?'Dados prontos · revisão de orçamento pendente':'Preflight Radar aprovado' : 'Preflight bloqueado'}</strong> · execução ${escape(state.run.id)} · sessão ${escape(report.session)}</p><ul>${report.items.map(i=>`<li>${escape(i.ticker)}: ${i.ready ? 'pronto · ' + modeLabel(i.mode) : escape(reasons.get(i.ticker) || i.error)}</li>`).join('')}</ul><p>Estimativa do lote: <strong>US$ ${cash(report.usd_estimated)}</strong> · Teto reservado: <strong>US$ ${cash(report.usd_reserved)}</strong> · Reservas já registradas nesta execução: US$ ${cash(report.global_budget_used)} · Orçamento da execução: US$ ${cash(state.run.budget_usd)}.</p>${money ? `<p>${old.map(x => `Execução ${escape(x.run)}: reserva US$ ${cash(x.usd_reserved)} · ${x.reservations.map(b => escape(forensic(b.forensic))).join(', ')} · valor reservado, não custo faturado.`).join('<br>')}${old.length?'<br>':''}Exposição agregada conservadora após este lote: <strong>US$ ${cash(money.aggregate_exposure_usd)}</strong> / limite local US$ ${cash(money.aggregate_cap_usd)} · até ${money.planned.calls_max} chamadas, ${money.planned.calls_planned} planejadas · ${escape(authLabels[money.authorization.state]||money.authorization.state)}.</p>` : ''}<p class="muted">Até 6 chamadas por ativo (5 analistas + Risk; Risk dispensado por veto determinístico). Estimativa baseada em 2.500 tokens de entrada e 800 de saída por chamada. Reserva conservadora: 32.768 de entrada e 8.192 de saída, incluindo pensamento, sem retries automáticos. <a href="https://ai.google.dev/gemini-api/docs/pricing" target="_blank" rel="noreferrer">Tarifas e hipóteses</a>.</p>${report.usd_reserved > report.max_usd || report.global_budget_used + report.usd_reserved > report.global_budget_cap ? '<p class="warning">Orçamento insuficiente para a reserva conservadora do lote.</p>' : ''}${budgetBlocked() && !report.replay ? '<p class="warning">Exposição agregada acima do limite local sem autorização de orçamento separada: revise e autorize os valores no painel abaixo antes de confirmar o lote.</p>' : ''}`;
  $('confirmation').hidden = !report.ready;
  const paid = !report.replay && report.items.some(i=>i.mode==='live');
  $('paid').closest('label').hidden = !paid; $('paid').checked = false; $('execute').disabled = paid || !isolated() || readonly();
  $('execute').textContent = report.replay ? '3. Confirmar recuperação offline' : paid ? '3. Confirmar e executar chamadas pagas' : '3. Executar exemplo sintético · US$ 0'; $('execute').dataset.action = report.replay ? 'read' : paid ? 'paid' : 'simulate';
  renderBudgetReview();
}
$('preflight').addEventListener('click', guarded(reviewPreflight));
function renderBudgetReview() {
  const money=state.run.budget, show=report?.ready&&!report.replay&&budgetBlocked();
  $('budget-review').hidden=!show;$('budget-consent').checked=false;
  if(!show)return;
  $('aggregate-budget').value='';$('aggregate-budget').min=String(money.aggregate_exposure_usd);
  $('budget-review-summary').textContent=`Execução ${state.run.id} · sessão ${state.run.session.split('-').reverse().join('/')} · ativos ${money.planned.tickers.join(', ')}. Reservas anteriores: US$ ${cash(money.other_runs_reserved_usd)}. Reserva desta execução: US$ ${cash(money.run_reserved_usd)}. Novo lote: US$ ${cash(money.planned.usd_reserved)}. Exposição agregada: US$ ${Number(money.aggregate_exposure_usd).toFixed(6)}. Limite geral atual: US$ ${cash(money.aggregate_cap_usd)}. Reservas não são cobrança confirmada.`;
  updateBudgetControl();
}
function updateBudgetControl() {
  const money=state?.run?.budget,limit=Number($('aggregate-budget').value);
  const scope=money?.planned.tickers.length===selected.size&&money.planned.tickers.every(t=>selected.has(t));
  const valid=money&&Number.isFinite(limit)&&limit>0&&limit>=money.aggregate_exposure_usd;
  $('budget-authorize').disabled=budgetPosting||readonly()||!report?.ready||!$('budget-consent').checked||!valid||!scope;
  $('budget-review-status').textContent=!scope?'Esta autorização cobre todos os ativos pendentes indicados. Selecione esse conjunto e refaça o preflight.':!valid?'Informe um teto que cubra a exposição agregada apresentada.':'O registro de orçamento não executa chamadas. A confirmação paga do lote continua na etapa 3.';
}
['aggregate-budget','budget-consent'].forEach(id=>$(id).addEventListener('input',updateBudgetControl));
$('budget-authorize').addEventListener('click',guarded(async()=>{
  updateBudgetControl();if($('budget-authorize').disabled)return;
  const version=viewVersion,payload={run:runId(),budget_token:state.run.budget.budget_token,max_aggregate_usd:Number($('aggregate-budget').value),confirm:true};
  budgetPosting=true;$('budget-authorize').disabled=true;$('execute').disabled=true;
  try{
    await api('budget-authorization',payload);
    if(version!==viewVersion)return;
    invalidate();await refresh();await reviewPreflight();
  }catch(e){if(version===viewVersion)invalidate();throw e;
  }finally{budgetPosting=false;}
}));
$('paid').addEventListener('change', () => { $('execute').disabled = !report?.ready || !$('paid').checked || !isolated() || budgetBlocked() || readonly() || budgetPosting; });
$('execute').addEventListener('click', guarded(async () => {
  if(!report?.ready) throw new Error('Refaça o preflight.');
  const current=report, version=viewVersion;
  const payload={...selection(),confirmation_token:current.confirmation_token,authorize_paid:$('paid').checked,confirm:true};
  const paid=!current.replay && current.items.some(i=>i.mode==='live');
  if(paid) {
    if(!payload.authorize_paid || !isolated() || budgetBlocked() || readonly())throw Error('explicit_paid_authorization_required');
    const accepted=await window.HFL.confirmCost({ready:current.ready,operation:'Comitês Radar · '+chosen().join(', '),treatment:current.identity,context:current.session+' · '+current.items.map(i=>i.ticker+': '+i.input_sha256).join(' · '),run:runId(),source:'POST /api/radar/preflight',confirmationToken:current.confirmation_token,callsMax:current.items.reduce((n,i)=>n+(i.estimate?.calls_max||0),0),estimatedUsd:current.usd_estimated,reservedUsd:current.usd_reserved,remainingUsd:Math.max(0,Math.min(state.run.budget_usd-state.run.usd_reserved,current.global_budget_cap-current.global_budget_used))});
    if(!accepted)return;
    if(version!==viewVersion || report!==current || !isolated() || budgetBlocked() || readonly())throw Error('preflight_or_confirmation_changed');
  }
  invalidate(); await api('run',payload); await refresh();
}));
$('refresh').addEventListener('click', guarded(() => refresh()));
const detailHtml = (row, compact=false) => M.detail(row,runId(),compact);
async function openDetail(ticker, session) {
  const version=viewVersion, row=await api(`detail?ticker=${encodeURIComponent(ticker)}&session=${encodeURIComponent(session)}`);
  if(version!==viewVersion)return;
  $('room-content').innerHTML=detailHtml(row); $('room').hidden=false;
  query.set('asset',ticker); syncUrl();
  $('room-title').focus({preventScroll:true}); $('room').scrollIntoView({block:'start'});
}
$('results').addEventListener('click', guarded(async event => {
  const key=event.target.closest('[data-detail]')?.dataset.detail;
  if(key) await openDetail(...key.split('|'));
}));
function syncUrl() {
  query.set('run',runId());
  history.replaceState(null,'','/radar?'+query+location.hash);
  window.dispatchEvent(new PopStateEvent('popstate'));
}
['asset','signal','risk','final'].forEach(key=>{
  $('filter-'+key).value=query.get(key)||'';
  $('filter-'+key).addEventListener('change',()=>{
    const value=$('filter-'+key).value; value ? query.set(key,value) : query.delete(key);
    syncUrl(); renderResults();
  });
});
$('clear-filters').addEventListener('click',()=>{
  ['asset','signal','risk','final'].forEach(key=>{query.delete(key);$('filter-'+key).value='';});
  syncUrl();renderResults();
});
$('close-room').addEventListener('click',()=>{$('room').hidden=true; query.delete('asset'); $('filter-asset').value=''; syncUrl(); renderResults(); $('results-title').tabIndex=-1; $('results-title').focus();});
$('compare').addEventListener('click', guarded(async () => {
  const keys=[$('compare-a').value,$('compare-b').value];
  const rows=keys.map(key=>state.items.find(i=>i.ticker+'|'+i.session===key));
  if(rows.some(r=>!r) || rows[0].ticker===rows[1].ticker) throw new Error('Selecione duas empresas diferentes.');
  if(rows[0].session!==rows[1].session || rows[0].mode!==rows[1].mode) { $('comparison').textContent=`Comparação bloqueada: sessões ou fontes diferentes (${rows[0].ticker}: ${rows[0].session}, ${modeLabel(rows[0].mode)}; ${rows[1].ticker}: ${rows[1].session}, ${modeLabel(rows[1].mode)}). Selecione a mesma sessão e fonte.`; return; }
  $('comparison').innerHTML=`<p class="muted small">Mesma execução ${escape(state.run.id)} e sessão ${escape(rows[0].session)}; as gerações ocorreram nos horários individuais abaixo.</p><div class="side-by-side">${rows.map(r=>`<article class="comparison-card">${detailHtml(r,true)}</article>`).join('')}</div>`;
}));
function choose(id) {
  guided=null;
  // Cancel every pending request of the previous run: no record of two runs is mixed.
  aborter.abort(); aborter = new AbortController(); state = null; selected = new Set();
  if (poll) { clearInterval(poll); poll = null; }
  invalidate(); $('error').hidden=true; $('room').hidden=true; $('comparison').textContent=''; $('input-check').hidden=true; $('run-card').innerHTML='';
  $('results').innerHTML='<tr><td colspan="7">Consultando a execução selecionada…</td></tr>'; $('radar-source').textContent='Consultando execução…'; $('prepare').disabled=$('preflight').disabled=true;
  query.set('run',id); syncUrl(); $('radar-assets').replaceChildren(); $('radar-overview').replaceChildren();
  return refresh(true);
}
$('radar-run').addEventListener('change',()=>{ ['asset','signal','risk','final'].forEach(k=>{query.delete(k);$('filter-'+k).value='';}); choose(runId()).catch(error); });
async function start() {
  const response = await fetch('/api/platform/radar-runs', {signal:aborter.signal});
  const value = await response.json();
  if (!response.ok) { $('radar-run').innerHTML='<option value="">Registro indisponível</option>'; $('radar-run').disabled=true; $('prepare').disabled=$('preflight').disabled=true; $('add-form').querySelectorAll('input,button').forEach(e=>e.disabled=true); $('radar-source').textContent='Nenhuma execução selecionada · operações bloqueadas.'; throw Error(value.error || 'registry_unavailable'); }
  runs = value;
  $('radar-run').innerHTML = runs.runs.map(r => `<option value="${escape(r.id)}">${escape(runOption(r))}</option>`).join('');
  const wanted = query.get('run') || (query.get('mode')==='SYNTHETIC_DEMO' ? runs.runs.find(r=>r.mode==='SYNTHETIC_DEMO')?.id : runs.selected);
  if (!runs.runs.some(r => r.id === wanted)) throw Error('unknown_radar_run');
  $('radar-run').value = wanted;
  await choose(wanted);
}
start().catch(error);
