/* Prospective records only. Loading a page performs GETs; paid inference is an explicit POST. */
"use strict";
const $ = (id) => document.getElementById(id);
const ND = "N/D";
const esc = (v) => String(v ?? ND).replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const money = (v) => v == null ? ND : Number(v).toLocaleString("pt-BR", {style:"currency",currency:"BRL"});
const pct = (v, digits=2) => v == null ? ND : (v * 100).toLocaleString("pt-BR", {maximumFractionDigits:digits}) + "%";
const num = (v, digits=6) => v == null ? ND : Number(v).toLocaleString("pt-BR", {maximumFractionDigits:digits});
const day = (s) => /^\d{4}-\d{2}-\d{2}/.test(s || "") ? s.slice(0,10).split("-").reverse().join("/") : esc(s);
const stamp = (s) => s ? `${day(s)} ${esc(s.slice(11,16))}` : ND;
const chip = (v, cls="") => `<span class="chip ${cls}">${esc(v)}</span>`;
const TONE = {COMPRA:"buy",VENDA:"sell",MANTER:"hold",APROVADO:"buy",VETADO:"sell",PENDENTE:"warn",EXECUTADA:"buy",NAO_EXECUTAVEL:"sell",SEM_ORDEM:"sell"};
const signal = (v) => chip(v ?? "Sem sinal", `sig-${TONE[v] || "none"}`);
const facts = (rows, cls="") => `<dl class="${cls}">${rows.map(([k,v])=>`<dt>${esc(k)}</dt><dd>${v}</dd>`).join("")}</dl>`;
const empty = (title, text="") => `<div class="empty"><strong>${esc(title)}</strong>${text ? `<p>${text}</p>` : ""}</div>`;
const signed = (v, fmt) => v == null ? ND : `${v > 0 ? "▲ +" : v < 0 ? "▼ " : ""}${fmt(v)}`;
const tone = (v) => v > 0 ? "good" : v < 0 ? "bad" : "flat";
const agentName = (id) => esc(`TA-${String(id).padStart(2,"0")}`);
const table = (headers, rows) => `<div class="scroll" tabindex="0" role="region" aria-label="Tabela rolável"><table><thead><tr>${headers.map(h=>`<th scope="col">${esc(h)}</th>`).join("")}</tr></thead><tbody>${rows.map(r=>`<tr>${r.map(v=>`<td>${v}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
// Validated categorical order (dark surface, adjacent pairs); dashes are the secondary encoding.
const COLORS = {ai:"#3987e5",buy_and_hold:"#d95926",sma_regime_h2_proposed:"#199e70",bollinger_state_h2_proposed:"#c98500"};
const DASH = {ai:[],buy_and_hold:[7,4],sma_regime_h2_proposed:[2,3],bollinger_state_h2_proposed:[10,3,2,3]};
const ROLE = {SUPPORTS_COMPRA:["Suporte à COMPRA","buy"],SUPPORTS_VENDA:["Suporte à VENDA","sell"],CAUTION:["Cautela","warn"],NEUTRAL:["Neutro","hold"]};
let wallets = [], latest = null, agentsData = null, records = [], selectedAgent = "TA-01", visible = null, charts = {}, decisionVersion = 0, refreshVersion = 0;

async function api(path, options) {
  const r = await fetch(`/api/forward/${path}`, {cache:"no-store",...options});
  const value = await r.json();
  if (r.status === 404 && value === null) return null;  // no record yet: render the empty state
  if (!r.ok) throw Error(value?.error || `HTTP ${r.status}`);
  return value;
}
function error(e) {
  $("error").hidden = false;
  $("error").innerHTML = `<p>Não foi possível concluir: ${esc(e.message)}. Nenhuma inferência é iniciada automaticamente.</p><button id="retry">Consultar novamente</button>`;
}

/* ── Navegação ─────────────────────────────────────────────── */
const VIEWS = ["visao","sala","carteiras","agentes"], LEGACY = {room:"sala",wallets:"carteiras"};
function route() {
  const hash = (typeof location === "undefined" ? "" : location.hash).slice(1);
  const view = VIEWS.includes(hash) ? hash : LEGACY[hash] || "visao";
  document.querySelectorAll("[data-view]").forEach(s => s.hidden = s.id !== view);
  document.querySelectorAll("[data-tab]").forEach(a => a.dataset.tab === view ? a.setAttribute("aria-current","page") : a.removeAttribute("aria-current"));
}

/* ── Gráfico de patrimônio: 0, 1 ou 2+ observações ─────────── */
function equityChart(id, list) {
  const box = $(id);
  charts[id]?.destroy(); delete charts[id];
  const points = Math.max(0, ...list.map(w => w.curve.length));
  if (!list.length) { box.innerHTML = empty("Nenhuma estratégia comparável selecionada"); return; }
  if (points < 2) {
    box.innerHTML = `<div class="empty compact"><strong>${points ? `1 fechamento reconciliado · ${day(list[0].curve[0].session)}` : "Sem fechamentos reconciliados"}</strong>
      <p>${points ? "Todas partem do mesmo ponto. A curva aparece a partir do segundo fechamento reconciliado; não existem valores anteriores à inicialização." : "A curva começa no primeiro fechamento reconciliado."}</p>
      ${points ? `<ul class="start-points">${list.map(w=>`<li><span class="swatch" style="--series:${COLORS[w.key]}" aria-hidden="true"></span>${esc(w.label)} <strong>${money(w.curve[0].equity)}</strong></li>`).join("")}</ul>` : ""}</div>`;
    return;
  }
  box.innerHTML = `<div class="chart"><canvas role="img" aria-label="Patrimônio prospectivo por estratégia; valores na tabela abaixo"></canvas></div><details><summary>Valores do gráfico em tabela</summary>${table(["Estratégia","Sessão","Patrimônio"], list.flatMap(w=>w.curve.map(r=>[esc(w.label),day(r.session),money(r.equity)])))}</details>`;
  if (typeof Chart === "undefined") return;
  charts[id] = new Chart(box.querySelector("canvas"), {
    type:"line",
    data:{labels:list[0].curve.map(r=>day(r.session)), datasets:list.map(w=>({label:w.label,data:w.curve.map(r=>r.equity),borderColor:COLORS[w.key],backgroundColor:COLORS[w.key],borderDash:DASH[w.key],pointRadius:3,pointHoverRadius:5,borderWidth:2,tension:0}))},
    options:{responsive:true,maintainAspectRatio:false,animation:false,interaction:{mode:"index",intersect:false},
      plugins:{legend:{labels:{color:"#c3c2b7",usePointStyle:true}},tooltip:{callbacks:{label:(c)=>`${c.dataset.label}: ${money(c.parsed.y)}`}}},
      scales:{x:{ticks:{color:"#a5a39b"},grid:{display:false}},y:{ticks:{color:"#a5a39b",callback:v=>money(v)},grid:{color:"#ffffff12"}}}}
  });
}

/* ── Visão Geral ───────────────────────────────────────────── */
function latestMark() { return wallets.map(w => w.mark?.session).filter(Boolean).sort().at(-1); }
function walletCard(w) {
  const head = `<div class="wallet-head"><h3><span class="swatch" aria-hidden="true"></span>${esc(w.label)}</h3>${w.pending ? chip("Ordem pendente","sig-warn") : ""}</div>`;
  if (!w.available) return `<article class="card wallet" style="--series:${COLORS[w.key]}">${head}${empty("Sem carteira prospectiva", esc(w.reason))}</article>`;
  const stale = w.mark?.session < latestMark();
  return `<article class="card wallet" style="--series:${COLORS[w.key]}">${head}
    <div class="value">${money(w.equity)}</div>
    <p class="delta ${tone(w.return)}">${signed(w.return, pct)} · ${signed(w.pnl, money)}</p>
    ${facts([["PETR4 investido",money(w.marked_value)],["Caixa",money(w.cash)],["Exposição",pct(w.exposure)],["Custos",money(w.costs)],["Operações",num(w.trades.length)],["Drawdown máx.",w.max_drawdown == null ? `${ND} <small>· requer 2+ fechamentos</small>` : pct(w.max_drawdown)]],"mini")}
    <small class="${stale || w.comparable === false ? "warn" : "muted"}">${stale ? "Sem novos dados desde" : "Marcação"} ${day(w.mark?.session)}${w.comparable === false ? " · fora da comparação" : ""}</small></article>`;
}
function renderOverviewChart() {
  const comparable = wallets.filter(w => w.available && w.comparable !== false);
  visible ??= new Set(comparable.map(w => w.key));
  // Toggles only exist when there is a curve for them to change.
  $("overview-series").innerHTML = comparable.some(w => w.curve.length > 1) ? comparable.map(w=>`<label class="toggle"><input type="checkbox" data-series="${esc(w.key)}" ${visible.has(w.key) ? "checked" : ""} /><span class="swatch" style="--series:${COLORS[w.key]}" aria-hidden="true"></span>${esc(w.label)}</label>`).join("") : "";
  equityChart("overview-chart", comparable.filter(w => visible.has(w.key)));
}
function renderLastDecision(d) {
  if (!d?.consensus) { $("last-decision").innerHTML = `<h2>Última deliberação</h2>${empty("Nenhuma decisão prospectiva registrada", d ? `Sessão ${day(d.session)}: ${esc(d.status)}.` : "Prepare os dados e execute o preflight na Sala de Decisão.")}<a class="action" href="#sala">Abrir Sala de Decisão →</a>`; return; }
  const c = d.consensus, ai = wallets.find(w => w.key === "ai");
  $("last-decision").innerHTML = `<div class="card-head"><h2>Última deliberação</h2>${chip(d.status)}</div>
    ${facts([["Ativo",esc(d.ticker)],["Data de referência",`${day(d.session)} · fechamento`],["Consenso",`${signal(c.consensus_reached ? c.technical_outcome : "SEM CONSENSO")} ${esc(c.signal?.justification)}`],["Risk Manager",signal(d.risk?.verdict)],["Portfolio Manager",`${signal(d.portfolio?.decision)} alvo ${pct(d.portfolio?.target_weight)}`],["Ordem",`${chip(d.order?.label, `sig-${TONE[d.order?.state] || "none"}`)} <small class="muted">${esc(d.order?.detail)}</small>`]])}
    <div class="split"><div class="intent"><small>Sinal futuro · abertura de ${day(d.target_session)}</small><strong>Alvo ${pct(d.portfolio?.target_weight)} em PETR4</strong></div>
    <div class="actual"><small>Posição executada · marcação ${day(ai?.mark?.session)}</small><strong>${pct(ai?.exposure)} PETR4 · ${pct(ai?.composition?.[1]?.weight)} caixa</strong></div></div>
    <a class="action" href="#sala">Abrir Sala de Decisão →</a>`;
}
function renderOverview() {
  $("overview-wallets").innerHTML = wallets.length ? wallets.map(walletCard).join("") : empty("Nenhuma carteira prospectiva", "O ledger da IA ainda não foi inicializado.");
  renderOverviewChart();
  renderLastDecision(latest);
  $("updated").textContent = `Última marcação: ${latestMark() ? day(latestMark()) : ND}${latest?.generated_at ? ` · última decisão gerada em ${stamp(latest.generated_at)}` : ""}`;
}

/* ── Sala de Decisão ───────────────────────────────────────── */
function analystCard(i, calls) {
  const last = calls.at(-1);
  const status = !last ? "Sem resposta gravada" : last.status === "ok" ? `Resposta válida${last.retry_count ? ` · ${last.retry_count} retry` : ""}` : `Resposta inválida${last.error_type ? ` · ${esc(last.error_type)}` : ""}`;
  return `<article class="card analyst${last?.signal ? "" : " missing"}">
    <div class="who"><span class="avatar" aria-hidden="true">TA<b>${i}</b></span><div><h3>${agentName(i)}</h3><small>Technical Analyst</small></div></div>
    ${signal(last?.signal)}
    ${last?.confidence != null ? `<div class="meter" aria-hidden="true"><span style="width:${last.confidence * 100}%"></span></div><small>Confiança registrada <strong>${num(last.confidence, 2)}</strong></small>` : "<small>Confiança N/D</small>"}
    <small class="${last?.status === "ok" ? "muted" : "warn"}">${status}</small>
    ${calls.length ? `<details><summary>Ver análise de ${agentName(i)}</summary>${calls.map(a=>`<ul class="evidence-list">${a.evidence.map(e=>`<li>${chip(ROLE[e.role]?.[0] || e.role, `sig-${ROLE[e.role]?.[1] || "none"}`)} ${esc(e.label)}</li>`).join("")}</ul><details><summary>Texto original gravado</summary><p class="quote">${esc(a.explanation)}</p></details><small class="muted">Registro #${esc(a.sequence)} · ${esc(a.status)}</small>`).join("<hr/>")}</details>` : ""}
  </article>`;
}
function quorumCard(d) {
  const c = d.consensus || {}, k = d.committee || {}, counts = c.vote_counts || {}, n = k.analyst_count || 0;
  const den = k.require_all_votes ? n : c.valid_votes;
  const [top, topCount] = Object.entries(counts).sort((a,b) => b[1] - a[1])[0] || [null, 0];
  const share = den ? topCount / den : null;
  const winners = d.analysts.filter(a => a.signal === top && a.confidence != null);
  const mean = winners.length ? winners.reduce((s,a) => s + a.confidence, 0) / winners.length : null;
  const slots = Array.from({length:n}, (_,i) => d.analysts.filter(a => Number(a.analyst_id) === i + 1).at(-1)?.signal);
  return `<article class="card quorum"><h2>Quórum do comitê</h2>
    <div class="pips" role="img" aria-label="${slots.map((v,i)=>`${agentName(i+1)}: ${v || "sem voto"}`).join("; ")}">${slots.map(v=>`<span class="pip sig-${TONE[v] || "none"}"></span>`).join("")}</div>
    <div class="vote-bars">${["COMPRA","VENDA","MANTER"].map(s=>`<div class="vote-row"><span>${s}</span><div class="track" aria-hidden="true"><span class="sig-${TONE[s]}" style="width:${n ? (counts[s] || 0) / n * 100 : 0}%"></span></div><strong>${counts[s] ?? 0}</strong></div>`).join("")}</div>
    <div class="threshold"><div class="track" aria-hidden="true"><span style="width:${(share || 0) * 100}%"></span><i style="left:${(c.consensus_threshold || 0) * 100}%"></i></div>
    <p>Sinal mais votado: <strong>${pct(share)}</strong> · limiar exigido <strong>${pct(c.consensus_threshold)}</strong>${k.require_all_votes ? " · todas as respostas exigidas" : ""}</p></div>
    <p class="result">Resultado agregado ${signal(c.consensus_reached ? c.technical_outcome : c.consensus_reached === false ? "SEM CONSENSO" : null)}</p>
    <p>Confiança coletiva registrada <strong>${num(c.signal?.confidence, 4)}</strong>${mean != null && share != null && c.consensus_reached ? ` <small class="muted">= ${num(mean, 4)} × ${topCount}/${den}</small>` : ""}</p>
    <p class="muted small">O agregador multiplica a média das confianças dos votos vencedores pela fração do comitê nesse sinal. É a autoavaliação registrada pelo modelo, não uma probabilidade de acerto.</p></article>`;
}
function synthesis(d) {
  const n = d.committee?.responded || 0, outcome = d.consensus?.technical_outcome;
  // Favorable/contrary only have a referent for a directional outcome (see forward_api.stance).
  const groups = ["COMPRA","VENDA"].includes(outcome)
    ? [["favorable",`Favoráveis à ${outcome}`,"buy"],["caution","Cautela","warn"],["contrary",`Contrárias à ${outcome}`,"sell"],["neutral","Neutras","hold"]]
    : [["supports_compra","Suporte à COMPRA","buy"],["supports_venda","Suporte à VENDA","sell"],["caution","Cautela","warn"],["neutral","Neutras","hold"]];
  const items = d.evidence_summary || [];
  const col = ([key,title,cls]) => { const list = items.filter(e => e.stance === key); return `<div class="stance"><h3>${chip(title,`sig-${cls}`)}</h3>${list.length ? `<ul>${list.map(e=>`<li><span>${esc(e.label)}</span><span class="freq" aria-hidden="true"><span style="width:${n ? e.count / n * 100 : 0}%"></span></span><small>${e.count}/${n} analistas · ${e.analysts.map(agentName).join(", ")}</small></li>`).join("")}</ul>` : '<p class="muted">Nenhuma.</p>'}</div>`; };
  return `<article class="card"><div class="card-head"><h2>Por que os agentes decidiram isso?</h2><small class="muted">Derivado das evidências estruturadas gravadas · nenhuma nova chamada ao modelo</small></div>
    ${items.length ? `<div class="stances">${groups.map(col).join("")}</div>` : empty("Sem evidências estruturadas gravadas")}
    <h3>Divergências entre agentes</h3>${(d.divergences || []).length ? `<ul class="divergences">${d.divergences.map(t=>`<li>${esc(t)}</li>`).join("")}</ul>` : `<p class="muted">${n ? "Nenhuma divergência: votos e classificações das evidências coincidem. Diferenças de frequência indicam apenas quantos analistas citaram cada evidência." : "Sem respostas válidas para comparar."}</p>`}</article>`;
}
function renderDecision(d) {
  if (!d) { $("decision").innerHTML = empty("Nenhuma sessão prospectiva registrada", "Atualize os dados para preparar a primeira entrada."); return; }
  if (!d.consensus) { $("decision").innerHTML = empty(`Sessão ${day(d.session)} · ${d.status}`, d.status === "MISSED" ? "Nenhuma decisão foi registrada antes da abertura seguinte; posição mantida." : "Input preparado, sem decisão gravada."); return; }
  const risk = d.risk || {}, p = d.portfolio || {}, n = d.committee?.analyst_count || 0;
  const flow = (d.flow || []).map(s=>`<li><small>${esc(s.stage)}</small>${signal(s.result)}<p>${esc(s.detail)}</p>${s.changed === false ? '<span class="tag">Não alterou</span>' : s.changed ? '<span class="tag warn">Alterou</span>' : ""}</li>`).join("");
  $("decision").innerHTML = `<div class="meta">${chip(d.status)} ${chip(d.ticker || "PETR4.SA")} <span>Referência <strong>${day(d.session)}</strong></span><span>Fechamento usado <strong>${money(d.close_used)}</strong></span><span>Abertura-alvo <strong>${day(d.target_session)} ${esc(d.target_open_deadline?.slice(11,16) || "")}</strong></span><span class="muted">${d.replayed_from_journal ? "Replay offline do journal" : "Gerada em"} ${stamp(d.generated_at)}</span></div>
    ${d.failure ? `<p class="callout bad">${esc(d.failure)}</p>` : ""}
    <ol class="flow" aria-label="Fluxo da decisão">${flow}</ol>
    <div class="room-grid"><div><h2>Comitê técnico · ${n} analistas</h2><div class="analysts">${Array.from({length:n}, (_,i) => analystCard(i + 1, d.analysts.filter(a => Number(a.analyst_id) === i + 1))).join("")}</div></div>${quorumCard(d)}</div>
    ${synthesis(d)}
    <div class="pair"><article class="card"><h2>Risk Manager</h2><p>${signal(risk.verdict)} ${chip(risk.risk_source)} ${risk.veto_effect ? chip(`Veto ${risk.veto_effect}`) : ""}</p><p>${esc(risk.analysis)}</p>${table(["Regra","Valor","Limite","Estado"], (risk.rules || []).map(r=>[esc(r.rule),num(r.value),`${esc(r.operator)} ${num(r.limit)}`,chip(r.status, r.status === "PASSOU" ? "sig-buy" : r.status === "DISPAROU" ? "sig-sell" : "")]))}</article>
    <article class="card"><h2>Portfolio Manager</h2><p>${signal(p.decision)} ${chip(p.final_cause)}</p><p>${esc(p.reasoning)}</p>
      <h3>Da recomendação à execução</h3>${facts([["Sinal técnico",signal(d.consensus.technical_outcome)],["Decisão final",signal(p.decision)],["Ordem pretendida",d.intent_weight == null ? "Nenhuma" : `Alvo ${pct(d.intent_weight)} PETR4`],["Ordem pendente",d.pending ? `Sim · abertura ${day(d.pending.target_session)}` : "Não"],["Ordem executada",d.execution ? `${day(d.execution.session)} · ${d.execution.trades.length} operação(ões)` : "Ainda não observada"],["Não executável",d.status === "LATE_NOT_EXECUTABLE" ? "Sim · decisão após a abertura" : "Não"],["Posição no fechamento",pct(p.observed_weight)]])}
      <p class="muted small">A posição-alvo é uma recomendação para a próxima abertura. A composição financeira atual está em Carteiras.</p></article></div>`;
}
function renderHistory() {
  $("history").innerHTML = records.length ? table(["Sessão","Estado","COMPRA / VENDA / MANTER","Sinal técnico","Decisão final","Alvo",""], records.slice().reverse().map(r=>[day(r.session),chip(r.status),r.vote_counts ? `${r.vote_counts.COMPRA ?? 0} / ${r.vote_counts.VENDA ?? 0} / ${r.vote_counts.MANTER ?? 0}` : ND,signal(r.technical_outcome),signal(r.final_decision),pct(r.target_weight),r.has_decision ? `<button data-session="${esc(r.session)}">Abrir</button>` : ""])) : empty("Nenhuma deliberação registrada");
}
async function loadDecision(session="") {
  const version = ++decisionVersion;
  try { const d = await api(`decision${session ? `?session=${encodeURIComponent(session)}` : ""}`); if (version === decisionVersion) renderDecision(d); } catch(e) { if (version === decisionVersion) error(e); }
}

/* ── Carteiras ─────────────────────────────────────────────── */
function allocation(w) {
  const [stock, cash] = w.composition;
  return `<div class="allocation" role="img" aria-label="PETR4 ${pct(stock.weight)}, caixa ${pct(cash.weight)}">${stock.weight > 0 ? `<span class="seg stock" style="width:${stock.weight * 100}%"></span>` : ""}${cash.weight > 0 ? `<span class="seg cash" style="width:${cash.weight * 100}%"></span>` : ""}</div>
    <ul class="legend"><li><i class="key stock"></i>PETR4 <strong>${pct(stock.weight)}</strong> · ${money(stock.value)} · ${num(stock.units)} unidades</li><li><i class="key cash"></i>Caixa <strong>${pct(cash.weight)}</strong> · ${money(cash.value)}</li></ul>`;
}
function renderComposition() {
  const w = wallets.find(w => w.key === $("strategy").value);
  document.querySelectorAll("[data-wallet]").forEach(el => el.setAttribute("aria-pressed", String(el.dataset.wallet === w?.key)));
  if (!w) { $("composition").innerHTML = ""; $("trades").innerHTML = ""; return; }
  if (!w.available) { $("composition").innerHTML = `<article class="card">${empty(`${w.label}: sem carteira prospectiva`, esc(w.reason))}</article>`; $("trades").innerHTML = ""; return; }
  $("composition").innerHTML = `<article class="card" style="--series:${COLORS[w.key]}"><div class="card-head"><h2><span class="swatch" aria-hidden="true"></span>${esc(w.label)} · composição atual</h2><small class="muted">Marcação ${day(w.mark?.session)} · ${money(w.mark?.close)} por unidade ajustada</small></div>
    <div class="value">${money(w.equity)} <small class="delta ${tone(w.return)}">${signed(w.return, pct)} · ${signed(w.pnl, money)}</small></div>
    <h3>Posição executada</h3>${allocation(w)}
    ${w.pending ? `<h3>Intenção pendente</h3><div class="allocation target" role="img" aria-label="Alvo ${pct(w.pending.target_weight)} PETR4, não executado"><span class="seg ghost" style="width:${w.pending.target_weight * 100}%"></span></div><p class="muted small">Alvo ${pct(w.pending.target_weight)} PETR4 na abertura de ${day(w.pending.target_session)}. Uma intenção de compra não é posição: a composição só muda após a execução observada.</p>` : ""}
    ${facts([["Patrimônio total",money(w.equity)],["Capital inicial",money(w.initial_capital)],["Exposição",pct(w.exposure)],["Custos acumulados",money(w.costs)],["Operações executadas",num(w.trades.length)],["Drawdown máximo",w.max_drawdown == null ? `${ND} · requer 2+ fechamentos` : pct(w.max_drawdown)],["Ordem pendente",w.pending ? `${day(w.pending.target_session)} · alvo ${pct(w.pending.target_weight)}` : "Nenhuma"],["Última decisão",w.last_decision ? `${day(w.last_decision.session)} · ${esc(w.last_decision.status)} · alvo ${pct(w.last_decision.target_weight)}` : w.key === "buy_and_hold" ? "Compra única na primeira abertura após a inicialização" : "Sem decisão"],["Proventos","Ainda não contabilizados"]],"wide")}</article>`;
  $("trades").innerHTML = `<article class="card"><h2>Operações executadas · ${esc(w.label)}</h2>${w.trades.length ? table(["Decisão","Execução","Ativo","Lado","Preço","Quantidade","Custo","Patrimônio no fechamento"], w.trades.map(t=>[t.decision_session ? day(t.decision_session) : w.key === "buy_and_hold" ? "Regra B&H" : ND,day(t.session),esc(t.asset),signal(t.type === "BUY" ? "COMPRA" : t.type === "SELL" ? "VENDA" : t.type),money(t.price),num(t.quantity),money(t.cost),money(t.equity_after)])) : empty("Nenhuma operação executada", "Ordens pendentes não são patrimônio investido.")}</article>`;
}
function renderWallets(data) {
  wallets = data?.wallets || [];
  const selected = $("strategy").value;
  $("strategy").innerHTML = wallets.map(w=>`<option value="${esc(w.key)}">${esc(w.label)}</option>`).join("");
  if (wallets.some(w => w.key === selected)) $("strategy").value = selected;
  $("wallet-table").innerHTML = wallets.length ? table(["Estratégia","Patrimônio","Retorno","Resultado","PETR4","Caixa","Exposição","Operações","Pendente","Custos","Atualização"], wallets.map(w => w.available ? [`<button class="link" data-wallet="${esc(w.key)}" style="--series:${COLORS[w.key]}"><span class="swatch" aria-hidden="true"></span>${esc(w.label)}</button>`,money(w.equity),`<span class="${tone(w.return)}">${signed(w.return, pct)}</span>`,`<span class="${tone(w.pnl)}">${signed(w.pnl, money)}</span>`,money(w.marked_value),money(w.cash),pct(w.exposure),num(w.trades.length),w.pending ? `Alvo ${pct(w.pending.target_weight)} · ${day(w.pending.target_session)}` : "—",money(w.costs),`${day(w.mark?.session)}${w.mark?.session < latestMark() ? ' <span class="warn">· sem novos dados</span>' : ""}`] : [esc(w.label),`<span class="warn">Indisponível</span>`,"","","","","","","","",""])) : empty("Nenhuma carteira prospectiva");
  const comparable = wallets.filter(w => w.available && w.comparable !== false);
  $("comparison-note").textContent = `${data?.comparison_note || ""}${comparable.length < wallets.length ? ` Fora do gráfico: ${wallets.filter(w => !comparable.includes(w)).map(w => w.label).join(", ")}.` : ""}`;
  equityChart("wallet-chart", comparable);
  renderComposition();
}

/* ── Agentes ───────────────────────────────────────────────── */
// ponytail: mirrors the ensemble rule in src/agents/technical_analyst.py (ties favour MANTER, then COMPRA).
function quorum(n, threshold, votes, requireAll) {
  const total = votes.COMPRA + votes.VENDA + votes.MANTER;
  if (Object.values(votes).some(v => !Number.isInteger(v) || v < 0) || total > n) return {error:`Informe votos inteiros que somem no máximo ${n}.`};
  const missing = n - total;
  if (requireAll && missing) return {reached:false, winner:null, share:null, text:`Quórum incompleto: ${missing} resposta(s) ausente(s) ou inválida(s). Sem consenso; o sinal seguro é MANTER.`};
  let winner = "MANTER";
  for (const s of ["COMPRA","VENDA"]) if (votes[s] > votes[winner]) winner = s;
  const den = requireAll ? n : total, share = den ? votes[winner] / den : 0, reached = share >= threshold;
  return {reached, winner:reached ? winner : null, share, text:reached ? `Consenso em ${winner}: ${votes[winner]}/${den} = ${pct(share)} ≥ ${pct(threshold)}.` : `Sem consenso: ${votes[winner]}/${den} = ${pct(share)} no sinal mais votado, abaixo de ${pct(threshold)}. O sinal seguro é MANTER.`};
}
function simulate() {
  const n = Number($("sim-n").value), votes = {COMPRA:Number($("sim-compra").value), VENDA:Number($("sim-venda").value), MANTER:Number($("sim-manter").value)};
  const r = quorum(n, Number($("sim-threshold").value), votes, $("sim-all").checked);
  $("sim-out").innerHTML = r.error ? `<span class="warn">${esc(r.error)}</span>` : `${signal(r.reached ? r.winner : "SEM CONSENSO")} ${esc(r.text)}`;
}
function agentTile(a) {
  const short = a.id.startsWith("TA") ? ["TA", Number(a.id.slice(3))] : [a.id, ""];
  if (!a.active) return `<div class="agent-tile idle"><span class="avatar" aria-hidden="true">${short[0]}<b>${short[1]}</b></span><div><strong>${esc(a.id)}</strong><small>Slot livre · sem histórico</small></div></div>`;
  const last = a.observations?.history?.at(-1);
  return `<button class="agent-tile" data-agent="${esc(a.id)}" aria-pressed="${a.id === selectedAgent}"><span class="avatar" aria-hidden="true">${short[0]}<b>${short[1]}</b></span><div><strong>${esc(a.id)}</strong><small>${esc(a.role)} · ativo na H2 v6</small>${last?.output ? signal(last.output) : ""}</div></button>`;
}
function renderProfile() {
  const a = agentsData?.agents.find(a => a.id === selectedAgent);
  if (!a) { $("profile").innerHTML = ""; return; }
  const o = a.observations, rate = (v) => v == null ? ND : pct(v, 1);
  $("profile").innerHTML = `<article class="card profile"><div class="card-head"><div class="who"><span class="avatar" aria-hidden="true">${a.id.startsWith("TA") ? `TA<b>${Number(a.id.slice(3))}</b>` : esc(a.id)}</span><div><h2>${esc(a.id)} · ${esc(a.role)}</h2><small class="muted">Ficha com dados registrados; métricas descritivas não medem competência individual.</small></div></div>${chip(a.active ? "Ativo · H2 v6" : "Slot livre")}</div>
    <div class="pair">${facts([["Modelo",a.params ? `${esc(a.params.provider)} · ${esc(a.params.model)}` : ND],["Versão do prompt",esc(a.prompt_version)],["Parâmetros",a.params ? Object.entries(a.params).filter(([k]) => !["provider","model"].includes(k)).map(([k,v])=>chip(`${k}=${v}`)).join(" ") : ND],["Seed observada",esc(o?.history.at(-1)?.seed)]])}
    ${o ? facts([["Chamadas registradas",num(o.calls)],["Sessões",num(o.sessions)],["Decisões registradas",num(o.decisions)],["Distribuição",Object.entries(o.outputs).map(([k,v])=>`${signal(k)} ${v}`).join(" ") || ND],["Confiança média",num(o.mean_confidence, 4)],["Concordância com o consenso",o.agreement == null ? ND : `${rate(o.agreement)} em ${o.agreement_n} sessão(ões) com consenso`],["Taxa de erro",rate(o.error_rate)],["Retries",`${o.retries} · ${rate(o.retry_rate)} das chamadas`],["Tokens",o.tokens == null ? `${ND} · não registrados pelo provedor` : `${num(o.tokens, 0)} · cobertura ${rate(o.token_coverage)}`],["Custo estimado",o.cost_usd == null ? ND : `US$ ${num(o.cost_usd, 5)} · preço de tabela do runner`]]) : empty("Sem observações", a.active ? "Nenhuma chamada registrada." : "Este slot não participou da H2 v6 nem de experimentos registrados.")}</div>
    ${o ? `<h3>Histórico de chamadas</h3>${table(["Sessão","Estado","Saída","Confiança","Tentativas","Tokens","Duração","Custo est. (US$)"], o.history.map(h=>[day(h.session),esc(h.status),signal(h.output),num(h.confidence, 2),num(h.attempt_count),num(h.tokens, 0),h.duration_ms == null ? ND : `${num(h.duration_ms / 1000, 1)} s`,num(h.cost_usd, 5)]))}` : ""}</article>`;
}
function renderAgents() {
  if (!agentsData) { $("committee").innerHTML = empty("Configuração indisponível"); $("catalog").innerHTML = ""; renderProfile(); return; }
  const c = agentsData.configuration, list = agentsData.agents, ta = list.filter(a => a.role === "Technical Analyst");
  $("committee").innerHTML = `<article class="card"><div class="card-head"><h2>Comitê ${esc(c.name)}</h2>${chip("Congelada · não editável","sig-warn")}</div>
    ${facts([["Analistas ativos",`${c.analyst_count} de ${ta.length} slots técnicos`],["Limiar de consenso",pct(c.consensus_threshold)],["Todas as respostas exigidas",c.require_all_votes ? "Sim" : "Não"],["Modelo",`${esc(c.provider)} · ${esc(c.model)} · T=${num(c.temperature)} · thinking ${esc(c.thinking_level)}`],["Posições no catálogo",`${c.slots} = ${ta.length} Technical + Risk + Portfolio`]])}
    <p class="muted small">Tamanhos planejados para experimentos futuros: 5 · 10 · 15 · 20 · 30 analistas. Cada configuração diferente exigirá identidade experimental e ledger próprios, em fase futura; a H2 v6 permanece com ${c.analyst_count}.</p></article>`;
  $("catalog").innerHTML = `<article class="card"><div class="card-head"><h2>Technical Analysts · ${ta.length} slots</h2><small class="muted">${ta.filter(a => a.active).length} ativos na configuração observada · ${ta.filter(a => !a.active).length} livres, sem histórico</small></div><div class="agent-grid">${ta.map(agentTile).join("")}</div>
    <h2>Gestão</h2><div class="agent-grid">${list.filter(a => a.role !== "Technical Analyst").map(agentTile).join("")}</div></article>`;
  renderProfile();
}

/* ── Carga ─────────────────────────────────────────────────── */
async function refresh() {
  const version = ++refreshVersion;
  $("error").hidden = true;
  try {
    const [history, data, agents, last] = await Promise.all([api("history"), api("portfolios"), api("agents"), api("decision")]);
    if (version !== refreshVersion) return;
    records = history || []; latest = last; agentsData = agents;
    const selected = $("session").value;
    $("session").innerHTML = records.map(r=>`<option value="${esc(r.session)}">${day(r.session)} · ${esc(r.status)}</option>`).reverse().join("");
    if (records.some(r => r.session === selected)) $("session").value = selected;
    else if (records.some(r => r.has_decision)) $("session").value = records.filter(r => r.has_decision).at(-1).session;
    renderWallets(data); renderOverview(); renderHistory(); renderAgents();
    await loadDecision($("session").value);
  } catch(e) { error(e); }
}
$("session").addEventListener("change", () => loadDecision($("session").value));
$("strategy").addEventListener("change", renderComposition);
$("refresh").addEventListener("click", refresh);
$("error").addEventListener("click", (e) => { if (e.target.id === "retry") refresh(); });
$("history").addEventListener("click", (e) => { const s = e.target.dataset?.session; if (s) { $("session").value = s; loadDecision(s); } });
$("wallet-table").addEventListener("click", (e) => { const k = e.target.closest?.("[data-wallet]")?.dataset.wallet; if (k) { $("strategy").value = k; renderComposition(); } });
$("overview-series").addEventListener("change", (e) => { const k = e.target.dataset?.series; if (k) { e.target.checked ? visible.add(k) : visible.delete(k); renderOverviewChart(); } });
$("catalog").addEventListener("click", (e) => { const id = e.target.closest?.("[data-agent]")?.dataset.agent; if (id) { selectedAgent = id; renderAgents(); } });
$("sim-form").addEventListener("input", simulate);
$("sim-form").addEventListener("submit", (e) => e.preventDefault());
if (typeof window !== "undefined") window.addEventListener("hashchange", route);
route(); simulate(); refresh();

let csrf, busy=false, posting=false, report=null, completedJob=null, confirmationToken=null;
const checkLabels={treatment_identity:"Identidade H2 v6 e Git limpo",after_reserved_windows:"Fora das janelas reservadas",before_target_open:"Antes da abertura-alvo",not_yet_decided:"Decisão ainda não existe",no_active_lock:"Ledger sem lock ativo",gemini_api_key_present:"Chave configurada no backend",input_frozen:"Input congelado e íntegro",ledger_reconciles:"Carteira reconciliável"};
function controls() {
  ["prepare","preflight","benchmarks"].forEach(id=>$(id).disabled=busy||posting||!csrf);
  $("execute").disabled=busy||posting||!report?.ready||!report?.confirmation_token;
}
function renderReport() {
  if(!report) { $("preflight-report").innerHTML=""; return; }
  const c=report.calendar||{}, input=report.input||{}, m=report.model||{}, estimate=report.estimate||{};
  $("preflight-report").innerHTML=`<hr/><h3>Preflight ${chip(report.state)}</h3>${facts([["Referência → data-alvo",`${esc(c.decision_session)} → ${esc(c.target_session)}`],["Prazo",esc(c.target_open_deadline)],["Input SHA256",esc(input.sha256?.slice(0,12))],["Modelo registrado",`${esc(m.model)} · T=${num(m.temperature)} · thinking ${esc(m.thinking_level)} · ${report.identity_verified?"identidade verificada":"identidade ainda não verificada"}`],["Custo estimado (USD)",`${num(estimate.usd_expected)} esperado · ${num(estimate.usd_prudent_budget)} orçamento prudente · ${num(estimate.usd_theoretical_ceiling)} teto teórico`]])}<p class="muted">Estimativa registrada pelo runner, não cotação em tempo real. ${esc(estimate.price_note)}</p><details><summary>Verificações do backend</summary>${Object.entries(report.checks||{}).map(([key,ok])=>`<p class="${ok?"good":"bad"}">${ok?"✓":"×"} ${esc(checkLabels[key]||key)}</p>`).join("")}</details>${report.state==="DECISION_EXISTS"?'<p class="callout">Decisão já existente: somente consulta, sem nova chamada Gemini.</p>':report.state==="RECOVERY_REQUIRED"?'<p class="callout bad">Tentativa/journal anterior encontrado. Recuperação só por diagnóstico e replay offline; chamadas pagas bloqueadas.</p>':!report.ready?'<p class="muted">Execução bloqueada. Corrija os gates indicados e repita o preflight. Não remova registros ou locks sem diagnóstico local.</p>':'<p class="good">READY · confirmação válida por até 10 minutos e vinculada ao input e ao ledger.</p>'}`;
}
async function submit(command,payload={}) {
  if(posting||busy) return;
  posting=true; controls(); $("error").hidden=true;
  try {
    const job=await api(command,{method:"POST",headers:{"Content-Type":"application/json","X-CSRF-Token":csrf},body:JSON.stringify(payload)});
    report=null; renderReport(); busy=true;
    $("job").textContent=`${job.command}: solicitado · ${job.session}. Acompanhe abaixo.`;
  } catch(e) { error(e); report=null; renderReport(); }
  finally { posting=false; controls(); await pollStatus(false); }
}
async function pollStatus(schedule=true) {
  try {
    const state=await api("status"); csrf=state.csrf_token; busy=state.busy;
    const j=state.job;
    if(j) {
      const progress=j.progress;
      $("job").innerHTML=`<p>${chip(j.command)} ${chip(j.state==="RUNNING" && j.command==="run"?"EXECUTANDO":j.state)} · ${esc(j.session)}</p><p>${esc(j.stage)}${j.error?` · <span class="bad">${esc(j.error)}</span>`:""}</p>${progress?`<p class="muted">Progresso observado no journal: ${progress.unavailable?esc(progress.message):`${progress.recorded} respostas gravadas / ${progress.reserved} chamadas reservadas. Total final depende dos gates do tratamento.`}</p>${(progress.stages||[]).map(s=>chip(`#${s.sequence} ${s.stage||"reservada / em andamento"} · ${s.status||"sem resposta gravada"}`)).join(" ")}`:""}${j.recovery_note?`<details><summary>Interrupção e recuperação</summary><p>${esc(j.recovery_note)}</p></details>`:""}${j.benchmarks?Object.entries(j.benchmarks).map(([k,v])=>`<p class="muted">${esc(k)}: ${esc(v)}</p>`).join(""):""}`;
      if(j.command==="preflight" && j.state==="COMPLETE") { report=j.report; renderReport(); }
      if(j.state!=="RUNNING" && completedJob!==j.id) { completedJob=j.id; await refresh(); }
    } else if(busy) $("job").textContent="Bloqueio persistente sem job disponível: recuperação local necessária. Nenhuma inferência será repetida.";
    controls();
  } catch(e) { error(e); csrf=null; controls(); }
  if(schedule) setTimeout(()=>pollStatus(),2000);
}
$("prepare").addEventListener("click",()=>submit("prepare"));
$("preflight").addEventListener("click",()=>submit("preflight"));
$("benchmarks").addEventListener("click",()=>submit("benchmarks"));
$("execute").addEventListener("click",()=>{
  if(!report?.ready||busy||posting) return;
  confirmationToken=report.confirmation_token;
  $("confirm-details").innerHTML=facts([["Data-alvo",esc(report.calendar.target_session)],["Input SHA256",esc(report.input.sha256.slice(0,12))],["Modelo",esc(report.model.model)],["USD esperado / prudente",`${num(report.estimate.usd_expected)} / ${num(report.estimate.usd_prudent_budget)}`]]);
  $("accept-charges").checked=false; $("submit-confirm").disabled=true;
  $("confirm-dialog").showModal();
});
$("accept-charges").addEventListener("change",()=>$("submit-confirm").disabled=!$("accept-charges").checked);
$("cancel-confirm").addEventListener("click",()=>$("confirm-dialog").close());
$("submit-confirm").addEventListener("click",()=>{
  if(!$("accept-charges").checked||posting||busy||!confirmationToken) return;
  $("confirm-dialog").close();
  const token=confirmationToken; confirmationToken=null;
  submit("run",{confirm:true,confirmation_token:token});
});
controls(); pollStatus();
