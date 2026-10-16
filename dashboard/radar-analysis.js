'use strict';
(() => {
  const el = id => document.getElementById(id), form = el('new-analysis-form');
  if (!form) return;
  const esc = v => String(v ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const day = v => v.split('-').reverse().join('/');
  const labels = {FUTURE_ANALYSIS:'Análise para sessão futura',SAME_DAY_ANALYSIS:'Análise para hoje',HISTORICAL_REANALYSIS:'Reanálise histórica — criada agora'};
  const errors = {analysis_wallet_changed_reload:'A carteira mudou. Atualize a página e revise a seleção.',analysis_reference_must_be_closed_before_target:'Escolha uma sessão de dados já encerrada e anterior ao dia-alvo.',analysis_target_not_a_planned_session:'O dia-alvo precisa ser uma sessão do calendário disponível.',analysis_target_before_wallet_start:'O dia-alvo é anterior ao início dessa carteira.',radar_busy_or_stale_lock:'Há uma preparação/análise em andamento ou um bloqueio de recuperação. Consulte o Radar antes de criar outra.',analysis_wallet_not_found:'Carteira indisponível. Atualize a página.'};
  let options, command = crypto.randomUUID().replaceAll('-',''), busy = false, revision = 0;
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
    el('analysis-tickers').value = (w?.positions.length ? w.positions.map(p=>p.ticker) : options.examples).join(', ');
    el('analysis-wallet-state').textContent = w ? `${w.nature_label} · caixa R$ ${Number(w.cash).toLocaleString('pt-BR',{minimumFractionDigits:2})} · ${w.positions.length} posição(ões). O estado atual será preservado com esta análise.` : 'Crie uma carteira na página inicial para começar.';
    history();
  }
  function reference() {
    const target = el('analysis-target').value;
    const days = options.sessions.filter(d=>d<target && d<=options.reference_session);
    el('analysis-reference').value = days.at(-1) || '';
    el('analysis-reference').max = days.at(-1) || options.reference_session;
    el('analysis-date-note').textContent = target < options.today ? 'Reanálise histórica com dados obtidos agora e o estado atual da carteira. Não será apresentada como previsão feita no passado.' : 'A data dos dados é anterior ao alvo. Preparar confirma a disponibilidade; o calendário não garante que os preços já foram publicados.';
  }
  async function context(run) {
    const version = ++revision, box = el('analysis-context');
    box.hidden = true;
    el('analysis-return').hidden = true;
    el('radar-to-global').hidden = run.startsWith('radar-ui-');
    try {
      const d = await api('?'+new URLSearchParams({run}));
      if (version !== revision || !d.context) return;
      const c = d.context;
      el('radar-to-global').hidden = true;
      el('analysis-return').href = '/?'+new URLSearchParams({wallet:c.wallet.id});
      el('analysis-return').hidden = false;
      box.textContent = `${c.wallet.name} · ${labels[c.classification]} ${day(c.target_date)} · dados até ${day(c.reference_session)}. Carteira preservada em ${new Date(c.created_at).toLocaleString('pt-BR',{timeZone:'America/Sao_Paulo'})}. Após o quórum, prepare o gestor em Resultados para obter uma proposta com quantidades.${d.wallet_changed?' A carteira mudou desde este registro; abra outra análise para movimentar o estado atual. O contexto original continua preservado.':''}`;
      box.hidden = false;
    } catch (e) { if(version===revision){box.textContent='Contexto da análise indisponível: '+e.message;box.hidden=false;} }
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
      location.assign('/radar?'+new URLSearchParams({run:d.run,wallet:w.id})+'#analysis-workflow');
    } catch(e) { el('analysis-status').textContent='Análise não aberta: '+e.message; }
    finally {busy=false;el('analysis-create').disabled=false;}
  });
  el('radar-run').addEventListener('change',()=>context(el('radar-run').value));
  api().then(d=>{
    options=d;
    el('analysis-wallet').innerHTML=d.wallets.map(w=>`<option value="${esc(w.id)}">${esc(w.name)} · ${esc(w.nature_label)}</option>`).join('') || '<option value="">Nenhuma carteira</option>';
    const query=new URLSearchParams(location.search), wanted=query.get('wallet');
    if(d.wallets.some(w=>w.id===wanted))el('analysis-wallet').value=wanted;
    el('analysis-target').min=d.sessions[1];el('analysis-target').max=d.sessions.at(-1);el('analysis-target').value=d.target_date;
    el('analysis-reference').min=d.sessions[0];reference();wallet();
    el('analysis-create').disabled=!d.wallets.length;
    el('analysis-status').textContent='Criar só registra e seleciona a análise. Preparação e chamadas pagas continuam em etapas próprias abaixo.';
    context(query.get('run') || d.selected);
    if(wanted || location.hash==='#new-analysis'){el('new-analysis').open=true;el('analysis-target').focus();}
  }).catch(e=>{el('analysis-status').textContent='Não foi possível abrir o cadastro: '+e.message;});
})();
