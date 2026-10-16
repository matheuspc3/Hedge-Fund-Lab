'use strict';
(() => {
  const el=id=>document.getElementById(id), panel=el('wallet-manager');
  if(!panel)return;
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const money=v=>Number(v).toLocaleString('pt-BR',{style:'currency',currency:'BRL'});
  const day=v=>v.split('-').reverse().join('/');
  const pct=v=>(Number(v)*100).toLocaleString('pt-BR',{maximumFractionDigits:2})+'%';
  const states={PREPARED:'Preparada',RUNNING:'Gerando',CLAIMED_RECOVERY_ONLY:'Autorizada · consultar/recuperar',RECOVERY_OR_REVIEW_REQUIRED:'Revisão necessária',VALID_PROPOSAL:'Proposta gerada',APPLIED:'Movimentações registradas'};
  const errors={manager_wallet_changed_new_analysis_required:'A carteira mudou desde o quórum. Abra uma nova análise para usar as posições atuais.',manager_complete_unique_universe_required:'O gestor devolveu uma cesta incompleta ou repetida. A resposta foi preservada para revisão.',manager_universe_must_cover_all_positions:'Inclua todas as posições da carteira nos ativos do quórum.',manager_budget_exceeded:'O teto informado ou o orçamento acumulado do Gestor Global não cobre esta chamada.',manager_key_or_network_isolation_missing:'Chave ou isolamento do servidor indisponível. Reinicie o servidor padrão.',manager_contract_changed:'O contrato mudou. Esta proposta continua no histórico; prepare outra para operar.',manager_insufficient_cash:'A proposta ultrapassou o caixa disponível, incluindo custos. Foi preservada para revisão.',manager_operation_incompatible_with_opinion:'A proposta contrariou um parecer ou veto. Não foi liberada para registro.',manager_insufficient_units:'A proposta tentou vender mais ações do que a carteira possui.',manager_financial_consent_required:'Revise a prévia e confirme a aprovação das movimentações.',manager_context_expired:'O contexto do gestor expirou. Prepare outra proposta.',manager_no_envelope_to_replay_or_busy:'Não há resposta recuperável ou a chamada ainda está em andamento.'};
  let data, selected=new URLSearchParams(location.search).get('proposal')||'', report, preview, version=0, busy=false, poll, command=crypto.randomUUID().replaceAll('-','');
  const run=()=>el('radar-run').value||new URLSearchParams(location.search).get('run');
  const current=()=>data?.history.find(s=>s.context.proposal===selected);
  function message(e){const code=e.message||String(e);return code.startsWith('manager_incomplete_quorum_')?'O gestor aguarda pareceres completos: '+code.slice('manager_incomplete_quorum_'.length).split('_').join(', ').toUpperCase()+'. Consulte os resultados por ativo e a recuperação do quórum.':errors[code]||code;}
  async function api(commandName, payload, runId=run()){
    const r=await fetch('/api/platform/wallet-manager'+(commandName?'/'+commandName:'?'+new URLSearchParams({run:runId})),payload?{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':data.csrf_token},body:JSON.stringify(payload)}:{cache:'no-store'});
    const d=await r.json();if(!r.ok)throw Error(d.error||'Não foi possível consultar a proposta.');return d;
  }
  function dismiss(){report=null;preview=null;el('manager-paid').checked=false;el('manager-financial').checked=false;el('manager-run').disabled=true;el('manager-apply').disabled=true;el('manager-inference').hidden=true;el('manager-preview-box').hidden=true;}
  function draw(){
    const s=current(), c=s?.context, r=s?.result;
    el('manager-history').innerHTML=data.history.length?data.history.map(s=>`<option value="${esc(s.context.proposal)}">${esc(new Date(s.context.created_at).toLocaleString('pt-BR'))} · ${esc(states[s.status])} · taxa original da proposta ${esc(s.context.cost_rate_pct)}%</option>`).join(''):'<option value="">Nenhuma proposta</option>';
    el('manager-history').value=selected;
    el('manager-result').hidden=!r;
    el('manager-attempts').hidden=!s?.failures?.length;
    el('manager-failures').innerHTML=(s?.failures||[]).map(f=>'<li>'+esc(new Date(f.recorded_at).toLocaleString('pt-BR'))+' · '+esc(message({message:f.code}))+'</li>').join('');
    el('manager-replay').hidden=!s||!['CLAIMED_RECOVERY_ONLY','RECOVERY_OR_REVIEW_REQUIRED'].includes(s.status)||!s.compatible;
    el('manager-status').textContent=s?states[s.status]:'Informe os custos para preparar o contexto do gestor. Nenhuma chamada é feita nesta consulta.';
    if(s?.failure&&!r)el('manager-status').textContent+=' · '+message({message:s.failure.code})+' · nenhum registro financeiro foi feito.';
    if(!r)return;
    el('manager-summary').textContent=r.response.summary;
    el('manager-price-note').textContent=`Referência: fechamento RAW B3 de ${day(c.reference_session)}. Não é cotação ao vivo. Contexto congelado em ${new Date(c.created_at).toLocaleString('pt-BR')}; alvo da análise ${day(c.target_date)}. Taxa utilizada na proposta original: ${c.cost_rate_pct}% por operação.`;
    const sides={BUY:'Comprar',SELL:'Vender',HOLD:'Manter'};
    el('manager-plan').innerHTML='<div class="ds-table-wrap" tabindex="0" role="region" aria-label="Plano de alocação, tabela rolável"><table class="ds-table"><thead><tr><th>Ativo</th><th>Atual</th><th>Movimentação</th><th>Depois</th><th>Preço de referência</th><th>Valor da operação</th><th>Custos</th><th>Peso antes → depois</th><th>Motivo</th></tr></thead><tbody>'+r.rows.map(a=>`<tr><td><strong>${esc(a.ticker)}</strong></td><td>${esc(a.quantity_before)}</td><td>${sides[a.side]}${a.side==='HOLD'?'':' '+esc(a.quantity)+' ações'}${a.side==='SELL'?' · '+(Number(a.quantity_after)===0?'saída total':'redução parcial'):''}</td><td>${esc(a.quantity_after)}</td><td>${money(a.price)}</td><td>${money(a.gross)}</td><td>${money(a.costs)}</td><td>${pct(a.weight_before)} → ${pct(a.weight_after)}</td><td>${esc(a.reasoning)}</td></tr>`).join('')+'</tbody></table></div>';
    el('manager-cash').textContent=`Projeção original de caixa: ${money(r.cash_before)} → ${money(r.cash_after)} · custos da proposta original: ${money(r.total_costs)}. Vendas financiam compras somente neste livro econômico simulado, sem liquidação de corretora.`;
    el('manager-risks').innerHTML=r.response.risks.map(s=>'<li>'+esc(s)+'</li>').join('');
    const consultOnly=c.wallet.nature!=='SIMULATION'||c.wallet.strategy==='BUY_HOLD'||!s.compatible;
    el('manager-approval').hidden=Boolean(s.applied)||consultOnly||!r.trades.length;
    el('manager-receipt').textContent=s.applied?'Cesta registrada em '+new Date(s.applied.recorded_at).toLocaleString('pt-BR')+'. Histórico preservado; a aprovação não será repetida.':consultOnly?'Consulta apenas: '+(!s.compatible?'contrato histórico preservado.':c.wallet.nature!=='SIMULATION'?'carteira de operações reais externas não recebe operações simuladas.':'a estratégia Buy & Hold não aceita rebalanceamento automático.') :!r.trades.length?'O gestor propôs manter a carteira; não há operações para registrar.':'';
    if(s.applied&&data.ledger){
      const originalIds=new Set(data.ledger.audit.filter(e=>e.source?.proposal===c.proposal).map(e=>e.id));
      const corrected=data.ledger.audit.some(e=>e.kind==='CORRECTION'&&originalIds.has(e.target));
      if(corrected){
        const booked=data.ledger.trades.filter(t=>t.source?.proposal===c.proposal);
        const rates=[...new Set(booked.map(t=>t.source.cost_rate_pct))];
        el('manager-receipt').textContent+=' Há correções posteriores no histórico de Operações.'+(booked.length===r.trades.length&&rates.length===1?' Taxa registrada: '+rates[0]+'% · custos registrados desta cesta: '+money(booked.reduce((sum,t)=>sum+Number(t.costs),0))+'.':'')+' A justificativa e a tabela abaixo preservam a proposta original, anterior às correções.';
      }
    }
  }
  async function load(reset=false){
    const id=run();if(!id)return;
    const v=version;
    const d=await api('',undefined,id);if(v!==version)return;
    if(d.context&&d.history.some(s=>s.applied)){
      try{
        const response=await fetch('/api/portfolio/manual?'+new URLSearchParams({wallet:d.context.wallet.id}),{cache:'no-store'});
        if(response.ok)d.ledger=(await response.json()).selected;
      }catch{} // Historical proposal stays readable when the personal ledger is unavailable.
      if(v!==version)return;
    }
    data=d;panel.hidden=!d.context;if(!d.context)return;
    if(reset||!d.history.some(s=>s.context.proposal===selected))selected=d.history.at(-1)?.context.proposal||'';
    el('manager-context').textContent=`${d.context.wallet.name} · alvo ${day(d.context.target_date)} · dados até ${day(d.context.reference_session)} · caixa preservado ${money(d.context.wallet.cash)}.`+(d.context.wallet.strategy==='BUY_HOLD'?' Buy & Hold: o plano será consultivo; para rebalancear, abra o quórum da Multiagentes.':d.context.wallet.nature!=='SIMULATION'?' Carteira real externa: consulta apenas, sem registrar negócios simulados.':'');
    draw();
    clearTimeout(poll);
    if(['RUNNING','CLAIMED_RECOVERY_ONLY'].includes(current()?.status))poll=setTimeout(()=>load().catch(failure),2500);
  }
  function failure(e){el('manager-error').textContent=message(e);el('manager-error').hidden=false;}
  async function action(fn){
    if(busy)return;busy=true;panel.setAttribute('aria-busy','true');el('manager-error').hidden=true;
    const v=version;
    try{await fn(v);}catch(e){if(v===version)failure(e);}finally{busy=false;panel.removeAttribute('aria-busy');}
  }
  el('manager-prepare-form').addEventListener('submit',event=>{
    event.preventDefault();if(!data)return;
    const request={run:run(),proposal:command,cost_rate_pct:el('manager-cost').value}, cap=el('manager-budget').value;
    action(async v=>{
      dismiss();el('manager-status').textContent='Conferindo quórum, carteira e preços…';
      const d=await api('prepare',request);if(v!==version)return;selected=d.context.proposal;command=crypto.randomUUID().replaceAll('-','');
      const p=await api('preflight',{run:request.run,proposal:selected,max_usd:cap});if(v!==version)return;
      await load();if(v!==version)return;report=p;
      el('manager-estimate').textContent=`Uma chamada do gestor · estimativa US$ ${p.estimate.usd_estimated} · reserva máxima US$ ${p.usd_reserved} · reservas acumuladas do Gestor Global US$ ${p.budget_used}. Não altera o orçamento do Radar nem autoriza movimentações.`;
      el('manager-inference').hidden=false;el('manager-paid').disabled=!p.ready;
      if(!p.ready)throw Error(p.errors.join(', '));
    });
  });
  el('manager-prepare-form').addEventListener('input',()=>{version++;command=crypto.randomUUID().replaceAll('-','');dismiss();});
  el('manager-paid').addEventListener('change',()=>{el('manager-run').disabled=!report?.ready||!el('manager-paid').checked||busy;});
  el('manager-run').addEventListener('click',()=>{
    if(!report||!el('manager-paid').checked)return;
    const p={run:run(),proposal:selected,max_usd:report.max_usd,confirmation_token:report.confirmation_token,authorize_paid:true};
    action(async v=>{dismiss();await api('run',p);if(v!==version)return;await load();});
  });
  el('manager-replay').addEventListener('click',()=>action(async v=>{await api('replay',{run:run(),proposal:selected});if(v!==version)return;await load();}));
  el('manager-preview').addEventListener('click',()=>action(async v=>{
    dismiss();const p={run:run(),proposal:selected,economic_date:data.today};
    const d=await api('preview',p);if(v!==version)return;
    preview={...p,preview_token:d.preview_token,confirm:true};
    el('manager-effect').textContent=`Registrar hoje (${day(data.today)}) aos preços RAW de referência exibidos: caixa ${money(d.before.cash)} → ${money(d.after.cash)}; custos acumulados ${money(d.before.costs)} → ${money(d.after.costs)}. Toda a cesta será confirmada em uma única transação.`;
    el('manager-preview-box').hidden=false;el('manager-financial').focus();
  }));
  el('manager-financial').addEventListener('change',()=>{el('manager-apply').disabled=!preview||!el('manager-financial').checked||busy;});
  el('manager-apply').addEventListener('click',()=>{
    if(!preview||!el('manager-financial').checked)return;
    const p=preview;
    action(async v=>{await api('apply',p);if(v!==version)return;dismiss();await load();el('manager-receipt').focus();});
  });
  el('manager-history').addEventListener('change',()=>{version++;selected=el('manager-history').value;dismiss();draw();});
  el('manager-refresh').addEventListener('click',()=>action(async()=>{dismiss();await load();}));
  el('radar-run').addEventListener('change',()=>{version++;selected='';clearTimeout(poll);dismiss();panel.hidden=true;load(true).catch(failure);});
  window.addEventListener('hfl:analysis-stage',event=>{if(event.detail!=='results'){version++;dismiss();}else load().catch(failure);});
  load().catch(failure);
})();
