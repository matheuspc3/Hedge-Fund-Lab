'use strict';
const $ = id => document.getElementById(id);
const esc = value => String(value ?? '—').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const money = value => Number(value || 0).toLocaleString('pt-BR', {style:'currency',currency:'BRL'});
const pct = value => value == null ? 'Indisponível' : (Number(value)*100).toFixed(2).replace('.', ',')+'%';
const colors = {PETR4:'#a1edcb',VALE3:'#84b5e8',ITUB4:'#c6a1e5',WEGE3:'#e7bd7a',BBAS3:'#ed9eab',CAIXA:'#536474'};
const charts = new Map();
const validationMessages = {weights_must_sum_to_one:'Os pesos dos ativos e do caixa devem somar 100%.',negative_or_excessive_target_weight:'Há um peso negativo ou acima do limite de concentração.',insufficient_settled_cash:'O caixa liquidado disponível não cobre esta compra.',individual_veto:'O parecer individual veta a operação neste ativo.'};
let state, requestVersion = 0;
async function api(path) {
  const response = await fetch('/api/portfolio/'+path, {cache:'no-store'});
  const result = await response.json();
  if (!response.ok) throw new Error('Consulta bloqueada: verifique a integridade dos registros ou o cenário solicitado.');
  return result;
}
function error(exc) { $('error').textContent = exc.message; $('error').hidden = false; }
function allocation(view) {
  const rows = Object.entries(view.positions).filter(([,p])=>Number(p.quantity)>0).map(([t,p])=>({ticker:t,weight:Number(p.weight),amount:Number(p.market_value)}));
  rows.push({ticker:'CAIXA',weight:Number(view.cash_weight),amount:Number(view.cash.settled)+Number(view.cash.receivable)});
  return rows;
}
function legend(view, amounts=true) {
  return allocation(view).map(r=>`<div class="legend-row"><span class="swatch" style="background:${colors[r.ticker]||'#9caab4'}"></span><div>${esc(r.ticker==='CAIXA'?'Caixa + recebíveis':r.ticker)} <strong>${pct(r.weight)}</strong>${amounts?`<small>${money(r.amount)}</small>`:''}</div></div>`).join('');
}
function chart(id, rows) {
  charts.get(id)?.destroy();
  charts.set(id,new Chart($(id),{type:'doughnut',data:{labels:rows.map(r=>r.ticker),datasets:[{data:rows.map(r=>r.weight),backgroundColor:rows.map(r=>colors[r.ticker]||'#9caab4'),borderColor:'#121a20',borderWidth:3,hoverOffset:3}]},options:{responsive:true,maintainAspectRatio:false,cutout:'78%',animation:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>`${c.label}: ${pct(c.raw)}`}}}}}));
}
function renderWallet() {
  const p=state.portfolio;
  $('session').textContent = `Sessão sintética ${p.session} · ${p.portfolio_id}`;
  $('equity').textContent=money(p.equity); $('available').textContent=money(p.cash.available); $('reserved').textContent=money(p.cash.reserved); $('receivable').textContent=money(p.cash.receivable);
  $('wallet-legend').innerHTML=legend(p); chart('wallet-chart',allocation(p));
  $('positions').innerHTML=state.opportunities.map(o=>{const t=o.ticker, pos=p.positions[t]; return pos?`<tr><td><strong>${esc(t)}</strong></td><td>${esc(pos.quantity)} / ${esc(pos.available)}<small>Reservadas: ${esc(pos.reserved)} · em liquidação: ${esc(pos.unsettled)}</small></td><td>${money(pos.average_cost)}</td><td>${money(pos.raw_mark)}</td><td>${pct(pos.weight)}</td><td>${money(pos.unrealized_pnl)}</td></tr>`:`<tr><td><strong>${esc(t)}</strong></td><td>0 / 0</td><td>—</td><td>—</td><td>0,00%</td><td>—</td></tr>`;}).join('');
  const r=state.risk;
  $('risk').innerHTML=[['Exposição total',pct(p.exposure)],['Maior concentração',pct(Math.max(0,...Object.values(p.positions).map(pos=>Number(pos.weight))))],['Volatilidade global · 60 retornos',pct(r.volatility)],['Drawdown consolidado',pct(p.drawdown)],['Setores','Não avaliados · sem metadados'],['Status das métricas',r.status==='OK'?'Histórico suficiente':'Bloqueado · histórico/limite']].map(([k,v])=>`<div><span>${esc(k)}</span><strong>${esc(v)}</strong></div>`).join('');
  $('pnl').innerHTML=[['Resultado realizado · pré-IR',money(p.realized_pnl)],['Resultado não realizado',money(p.unrealized_pnl)],['Custos acumulados',money(p.costs)]].map(([k,v])=>`<div><span>${esc(k)}</span><strong>${esc(v)}</strong></div>`).join('');
  $('opportunities').innerHTML=state.opportunities.map(o=>`<article class="opportunity"><strong>${esc(o.ticker)}</strong><p><span class="pill">${esc(o.recommendation)}</span></p><small>${esc(o.session)} · SINTÉTICO</small><small>Risco consultivo: ${esc(o.risk_verdict)}</small><small>Fonte: fixture offline · ${o.votes_count}/5 votos</small><details><summary>Referências seladas</summary><pre>${esc(JSON.stringify(o,null,2))}</pre></details></article>`).join('');
  $('case-buttons').innerHTML=state.cases.map(c=>`<button class="secondary" data-case="${esc(c.id)}" type="button" title="${esc(c.label)}">Exemplo ${esc(c.id)}${c.valid?'':' · bloqueado'}</button>`).join('');
  $('integrity').textContent=`CADEIA ÍNTEGRA · ${state.integrity.events} EVENTOS`;
  $('audit-summary').textContent=`${state.identity} · ${state.integrity.events} eventos verificados. Consultas sem inferência e sem gravação. Limites e custos pertencem somente à política de demonstração.`;
  $('audit').textContent=JSON.stringify({policy:state.policy,integrity:state.integrity,events:state.events,executions:p.executions,pending:p.pending,receivables:p.receivables},null,2);
}
function targetRows(p) {
  const rows=Object.entries(p.target_weights).filter(([,w])=>Number(w)>0).map(([ticker,weight])=>({ticker,weight:Number(weight)}));
  rows.push({ticker:'CAIXA',weight:Number(p.target_cash_weight)}); return rows;
}
function targetLegend(rows) { return rows.map(r=>`<div class="legend-row"><span class="swatch" style="background:${colors[r.ticker]||'#9caab4'}"></span><span>${esc(r.ticker)} <strong>${pct(r.weight)}</strong></span></div>`).join(''); }
function renderPlan(item) {
  ['before-chart','after-chart'].forEach(id=>{charts.get(id)?.destroy();charts.delete(id);});
  const p=item.proposal,v=item.validation,before=item.before;
  const target=targetRows(p);
  const operations=p.operations.map(op=>{const price=Number(op.limit_price),q=Number(op.quantity),fees=Number(op.cost_ceiling),waiting=v.deferred_operations.some(d=>d.operation_id===op.operation_id); return `<tr><td><strong>${esc(op.ticker)}</strong></td><td>${pct(before.positions[op.ticker]?.weight||0)} → ${pct(p.target_weights[op.ticker]||0)}</td><td>${op.side==='BUY'?'COMPRAR':'VENDER'}${waiting?'<small class="warning">AGUARDAR LIQUIDAÇÃO</small>':''}</td><td>${esc(op.quantity)}</td><td>${money(op.side==='BUY'?q*price+fees:q*price-fees)}<small>${op.side==='BUY'?'Caixa liquidado necessário':'A receber · indisponível no trade'}</small></td><td>${money(fees)}</td><td>${op.dependencies.map(esc).join(', ')||'Nenhuma'}<small>${esc(op.reasoning)}</small></td></tr>`;});
  $('plan').innerHTML=`<div class="plan-head"><h3>${esc(item.label)}</h3><p class="muted small">Sessão ${esc(p.decision_session)} · Proposta sintética · ${v.valid?'Validação aprovada':'Validação bloqueada'} · ${p.operations.length} operações propostas</p><p class="muted small">Pareceres e marcas vinculados à sessão ${esc(p.decision_session)}. ${p.decision_session!==state.portfolio.session?"Exemplo histórico sintético, distinto da sessão atual do painel de oportunidades.":"Mesma sessão do painel de oportunidades."}</p></div>${v.valid?'':`<div class="blocked" role="status"><strong>Proposta rejeitada. Nenhuma execução permitida.</strong><p>${v.errors.map(e=>esc(validationMessages[e.code]||e.code)).join('<br>')}</p></div>`}<div class="allocation-compare"><article class="allocation-panel"><h4>Carteira atual · ${money(before.equity)}</h4><div class="wallet-grid"><div class="chart"><canvas id="before-chart" role="img" aria-label="Alocação atual, valores na legenda"></canvas></div><div class="legend">${legend(before,false)}</div></div></article><article class="allocation-panel"><h4>Intenção de alocação${v.valid?'':' · inválida'}</h4><div class="wallet-grid"><div class="chart"><canvas id="after-chart" role="img" aria-label="Pesos-alvo declarados; projeção financeira exibida separadamente"></canvas></div><div class="legend">${targetLegend(target)}</div></div></article></div>${operations.length?`<div class="table-scroll" tabindex="0" role="region" aria-label="Operações propostas, rolável horizontalmente"><table class="plan-table"><thead><tr><th>Ativo</th><th>Peso atual → alvo</th><th>Movimento</th><th>Unidades</th><th>Capital</th><th>Custo máximo</th><th>Dependência / justificativa</th></tr></thead><tbody>${operations.join('')}</tbody></table></div>`:(v.valid?'<p class="no-op">MANTER · Preservar posições e caixa, sem nova operação.</p>':'<p class="no-op">Nenhuma operação autorizada para esta proposta.</p>')}${v.deferred_operations.length?'<p class="dependency">A venda gera recebível. A compra dependente fica adiada e exige recebimento confirmado, preços rechecados, nova proposta e nova aprovação. A projeção condicional não é caixa disponível.</p>':''}${v.projected?`<div class="projection-facts"><div>Patrimônio projetado · etapa imediata<strong>${money(v.projected.equity)}</strong></div><div>Caixa disponível após operações imediatas<strong>${money(v.projected.cash.available)}</strong></div><div>A receber após operações imediatas<strong>${money(v.projected.cash.receivable)}</strong></div><div>Custos previstos · plano completo<strong>${money(v.estimated_costs)}</strong></div></div><p class="muted small">Pesos-alvo são intenções. O validador recalcula quantidades inteiras, patrimônio, exposição e concentração após custos. ${Object.entries(v.projected.positions).filter(([,pos])=>Number(pos.quantity)>0).map(([t,pos])=>`${esc(t)}: ${pct(pos.weight)}`).join(' · ')} · Caixa: ${pct(v.projected.cash_weight)}.</p>`:''}<details><summary>Contrato da proposta e validação independente</summary><pre>${esc(JSON.stringify({proposal:p,validation:v,approval:item.approval||null},null,2))}</pre></details>`;
  chart('before-chart',allocation(before));
  // A rejected allocation is not drawn as if it were a valid 100% portfolio.
  if(v.valid) chart('after-chart',target); else { $('after-chart').hidden=true; $('after-chart').parentNode.insertAdjacentHTML('beforeend','<p class="warning">Alocação inválida</p>'); }
}
async function choose(path, button) {
  const version=++requestVersion; $('error').hidden=true; $('simulate').disabled=true;
  try {const item=await api(path);if(version!==requestVersion)return;document.querySelectorAll('[data-case]').forEach(b=>{b.classList.remove('active');b.setAttribute('aria-pressed','false');});button?.classList.add('active');button?.setAttribute('aria-pressed','true');renderPlan(item);} catch(exc){if(version===requestVersion)error(exc);} finally{if(version===requestVersion)$('simulate').disabled=false;}
}
$('simulate').addEventListener('click',()=>choose('scenario?name='+encodeURIComponent($('scenario').value)));
$('case-buttons').addEventListener('click',event=>{const button=event.target.closest('[data-case]');if(button)choose('case?case='+button.dataset.case,button);});
async function start() {state=await api('status');if(!state.initialized)throw new Error(state.reason);renderWallet();await choose('case?case=A');}
start().catch(error);
