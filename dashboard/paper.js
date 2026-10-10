/* Prospective records only. Loading a page performs GETs; paid inference is an explicit POST. */
"use strict";
const $ = (id) => document.getElementById(id);
const esc = (v) => String(v ?? "Não registrado").replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const money = (v) => v == null ? "Não registrado" : Number(v).toLocaleString("pt-BR", {style:"currency",currency:"BRL"});
const pct = (v) => v == null ? "Não registrado" : (v * 100).toLocaleString("pt-BR", {maximumFractionDigits:2}) + "%";
const num = (v) => v == null ? "Não registrado" : Number(v).toLocaleString("pt-BR", {maximumFractionDigits:6});
const chip = (v) => `<span class="chip">${esc(v)}</span>`;
const facts = (rows) => `<dl>${rows.map(([k,v])=>`<dt>${esc(k)}</dt><dd>${v}</dd>`).join("")}</dl>`;
const metric = (label,value,sub="") => `<div class="card"><small>${esc(label)}</small><div class="value">${value}</div><small>${esc(sub)}</small></div>`;
let wallets = [], chart, decisionVersion = 0;
async function api(path, options) {
  const r = await fetch(`/api/forward/${path}`, {cache:"no-store",...options});
  const value = await r.json();
  if (!r.ok) throw Error(value?.error || `HTTP ${r.status}`);
  return value;
}
function error(e) { $("error").hidden = false; $("error").textContent = `Não foi possível concluir: ${e.message}. Consulte os registros novamente; nenhuma inferência é iniciada automaticamente.`; }
function renderDecision(d) {
  if (!d) { $("decision").innerHTML = '<p class="empty">Nenhuma sessão prospectiva registrada. Atualize os dados para preparar a primeira entrada.</p>'; return; }
  const c=d.consensus||{}, risk=d.risk||{}, p=d.portfolio||{};
  const analysts = Array.from({length:5},(_,i) => {
    const calls=(d.analysts||[]).filter(a=>Number(a.analyst_id)===i+1);
    return `<article class="card"><h3>Technical Analyst ${i+1}</h3>${calls.length ? calls.map(a=>`${chip(a.signal||a.status)}<p>Confiança: ${num(a.confidence)}</p><details><summary>Evidências e explicação</summary>${a.evidence.map(e=>`<span class="evidence">${esc(e.code)} · ${esc(e.role)}</span>`).join("")}<p class="muted">${esc(a.explanation)}</p><small>Registro ${esc(a.sequence)} · ${esc(a.status)}</small></details>`).join("") : '<p class="muted">Sem resposta gravada.</p>'}</article>`;
  }).join("");
  $("decision").innerHTML = `<div class="row spread"><p>${chip(d.status)} ${chip(d.ticker||"PETR4.SA")}</p><small>${d.replayed_from_journal ? "Replay offline do journal" : "Decisão prospectiva registrada"} · ${esc(d.generated_at)}</small></div>
    ${d.failure?`<p class="callout bad">${esc(d.failure)}</p>`:""}
    <div class="metrics">${metric("Data de referência",esc(d.session),"Fechamento da sessão")}${metric("Fechamento utilizado",money(d.close_used),"Preço ajustado congelado")}${metric("Próximo pregão",esc(d.target_session),"Execução na abertura, se elegível")}${metric("Prazo de abertura",esc(d.target_open_deadline?.slice(11,16)||"—"),"America/Sao_Paulo")}</div>
    <h2>Cinco leituras técnicas</h2><div class="analysts">${analysts}</div>
    <div class="card"><h2>Consenso técnico agregado</h2><div class="row">${chip(c.technical_outcome)}${Object.entries(c.vote_counts||{}).map(([k,v])=>chip(`${k}: ${v}`)).join("")}</div><p>${esc(c.signal?.justification)}</p><small>Limiar ${pct(c.consensus_threshold)} · votos válidos ${esc(c.valid_votes)} · consenso ${c.consensus_reached==null?"não registrado":c.consensus_reached?"atingido":"não atingido"}</small><details><summary>Evidências recorrentes (${d.evidence_summary?.length||0})</summary>${(d.evidence_summary||[]).map(e=>`<span class="evidence">${esc(e.code)} · ${esc(e.role)} · ${e.count} registros</span>`).join("")}</details></div>
    <div class="pair"><article class="card"><h2>Risk Manager</h2><p>${chip(risk.verdict)} ${chip(risk.risk_source)} ${risk.veto_effect?chip(`Veto ${risk.veto_effect}`):""}</p>${facts(Object.entries(risk.metrics||{}).map(([k,v])=>[k,num(v)]))}<p>${esc(risk.analysis)}</p><details><summary>Regras registradas e limites do tratamento</summary>${(risk.rules||[]).map(r=>`<p class="muted">${esc(r.rule)}: ${esc(r.status)} · ${num(r.value)} · limite ${esc(r.operator)} ${num(r.limit)}</p>`).join("")}${risk.risk_rule?chip(risk.risk_rule):""}</details></article>
    <article class="card"><h2>Portfolio Manager</h2><p>${chip(p.decision)} ${chip(p.final_cause)}</p><p>${esc(p.reasoning)}</p>${facts([["Posição no fechamento da decisão",pct(p.observed_weight)],["Posição-alvo",pct(p.target_weight)],["Ordem pendente",d.pending?`Alvo ${pct(d.pending.target_weight)} · abertura ${esc(d.pending.target_session)}`:"Nenhuma ordem pendente desta decisão"],["Execução observada",d.execution?`${esc(d.execution.session)} · ${d.execution.trades.length} operações registradas`:"Ainda não observada nos registros"]])}<p class="muted">A posição-alvo é uma recomendação futura. A composição financeira atual está em Carteiras.</p></article></div>`;
}
async function loadDecision(session="") {
  const version=++decisionVersion;
  try { const d=await api(`decision${session?`?session=${encodeURIComponent(session)}`:""}`); if(version===decisionVersion) renderDecision(d); } catch(e) { if(version===decisionVersion) error(e); }
}
function table(headers,rows) { return `<div class="scroll"><table><thead><tr>${headers.map(h=>`<th>${esc(h)}</th>`).join("")}</tr></thead><tbody>${rows.map(r=>`<tr>${r.map(v=>`<td>${v}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`; }
function renderComposition() {
  const w=wallets.find(w=>w.key===$("strategy").value);
  if(!w) return;
  document.querySelectorAll("[data-wallet]").forEach(el=>el.classList.toggle("selected",el.dataset.wallet===w.key));
  if(!w.available) { $("composition").innerHTML=`<p class="empty">${esc(w.label)}: ${esc(w.reason)}</p>`; return; }
  $("composition").innerHTML=`<article class="card"><h2>${esc(w.label)} · composição atual</h2><p class="muted">Marcação observada: ${esc(w.mark?.session)} · ${money(w.mark?.close)} por unidade ajustada</p><div class="allocation" aria-hidden="true">${w.composition.map(c=>`<span style="width:${Math.max(0,Math.min(100,c.weight*100))}%"></span>`).join("")}</div>${table(["Ativo","Peso","Quantidade","Valor marcado"],w.composition.map(c=>[esc(c.asset),pct(c.weight),c.asset==="Caixa"?"—":num(c.units),money(c.value)]))}
    <div class="metrics">${metric("Posições",num(w.position_count))}${metric("Exposição",pct(w.exposure))}${metric("Custos executados",money(w.costs))}${metric("Patrimônio virtual",money(w.equity))}</div>
    ${facts([["Última decisão",w.last_decision?`${esc(w.last_decision.session)} · ${esc(w.last_decision.status)}`:w.key==="buy_and_hold"?"Compra única na primeira abertura após a inicialização":"Sem decisão"],["Ordem pendente",w.pending?`${esc(w.pending.target_session)} · alvo ${pct(w.pending.target_weight)}`:"Nenhuma"],["Próxima ação possível",w.pending?"Aguardar preço observado da abertura e reconciliação do runner":"Decidir após o próximo fechamento / consultar preflight"]])}
    <h2 style="margin-top:20px">Histórico de operações executadas</h2>${w.trades.length?table(["Sessão","Tipo","Quantidade","Preço","Custo"],w.trades.map(t=>[esc(t.session),esc(t.type),num(t.quantity),money(t.price),money(t.cost)])):'<p class="empty">Nenhuma operação executada. Ordens pendentes não são patrimônio investido.</p>'}</article>`;
}
function renderWallets(data) {
  wallets=data.wallets;
  const selected=$("strategy").value;
  $("strategy").innerHTML=wallets.map(w=>`<option value="${esc(w.key)}">${esc(w.label)}</option>`).join("");
  if(wallets.some(w=>w.key===selected)) $("strategy").value=selected;
  $("wallet-cards").innerHTML=wallets.map(w=>`<article class="card" data-wallet="${esc(w.key)}"><h3>${esc(w.label)}</h3>${w.available?`<div class="value">${money(w.equity)}</div><p class="${w.return<0?"bad":"good"}">${pct(w.return)} acumulado</p><small>${w.pending?"Ordem pendente":"Sem ordem pendente"} · ${w.trades.length} operações</small>`:`<p class="warn">Não disponível para comparação</p><small>${esc(w.reason)}</small>`}</article>`).join("");
  $("comparison-note").textContent=data.comparison_note||"Somente curvas dos registros prospectivos. Um único fechamento ainda não permite medir evolução; não há retornos anteriores à inicialização.";
  const available=wallets.filter(w=>w.available && w.comparable!==false), colors=["#3987e5","#c98500","#d55181","#199e70"];
  if(chart) chart.destroy();
  if(available.length && typeof Chart!=="undefined") chart=new Chart($("equity"), {
    type:"line",
    data:{labels:available[0].curve.map(r=>r.session), datasets:available.map((w,i)=>({label:w.label,data:w.curve.map(r=>r.equity),borderColor:colors[i],pointRadius:4,borderWidth:2,tension:0}))},
    options:{responsive:true,maintainAspectRatio:false,animation:false,
      plugins:{legend:{labels:{color:"#c3c2b7"}}},
      scales:{x:{ticks:{color:"#a5a39b"},grid:{color:"#ffffff0a"}},y:{ticks:{color:"#a5a39b",callback:v=>money(v)},grid:{color:"#ffffff12"}}}
    }
  });
  $("curve-table").innerHTML=`<details><summary>Valores do gráfico em tabela</summary>${table(["Estratégia","Sessão","Patrimônio"],available.flatMap(w=>w.curve.map(r=>[esc(w.label),esc(r.session),money(r.equity)])))}</details>`;
  renderComposition();
}
async function refresh() {
  $("error").hidden=true;
  try {
    const [history,data]=await Promise.all([api("history"),api("portfolios")]);
    const selected=$("session").value;
    $("session").innerHTML=history.map(r=>`<option value="${esc(r.session)}">${esc(r.session)} · ${esc(r.status)}</option>`).reverse().join("");
    if(history.some(r=>r.session===selected)) $("session").value=selected;
    renderWallets(data); await loadDecision($("session").value);
  } catch(e) { error(e); }
}
$("session").addEventListener("change",()=>loadDecision($("session").value));
$("strategy").addEventListener("change",renderComposition);
$("refresh").addEventListener("click",refresh);
refresh();
