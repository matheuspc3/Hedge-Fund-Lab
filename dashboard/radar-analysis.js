'use strict';
(() => {
  const el = id => document.getElementById(id), form = el('new-analysis-form');
  if (!form) return;
  const esc = v => String(v ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const day = v => v.split('-').reverse().join('/');
  const labels = {FUTURE_ANALYSIS:'Análise para sessão futura',SAME_DAY_ANALYSIS:'Análise para hoje',HISTORICAL_REANALYSIS:'Reanálise histórica — criada agora'};
  const errors = {analysis_wallet_changed_reload:'A carteira mudou. Atualize a página e revise a seleção.',analysis_reference_must_be_closed_before_target:'Escolha uma sessão de dados já encerrada e anterior ao dia-alvo.',analysis_target_not_a_planned_session:'O dia-alvo precisa ser uma sessão do calendário disponível.',analysis_target_before_wallet_start:'O dia-alvo é anterior ao início dessa carteira.',radar_busy_or_stale_lock:'Há uma preparação/análise em andamento ou um bloqueio de recuperação. Consulte o Radar antes de criar outra.',analysis_wallet_not_found:'Carteira indisponível. Atualize a página.'};
  errors.analysis_multiagent_requires_full_universe = 'A Multiagentes acompanha os cinco ativos mesmo com posição zerada. Atualize a página para carregar o universo completo.';
  let options, command = crypto.randomUUID().replaceAll('-',''), busy = false, revision = 0;
  const cycle = analysis => window.dispatchEvent(new CustomEvent('hfl:cycle',{detail:{analysis}}));
  async function api(query='', payload) {
    const response = await fetch('/api/platform/radar-analysis'+query, payload ? {method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':options.csrf_token},body:JSON.stringify(payload)} : {cache:'no-store'});
    const value = await response.json();
    if (!response.ok) throw Error(errors[value.error] || value.error || 'Consulta indisponível.');
    return value;
  }
  function history() {
    const rows = options.history.filter(r=>r.wallet===el('analysis-wallet').value).reverse();
    el('analysis-history').innerHTML = rows.length ? '<ul>'+rows.map(r=>`<li><a href="/radar?run=${encodeURIComponent(r.run)}">Alvo ${day(r.target_date)} · dados ${day(r.reference_session)} · ${esc(labels[r.classification])}</a><br><small>Registrada em ${esc(new Date(r.created_at).toLocaleString('pt-BR',{timeZone:'America/Sao_Paulo'}))}</small></li>`).join('')+'</ul>' : '<p>Nenhuma análise vinculada a esta carteira. As execuções anteriores continuam no seletor do Radar.</p>';
  }
  function wallet() {
    const w = options.wallets.find(w=>w.id===el('analysis-wallet').value);
    el('analysis-tickers').value = (w?.analysis_tickers || options.examples).join(', ');
    el('analysis-tickers').readOnly = w?.strategy === 'MULTIAGENT';
    el('analysis-wallet-state').textContent = w ? `${w.nature_label} · caixa R$ ${Number(w.cash).toLocaleString('pt-BR',{minimumFractionDigits:2})} · ${w.positions.length} posição(ões). O estado atual será preservado com esta análise.` : 'Crie uma carteira na página inicial para começar.';
    if (w?.strategy === 'MULTIAGENT') el('analysis-wallet-state').textContent += ' Os cinco ativos continuam em análise mesmo com posição zerada, permitindo novas compras.';
    history();
  }
  function reference() {
    const target = el('analysis-target').value;
    const days = options.sessions.filter(d=>d<target && d<=options.reference_session);
    el('analysis-reference').value = days.at(-1) || '';
    el('analysis-reference').max = days.at(-1) || options.reference_session;
    el('analysis-date-note').textContent = target < options.today ? 'Reanálise histórica com dados obtidos agora e o estado atual da carteira. Não será apresentada como previsão feita no passado.' : 'A data dos dados é anterior ao alvo. Preparar confirma a disponibilidade; o calendário não garante que os preços já foram publicados.';
    if (options.reference_note && el('analysis-reference').value === options.reference_session) el('analysis-date-note').textContent += ' ' + options.reference_note; // B3 has not published the last closed session yet
  }
  async function context(run) {
    const version = ++revision, box = el('analysis-context');
    box.hidden = true;
    el('analysis-return').hidden = true;
    el('radar-to-global').hidden = run.startsWith('radar-ui-');
    cycle(undefined);
    try {
      const d = await api('?'+new URLSearchParams({run}));
      if (version !== revision) return;
      const c = d.context;
      cycle(c?{wallet:c.wallet.name,target:c.target_date,reference:c.reference_session,created:c.created_at,changed:d.wallet_changed}:null);
      if (!c) return;
      el('radar-to-global').hidden = true;
      el('analysis-return').href = '/?'+new URLSearchParams({wallet:c.wallet.id});
      el('analysis-return').hidden = false;
      box.textContent = `${c.wallet.name} · ${labels[c.classification]} ${day(c.target_date)} · dados até ${day(c.reference_session)}. Carteira preservada em ${new Date(c.created_at).toLocaleString('pt-BR',{timeZone:'America/Sao_Paulo'})}. Após o quórum, prepare o gestor em Resultados para obter uma proposta com quantidades.${d.wallet_changed?' A carteira mudou desde este registro; abra outra análise para movimentar o estado atual. O contexto original continua preservado.':''}`;
      box.hidden = false;
    } catch (e) { if(version===revision){cycle(null);box.textContent='Contexto da análise indisponível: '+e.message;box.hidden=false;} }
  }
  el('analysis-wallet').addEventListener('change',()=>{command=crypto.randomUUID().replaceAll('-','');wallet();});
  el('analysis-target').addEventListener('change',reference);
  form.addEventListener('input',()=>{command=crypto.randomUUID().replaceAll('-','');});
  form.addEventListener('submit',async event=>{
    event.preventDefault(); if(busy || !options) return;
    const w = options.wallets.find(w=>w.id===el('analysis-wallet').value);
    if (!w) return;
    busy=true;el('analysis-create').disabled=true;el('analysis-status').textContent='Criando análise e preservando o contexto…';
    try {
      const d = await api('',{command_id:command,wallet:w.id,wallet_revision:w.revision,target_date:el('analysis-target').value,reference_session:el('analysis-reference').value,tickers:el('analysis-tickers').value.split(',').map(t=>t.trim().toUpperCase()).filter(Boolean),confirm:true});
      // Full navigation drops all preflight/consent of the previously viewed run.
      // auto=1: the free data check starts by itself (radar.js); paid steps still wait.
      location.assign('/radar?'+new URLSearchParams({run:d.run,wallet:w.id,auto:'1'})+'#analysis-workflow');
    } catch(e) { el('analysis-status').textContent='Análise não aberta: '+e.message; }
    finally {busy=false;el('analysis-create').disabled=false;}
  });
  el('radar-run').addEventListener('change',()=>context(el('radar-run').value));
  api().then(d=>{
    options=d;
    el('analysis-wallet').innerHTML=d.wallets.map(w=>`<option value="${esc(w.id)}">${esc(w.name)} · ${esc(w.nature_label)}</option>`).join('') || '<option value="">Nenhuma carteira</option>';
    const query=new URLSearchParams(location.search), wanted=query.get('wallet');
    const agents=d.wallets.find(w=>w.nature==='SIMULATION'&&w.strategy==='MULTIAGENT'); // the wallet the agents move
    if(d.wallets.some(w=>w.id===wanted))el('analysis-wallet').value=wanted;else if(agents)el('analysis-wallet').value=agents.id;
    el('analysis-target').min=d.sessions[1];el('analysis-target').max=d.sessions.at(-1);el('analysis-target').value=d.target_date;
    el('analysis-reference').min=d.sessions[0];reference();wallet();
    el('analysis-create').disabled=!d.wallets.length;
    el('analysis-status').textContent='Criar registra a análise e já verifica os dados, sem custo. Chamadas pagas sempre esperam sua autorização.';
    context(query.get('run') || d.selected);
    if(wanted || location.hash==='#new-analysis'){el('new-analysis').open=true;el('analysis-target').focus();}
  }).catch(e=>{el('analysis-status').textContent='Não foi possível abrir o cadastro: '+e.message;});
})();
// Cycle view (DP-17): the whole analysis cycle as connected steps, like a CI run graph.
// The analysis form above, radar.js (data, budget, analysts) and wallet-manager.js (manager,
// preview, approval, auction) send what they already fetched as 'hfl:cycle' events; this only
// reads it. Every control and consent stays in its own section: a click only brings it into view.
(() => {
  const names={created:'Análise criada',data:'Dados',budget:'Orçamento',agents:'Analistas',manager:'Gestor',preview:'Prévia',approval:'Aprovação',auction:'Execução'};
  const labels={done:'concluído',running:'em andamento',you:'aguardando você',blocked:'bloqueado',pending:'pendente',skipped:'não se aplica',waiting:'aguardando o mercado'};
  const day=v=>v?v.split('-').reverse().join('/'):'—';
  const at=v=>v?new Date(v).toLocaleString('pt-BR',{timeZone:'America/Sao_Paulo',day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'}):'';
  const span=(a,b)=>{const m=Math.round((new Date(b)-new Date(a))/60000);return !a||!b||!(m>=0)?'':m<1?'< 1 min':m<60?m+' min':Math.floor(m/60)+' h '+m%60+' min';};
  const when=(end,start)=>[at(end),span(start,end)].filter(Boolean).join(' · ');
  const short=t=>t.length>320?t.slice(0,319)+'…':t;
  const uniq=v=>short([...new Set(v.filter(Boolean))].join(' · '));
  const leg=o=>o.leg==='INTRADAY'?'pregão de '+day(o.session)+' (simulação intradiária)':'leilão de '+(o.leg==='OPEN'?'abertura':'fechamento')+' de '+day(o.session);
  const settled=n=>n.state==='done'||n.state==='skipped';
  function nodes({analysis:a,radar:r,manager:m}={}){
    const out=[], N=(id,state,detail='',x={})=>({id,name:names[id],state,detail,...x}), ok=id=>settled(out.find(n=>n.id===id));
    const e=m?.s, plan=Boolean(e?.result), sent=e?.order||e?.execution, moved=sent||e?.applied, expired=e?.status==='EXPIRED';
    // A manager proposal exists only after a complete quorum (manager_incomplete_quorum_* otherwise).
    const run=r?.run, job=r?.job||{}, total=run?.universe.length||0, quorum=total>0&&run.opinions===total||Boolean(e), live=job.status==='RUNNING', batch=job.command==='run';
    const inputsReady=total>0&&run.inputs===total&&run.integrity==='OK', reserved=Number(run?.usd_reserved)>0;
    out.push(a?N('created',a.changed&&!moved?'blocked':'done',a.wallet,{time:at(a.created),reason:a.changed&&!moved?'a carteira mudou depois desta análise':'',next:'Crie outra análise para movimentar a carteira atual.'})
      :run?N('created','done','Execução '+run.id,{time:at(run.registered_at)}):N('created','pending','Consultando…'));
    // Readiness rows explain a block in words (e.g. session not yet published by B3); the
    // sealed last_prepare only has the raw error, used when no readiness row explains it.
    const stuck=(r?.readiness||[]).filter(i=>['BLOCKED_DATA','UNRESOLVED_DIVERGENCE','INTEGRITY_ERROR'].includes(i.input_state)), failed=(r?.last_prepare?.items||[]).filter(i=>i.status==='BLOCKED');
    out.push(!r?N('data','pending','Consultando…')
      :quorum?N('data','done','Dados verificados',{time:at(run.prepared_at)})
      :job.command==='prepare'&&live?N('data','running','Preparando e validando os dados',{time:'desde '+at(job.started_at)})
      :r.readonly?N('data','blocked','Somente leitura',{reason:'esta execução não é a operacional do servidor',next:'Crie uma nova análise para continuar.'})
      :stuck.length||!inputsReady&&failed.length?N('data','blocked',`${(stuck.length?stuck:failed).length}/${total} ativos bloqueados`,{reason:stuck.length?uniq(stuck.map(i=>i.action||i.error)):uniq(failed.map(i=>i.error)),time:at(r.last_prepare?.generated_at),diag:true,next:'Veja o diagnóstico por ativo.'})
      :inputsReady||r.report?.ready?N('data','done','Dados prontos',{time:job.command==='prepare'?when(job.finished_at,job.started_at):at(run.prepared_at)})
      :r.report?N('data','blocked','Verificação bloqueada',{reason:uniq(r.report.items.filter(i=>!i.ready).map(i=>i.ticker+': '+i.error)),diag:true,next:'Veja o diagnóstico por ativo.'})
      :N('data','you','Verificar dados (gratuito)',{next:'Verifique os dados do dia; não há custo.'}));
    const auth=run?.budget?.authorization;
    out.push(!r?N('budget','pending','Consultando…')
      :!run.budget?N('budget','skipped','Sem custo (sintético)')
      :!quorum&&!ok('data')?N('budget','pending','Depois dos dados') // never "done" ahead of blocked data
      :reserved?N('budget','done','Reserva do lote registrada')
      :quorum||auth.state==='VALID'||!auth.required?N('budget','done',auth.state==='VALID'?'Teto autorizado':'Sem autorização pendente')
      :r.review?N('budget','you','Digite o teto e autorize',{next:'Digite o teto agregado e marque a autorização de orçamento.'})
      :N('budget','pending','Revisão depois da verificação'));
    const count=`${run?.opinions??0}/${total} pareceres`;
    out.push(!r?N('agents','pending','Consultando…')
      :batch&&live?N('agents','running',count,{time:'desde '+at(job.started_at)})
      :quorum?N('agents','done',count,{time:batch?when(job.finished_at,job.started_at):''})
      :batch&&(job.outcome?job.outcome.state!=='COMPLETED':job.status!=='COMPLETED')?N('agents','blocked',count,{reason:short(job.outcome?.summary||'execução interrompida ('+job.status+')'),diag:true,next:'Veja o diagnóstico e a recuperação por ativo.'})
      :!ok('data')||!ok('budget')?N('agents','pending',count)
      :r.paid?N('agents','you','Autorize a chamada paga',{next:'Marque a autorização paga dos analistas e confirme o custo.'})
      :N('agents','pending',count));
    out.push(a===null||m===null?N('manager','skipped','Sem carteira vinculada')
      :!m?N('manager','pending','Consultando…')
      :plan?N('manager','done','Plano gerado',{time:at(e.result.completed_at)})
      :expired?N('manager','blocked','Proposta expirada',{reason:'os leilões do pregão-alvo já passaram',next:'Crie outra análise para o próximo pregão.'})
      :!quorum?N('manager','pending','Depois dos analistas')
      :['RUNNING','CLAIMED_RECOVERY_ONLY'].includes(e?.status)?N('manager','running','Gerando o plano')
      :e?.status==='RECOVERY_OR_REVIEW_REQUIRED'?N('manager','blocked','Revisão necessária',{reason:short(m.failure||'consulte as falhas preservadas'),next:'Recupere a resposta gravada, sem nova chamada, ou prepare outra proposta.'})
      :m.inference?N('manager','you','Autorize a chamada paga do gestor',{next:'Marque a autorização paga do gestor e gere o plano.'})
      :N('manager','you',m.cost?'Prepare a proposta (gratuito)':'Informe a taxa simulada',{next:m.cost?'Prepare a proposta do gestor; não há custo.':'Informe a taxa simulada por operação, inclusive se for zero.'}));
    const skip=!plan?'':!e.result.trades.length?'O gestor propôs manter':m.consult&&!moved?'Consulta apenas':'';
    const gone={reason:'os leilões do pregão-alvo já passaram',next:'Crie outra análise para o próximo pregão.'};
    const after=(id,wait)=>!plan?N(id,'pending',wait):skip?N(id,'skipped',skip):null;
    out.push(after('preview','Depois do plano')||(moved||m.preview?N('preview','done','Cotações conferidas')
      :expired?N('preview','blocked','Proposta expirada',gone)
      :N('preview','you','Abra a prévia (gratuita)',{next:'Abra a prévia com a cotação atrasada; nada é registrado.'})));
    out.push(after('approval','Depois da prévia')||(sent?N('approval','done','Ordem aprovada',{time:at(e.order?.approved_at)})
      :e.applied?N('approval','done','Aprovada',{time:at(e.applied.recorded_at)})
      :expired?N('approval','blocked','Proposta expirada',gone)
      :m.preview?N('approval','you','Revise e aprove a ordem',{next:'Revise quantidades e custos e marque a aprovação financeira.'})
      :N('approval','pending','Depois da prévia')));
    const x=e?.execution;
    out.push(after('auction','Depois da aprovação')||(x?.status==='EXECUTED'?N('auction','done','Executada no '+leg(x),{time:at(x.executed_at)})
      :x?N('auction','blocked',x.status==='ORDER_REJECTED'?'Ordem recusada':'Nenhuma ordem executável',{reason:short(x.reason||'consulte o recibo do gestor'),next:'Nada foi registrado; crie outra análise.'})
      :e.order?N('auction','waiting',e.order.leg==='INTRADAY'?'Aguardando preço intradiário de '+day(e.order.session):'Aguardando o '+leg(e.order),{next:e.order.leg==='INTRADAY'?'O servidor busca a primeira barra de 1 minuto posterior à aprovação. Yahoo tem atraso ~15 min; nenhuma cotação anterior é usada.':'Nada a fazer: a ordem executa ao preço oficial B3 quando ele entrar na base.'})
      :e.applied?N('auction','done','Registrada ao preço de referência')
      :expired?N('auction','blocked','Proposta expirada',gone)
      :N('auction','pending','Depois da aprovação')));
    return out;
  }
  function summary(list){ // the first unsettled step is the cycle's state and next action
    const n=list.find(n=>!settled(n)), cap=t=>t&&t[0].toUpperCase()+t.slice(1).replace(/\.$/,'');
    if(!n)return {state:'Ciclo concluído',text:'Crie a próxima análise quando quiser.'};
    return {node:n,state:{blocked:'Bloqueado em '+n.name,you:'Aguardando você em '+n.name,running:n.name+' em andamento',waiting:n.detail,pending:'Pendente: '+n.name}[n.state],
      text:n.state==='blocked'?[cap(n.reason),n.next].filter(Boolean).join('. '):n.state==='running'?n.detail+'. A tela atualiza sozinha.':n.next||n.detail};
  }
  window.HFLCycle={nodes,summary};
  const box=document.getElementById('agent-cycle');
  if(!box)return;
  const snap={}, hashes={setup:'#new-analysis',workflow:'#analysis-workflow',results:'#analysis-results'};
  // Where a click lands: the first visible control (only when the step needs you), else the section.
  const go={created:['#analysis-target','#new-analysis'],data:['#guided-check','#analysis-workflow'],budget:['#aggregate-budget','#analysis-workflow'],agents:['#paid','#analysis-workflow'],manager:['#manager-paid','#manager-cost','#wallet-manager'],preview:['#manager-preview','#manager-result'],approval:['#manager-financial','#manager-receipt'],auction:['#manager-receipt']};
  const set=(id,v)=>{const e=document.getElementById(id);if(e.textContent!==v)e.textContent=v;}; // unchanged text is not re-announced
  function render(){
    const list=nodes(snap), s=summary(list), a=snap.analysis, run=snap.radar?.run;
    for(const n of list){
      const li=box.querySelector(`[data-node="${n.id}"]`), b=li.querySelector('button'), diag=li.querySelector('.cycle-diag');
      li.dataset.state=n.state;li.toggleAttribute('data-active',n===s.node);
      if(n===s.node)b.setAttribute('aria-current','step');else b.removeAttribute('aria-current');
      li.querySelector('.cycle-state').textContent=labels[n.state];
      li.querySelector('.cycle-detail').textContent=n.reason?n.detail+': '+n.reason:n.detail;
      li.querySelector('.cycle-time').textContent=n.time||'';
      if(diag)diag.hidden=!n.diag;
    }
    set('cycle-wallet',a?.wallet||snap.manager?.s?.context.wallet.name||'—');set('cycle-target',a?day(a.target):'—');
    set('cycle-reference',a?day(a.reference):run?day(run.session):'—');set('cycle-start',at(a?.created||run?.registered_at)||'—');
    set('cycle-next',s.state+'. '+s.text);box.dataset.state=s.node?.state||'done';
  }
  function reveal(stage,targets){
    const t=targets.map(q=>document.querySelector(q)).find(e=>e?.getClientRects().length)||document.querySelector(`[data-agent-screen="${stage}"]`);
    t.scrollIntoView({block:'center',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});t.focus({preventScroll:true});
  }
  box.addEventListener('click',event=>{
    const b=event.target.closest('button,.cycle-diag');if(!b)return;
    event.preventDefault();
    const li=b.closest('li'), n=nodes(snap).find(n=>n.id===li.dataset.node), stage=li.querySelector('button').dataset.agentStage, diag=n.diag&&n.state==='blocked';
    if(diag)document.getElementById('diagnostic-details').open=true;
    const targets=diag?['#diagnostic-details>summary']:n.state==='you'||n.state==='blocked'?go[n.id]:go[n.id].slice(-1);
    if(document.body.dataset.agentStage===stage)return reveal(stage,targets);
    window.addEventListener('hashchange',()=>reveal(stage,targets),{once:true});location.hash=hashes[stage];
  });
  window.addEventListener('hfl:cycle',event=>{Object.assign(snap,event.detail);render();});
  render();
})();
