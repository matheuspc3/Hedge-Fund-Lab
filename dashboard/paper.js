/* Legacy PETR4/H2: historical consultation only; every request is a GET. */
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
const COLORS = {ai:"#3987e5",buy_and_hold:"#d95926",sma_regime_h2_proposed:"#199e70",bollinger_state_h2_proposed:"#c98500",h2_v6_supervised:"#d55181"};
const DASH = {ai:[],buy_and_hold:[7,4],sma_regime_h2_proposed:[2,3],bollinger_state_h2_proposed:[10,3,2,3],h2_v6_supervised:[12,3]};
const ORDER = ["ai","h2_v6_supervised","buy_and_hold","sma_regime_h2_proposed","bollinger_state_h2_proposed"];
const STATES = {AGUARDANDO_APROVACAO:["Aguardando aprovação","warn"],APROVADA:["Aprovada","buy"],AJUSTADA_CONCENTRACAO:["Aprovada · ajustada por concentração","warn"],BLOQUEADA_VOLATILIDADE:["Bloqueada · volatilidade","sell"],PENDENTE_ABERTURA:["Aguardando abertura oficial","warn"],EXECUTADA:["Execução virtual confirmada","buy"],NAO_EXECUTADA_LIMITE_PRECO:["Não executada · limite de preço","sell"],NAO_EXECUTADA_GAP:["Não executada · gap","sell"],BLOQUEADA_BASE_PRECOS:["Bloqueada · base de preços","sell"],REJEITADA:["Rejeitada","sell"],CANCELADA:["Cancelada","hold"],EXPIRADA:["Expirada","hold"],SEM_ORDEM_NECESSARIA:["Sem ordem necessária","hold"],SEM_DECISAO:["Sem decisão","none"]};
const stateChip = (v) => `<span class="chip sig-${STATES[v]?.[1] || "none"}" title="${esc(v)}">${esc(STATES[v]?.[0] || v)}</span>`;
const LIMITS = {max_buy_price:["Preço máximo de compra (R$)",0.01],min_sell_price:["Preço mínimo de venda (R$)",0.01],max_gap_up:["Gap de alta máximo (%)",0.1],max_gap_down:["Gap de baixa máximo (%)",0.1],max_concentration:["Concentração máxima (%)",1],max_volatility:["Volatilidade máxima (%)",0.1]};
const PRICE_LIMITS = ["max_buy_price","min_sell_price"];
const ROLE = {SUPPORTS_COMPRA:["Suporte à COMPRA","buy"],SUPPORTS_VENDA:["Suporte à VENDA","sell"],CAUTION:["Cautela","warn"],NEUTRAL:["Neutro","hold"]};
let supervisionView = null, wallets = [], latest = null, agentsData = null, records = [], selectedAgent = "TA-01", visible = null, charts = {}, decisionVersion = 0, refreshVersion = 0;
let marketController;

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
const VIEWS = ["acompanhamento","visao","sala","mercado","carteiras","agentes"], LEGACY = {room:"sala",wallets:"carteiras",supervisao:"sala"};
function route() {
  const hash = (typeof location === "undefined" ? "" : location.hash).slice(1);
  const view = VIEWS.includes(hash) ? hash : LEGACY[hash] || "visao";
  document.querySelectorAll("[data-view]").forEach(s => s.hidden = s.id !== view);
  document.querySelectorAll("[data-tab]").forEach(a => a.dataset.tab === view ? a.setAttribute("aria-current","page") : a.removeAttribute("aria-current"));
  if (view === "mercado") loadMarket();
  if (hash === "supervisao") focusSupervision();
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
  const head = `<div class="wallet-head"><h3><span class="swatch" aria-hidden="true"></span>${esc(w.label)}</h3>${w.supervision?.awaiting ? chip("Aguardando aprovação","sig-warn") : w.pending ? chip("Ordem pendente","sig-warn") : ""}</div>`;
  const last = w.trades?.at(-1);
  if (!w.available) return `<article class="card wallet" style="--series:${COLORS[w.key]}">${head}${empty("Sem carteira prospectiva", esc(w.reason))}</article>`;
  const stale = w.mark?.session < latestMark();
  return `<article class="card wallet" style="--series:${COLORS[w.key]}">${head}
    <div class="value">${money(w.equity)}</div>
    <p class="delta ${tone(w.return)}">${signed(w.return, pct)} · ${signed(w.pnl, money)}</p>
    ${facts([["PETR4 investido",money(w.marked_value)],["Caixa",money(w.cash)],["Exposição",pct(w.exposure)],["Custos",money(w.costs)],["Operações",num(w.trades.length)],["Última operação",last ? `${day(last.session)} · ${last.type === "BUY" ? "compra" : "venda"}` : "Nenhuma"],["Drawdown máx.",w.max_drawdown == null ? `${ND} <small>(2+ fechamentos)</small>` : pct(w.max_drawdown)]],"mini")}
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
  if (!d?.consensus) { $("last-decision").innerHTML = `<h2>Última deliberação</h2>${empty("Nenhuma decisão prospectiva registrada", d ? `Sessão ${day(d.session)}: ${esc(d.status)}.` : "Etapa anterior preservada para consulta; nenhuma decisão é criada pela interface.")}<a class="action" href="#sala">Abrir Decisão do dia →</a>`; return; }
  const c = d.consensus, ai = wallets.find(w => w.key === "ai");
  $("last-decision").innerHTML = `<div class="card-head"><h2>Última deliberação</h2>${chip(d.status)}</div>
    ${facts([["Ativo",esc(d.ticker)],["Data de referência",`${day(d.session)} · fechamento`],["Consenso",`${signal(c.consensus_reached ? c.technical_outcome : "SEM CONSENSO")} ${esc(c.signal?.justification)}`],["Risk Manager",signal(d.risk?.verdict)],["Portfolio Manager",`${signal(d.portfolio?.decision)} alvo ${pct(d.portfolio?.target_weight)}`],["Ordem",`${chip(d.order?.label, `sig-${TONE[d.order?.state] || "none"}`)} <small class="muted">${esc(d.order?.detail)}</small>`]])}
    <div class="split"><div class="intent"><small>Sinal futuro · abertura de ${day(d.target_session)}</small><strong>Alvo ${pct(d.portfolio?.target_weight)} em PETR4</strong></div>
    <div class="actual"><small>Posição executada · marcação ${day(ai?.mark?.session)}</small><strong>${pct(ai?.exposure)} PETR4 · ${pct(ai?.composition?.[1]?.weight)} caixa</strong></div></div>
    <a class="action" href="#sala">Abrir Decisão do dia →</a>`;
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
  if (!d) { $("decision").innerHTML = empty("Nenhuma sessão prospectiva registrada", "Nenhuma decisão é criada pela interface Legacy."); return; }
  if (!d.consensus) { $("decision").innerHTML = empty(`Sessão ${day(d.session)} · ${d.status}`, d.status === "MISSED" ? "Nenhuma decisão foi registrada antes da abertura seguinte; posição mantida." : "Input preparado, sem decisão gravada.") + '<div id="supervision-panel"></div>'; renderSupervision(d); return; }
  const risk = d.risk || {}, p = d.portfolio || {}, n = d.committee?.analyst_count || 0;
  const flow = (d.flow || []).map(s=>`<li><small>${esc(s.stage)}</small>${signal(s.result)}<p>${esc(s.detail)}</p>${s.changed === false ? '<span class="tag">Não alterou</span>' : s.changed ? '<span class="tag warn">Alterou</span>' : ""}</li>`).join("");
  $("decision").innerHTML = `<div class="meta">${chip(d.status)} ${chip(d.ticker || "PETR4.SA")} <span>Referência <strong>${day(d.session)}</strong></span><span>Fechamento usado <strong>${money(d.close_used)}</strong></span><span>Abertura-alvo <strong>${day(d.target_session)} ${esc(d.target_open_deadline?.slice(11,16) || "")}</strong></span><span class="muted">${d.replayed_from_journal ? "Replay offline do journal" : "Gerada em"} ${stamp(d.generated_at)}</span></div>
    ${d.failure ? `<p class="callout bad">${esc(d.failure)}</p>` : ""}
    <ol class="flow" aria-label="Fluxo da decisão">${flow}</ol>
    ${quorumCard(d)}
    ${synthesis(d)}
    <div class="pair"><article class="card"><h2>Risk Manager</h2><p>${signal(risk.verdict)} ${chip(risk.risk_source)} ${risk.veto_effect ? chip(`Veto ${risk.veto_effect}`) : ""}</p><p>${esc(risk.analysis)}</p>${table(["Regra","Valor","Limite","Estado"], (risk.rules || []).map(r=>[esc(r.rule),num(r.value),`${esc(r.operator)} ${num(r.limit)}`,chip(r.status, r.status === "PASSOU" ? "sig-buy" : r.status === "DISPAROU" ? "sig-sell" : "")]))}</article>
    <article class="card"><h2>Portfolio Manager</h2><p>${signal(p.decision)} ${chip(p.final_cause)}</p><p>${esc(p.reasoning)}</p>
      <h3>Da recomendação à execução</h3>${facts([["Sinal técnico",signal(d.consensus.technical_outcome)],["Decisão final",signal(p.decision)],["Ordem pretendida",d.intent_weight == null ? "Nenhuma" : `Alvo ${pct(d.intent_weight)} PETR4`],["Ordem pendente",d.pending ? `Sim · abertura ${day(d.pending.target_session)}` : "Não"],["Ordem executada",d.execution ? `${day(d.execution.session)} · ${d.execution.trades.length} operação(ões)` : "Ainda não observada"],["Não executável",d.status === "LATE_NOT_EXECUTABLE" ? "Sim · decisão após a abertura" : "Não"],["Posição no fechamento",pct(p.observed_weight)]])}
      <p class="muted small">A posição-alvo é uma recomendação para a próxima abertura. A composição financeira atual está em Carteiras.</p></article></div>
    <div id="supervision-panel"></div>
    <details class="card"><summary>Comitê técnico · ${n} analistas · votos individuais</summary><div class="analysts">${Array.from({length:n}, (_,i) => analystCard(i + 1, d.analysts.filter(a => Number(a.analyst_id) === i + 1))).join("")}</div></details>`;
  renderSupervision(d);
  focusSupervision();
}

/* ── Supervisão Humana ─────────────────────────────────────── */
function limitText(key, value) {
  return `${esc(LIMITS[key]?.[0].replace(/ \(.*\)/, "") || key)} ${PRICE_LIMITS.includes(key) ? money(value) : pct(value)}`;
}
function focusSupervision() {
  const box = $("supervision-panel");
  if (location.hash === "#supervisao" && box) { box.tabIndex=-1; box.focus(); box.scrollIntoView({block:"start"}); }
}
function renderSupervision(d) {
  const box = $("supervision-panel");
  if (!box) return;
  const s = supervisionView, intro = '<p class="muted small">Carteira H2 v6 Supervisionada · registro histórico somente consulta. Autorizações, reservas e pendências são preservadas; esta página não reconcilia nem encerra intenções.</p>';
  const head = (state) => `<div class="card-head"><h2>Supervisão Humana</h2>${state ? stateChip(state) : ""}</div>${intro}`;
  if (!s?.initialized) { box.innerHTML = `<article class="card supervision">${head()}${empty("Carteira supervisionada não inicializada", esc(s?.reason || "Consulte os registros."))}</article>`; return; }
  const p = s.selected;
  if (!p || p.decision_session !== d.session) { box.innerHTML = `<article class="card supervision">${head()}${empty("Sem proposta supervisionada para esta sessão", "Nenhuma proposta é criada ou sincronizada pela interface Legacy.")}</article>`; return; }
  const a = p.approval, o = p.outcome;
  const limits = a ? (Object.keys(a.limits || {}).length ? Object.entries(a.limits).map(([k,v]) => chip(limitText(k, v))).join(" ") : "Nenhum limite adicional") : "—";
  const waiting = {AGUARDANDO_APROVACAO:"Decisão humana até o prazo", APROVADA:"Abertura oficial e verificação dos limites", AJUSTADA_CONCENTRACAO:"Abertura oficial e verificação dos limites", PENDENTE_ABERTURA:"Reconciliação com a abertura oficial, disponível após o fechamento"}[p.order_state] || "Nenhuma";
  const c = d.consensus || {};
  box.innerHTML = `<article class="card supervision">${head(p.order_state)}
    <div class="pair">${facts([["Ativo",esc(d.ticker)],["Data de referência",day(p.decision_session)],["Decisão dos agentes",`${signal(d.portfolio?.decision)} <small class="muted">${esc(p.final_cause)}</small>`],["Consenso",`${signal(c.consensus_reached ? c.technical_outcome : "SEM CONSENSO")} ${esc(c.signal?.justification || "")}`],["Risk Manager",signal(d.risk?.verdict)],["Portfolio Manager",signal(d.portfolio?.decision)]])}
    ${facts([["Posição supervisionada no fechamento",pct(p.weight_at_close)],["Carteira supervisionada agora",`${pct(s.position.weight)} PETR4 · ${money(s.position.equity)}`],["Posição-alvo recomendada",p.recommended_target == null ? "Nenhuma ordem" : `${pct(p.recommended_target)} PETR4`],["Prazo de validade",p.deadline ? `${stamp(p.deadline)}` : ND],["Fechamento bruto oficial",money(p.raw_close)]])}</div>
    <h3>Da recomendação à ordem supervisionada</h3>
    <ol class="ladder">
      <li><small>Recomendação original</small><div>${signal(p.direction && !["VETO"].includes(p.direction) ? p.direction : d.portfolio?.decision)} ${esc(p.reason)}</div></li>
      <li><small>Decisão do operador</small><div>${a ? `${chip(a.action === "APPROVE" ? "Aprovou" : "Rejeitou", a.action === "APPROVE" ? "sig-buy" : "sig-sell")} ${stamp(a.created_at)}${p.cancel ? ` · ${chip("Cancelou","sig-hold")} ${stamp(p.cancel.created_at)}` : ""}` : "Nenhuma ação registrada"}</div></li>
      <li><small>Limites aplicados</small><div>${limits}${a?.effect ? ` <span class="muted">${esc(a.effect.reason)}</span>` : ""}</div></li>
      <li><small>Condições pendentes</small><div>${esc(waiting)}</div></li>
      <li><small>Status da ordem</small><div>${stateChip(p.order_state)}</div></li>
      <li><small>Resultado da reconciliação</small><div>${o ? `${esc(o.reason)}${o.prices ? `<br/><span class="muted small">Abertura bruta ${money(o.prices.raw_open)} (${esc(o.prices.raw_source)}) · ajustada ${money(o.prices.adjusted_open)} · gap bruto ${pct(o.prices.raw_gap)}</span>` : ""}` : "Ainda não reconciliada"}</div></li>
    </ol>
    <p class="muted small">${s.audit.ok ? `Cadeia de auditoria íntegra · ${s.audit.events} eventos` : `<span class="bad">Auditoria com divergências: ${esc(s.audit.errors.join("; "))}</span>`}</p></article>`;
}
function openingBand(band) {
  const lo = band.lower > 0 ? money(band.lower) : "Sem piso adicional", hi = band.upper == null ? "Sem teto adicional" : money(band.upper);
  return `<div class="opening-band ${band.empty ? "blocked" : ""}" role="img" aria-label="${esc(band.empty ? "Faixa vazia, limites contraditórios" : `Faixa inclusiva: ${lo} a ${hi}`)}"><span>${band.empty ? "Nenhum preço permitido" : "Faixa bruta permitida · extremos inclusivos"}</span><div class="band-line"></div><div class="band-ends"><strong>${lo}</strong><strong>${hi}</strong></div></div>`;
}
async function loadMarket() {
  marketController?.abort(); marketController = new AbortController();
  const controller = marketController;
  $("market-content").innerHTML = '<p class="state">Consultando registros locais…</p>';
  try {
    const m = await api("market", {signal:controller.signal});
    if (controller.signal.aborted) return;
    const c = m.official_close || {}, q = m.intraday || {}, i = m.indicators || {};
    const classification = {realtime_verified:"Tempo real comprovado",delayed:"Atrasada",official_close:"Fechamento oficial",unknown:"Desconhecida"};
    $("market-content").innerHTML = `<div class="market-grid"><article class="card"><div class="card-head"><h2>${esc(m.ticker)} · fechamento de referência</h2>${chip("FECHAMENTO OFICIAL","sig-hold")}</div><p class="market-price">${money(c.price)}</p>${facts([["Sessão do fechamento",day(c.session)],["Procedência",esc(c.source)],["Coleta registrada",stamp(c.timestamp)],["Próxima abertura prevista",stamp(m.session.expected_open)],["Próxima sessão B3",day(m.session.next_session)],["Sessão pelo relógio",chip(m.session.state,"sig-warn")]])}<p class="muted small">${esc(c.timestamp_basis || m.data_issue)}</p><p class="muted small">${esc(m.session.basis)}</p>${c.stale ? '<p class="warn">Fechamento local desatualizado para a última sessão encerrada.</p>' : ""}</article>
    <article class="card"><div class="card-head"><h2>Cotação intradiária</h2>${chip(classification[q.classification],"sig-warn")}</div>${q.price == null ? empty("Cotação intradiária indisponível","O fechamento histórico ao lado não é uma cotação em tempo real.") : `<p class="market-price">${money(q.price)}</p>${facts([["Timestamp do provider",stamp(q.timestamp)],["Variação contra fechamento",signed(q.change_vs_close,pct)]])}`}${facts([["Fonte",esc(q.source)],["Atualização",esc(classification[q.classification])],["Consulta local",stamp(m.as_of)]])}${q.stale ? '<p class="warn">Informação desatualizada.</p>' : ""}<p class="muted">${esc(m.refresh)}</p><p class="muted small">Uma cotação atrasada não identifica o preço oficial do leilão nem confirma execução.</p></article></div>
    <article class="card"><div class="card-head"><h2>Condições aprovadas</h2>${chip("SOMENTE INFORMATIVO","sig-warn")}</div>${m.approved_conditions.length ? m.approved_conditions.map(p=>`<h3>${esc(p.direction)} · abertura-alvo ${day(p.target_session)} ${chip(p.state,p.state === "Fora do limite" ? "sig-sell" : "sig-warn")}</h3>${openingBand(p.band)}${table(["Limite aprovado","Valor","Cotação observada"],p.band.checks.map(c=>[esc(LIMITS[c.key]?.[0]),PRICE_LIMITS.includes(c.key) ? money(c.limit) : pct(c.limit),c.passed === true ? "Dentro do limite" : c.passed === false ? "Fora do limite" : "Dados insuficientes"]))}<p class="muted small">${esc(p.note)}</p>`).join("") : empty("Nenhuma condição aprovada ativa","Não há condição aprovada ativa nos registros consultados; ações estão indisponíveis no Legacy.")}<p class="muted">${esc(m.execution_authority)}</p>${m.audit && !m.audit.ok ? '<p class="bad">Auditoria com divergências; não use estes registros para decidir.</p>' : ""}</article>
    <article class="card"><div class="card-head"><h2>Indicadores do fechamento</h2>${chip("HISTÓRICO · BASE AJUSTADA","sig-hold")}</div>${facts([["Sessão de referência",day(i.session)],["SMA50 · R$ ajustados",money(i.sma50)],["SMA200 · R$ ajustados",money(i.sma200)],["RSI14 · pontos de 0 a 100",num(i.rsi,2)],["MACD 12/26 · R$ ajustados",num(i.macd,4)],["Sinal MACD9 · R$ ajustados",num(i.macd_signal,4)],["Volatilidade anualizada gravada",pct(i.volatility)]])}<p class="muted small provenance">${esc(i.source || m.data_issue)}</p><p class="muted small">Indicadores derivados da série congelada; não são recalculados com cotações intradiárias.</p></article>`;
  } catch(e) { if (e.name !== "AbortError") $("market-content").innerHTML = empty("Mercado indisponível",esc(e.message)); }
}
function supervisionHistory(w) {
  const s = supervisionView;
  if (w.key !== "h2_v6_supervised" || !s?.initialized) return "";
  const last = s.timeline.filter(t => t.difference != null).at(-1), k = w.supervision || {};
  return `<article class="card"><div class="card-head"><h2>Supervisão humana · histórico</h2><small class="muted">Início ${day(s.inception)} · criada em ${stamp(s.initialized_at)}</small></div>
    ${facts([["Aguardando aprovação",num(k.awaiting)],["Aprovadas",num(k.approved)],["Rejeitadas",num(k.rejected)],["Não executadas por limite ou bloqueio",num(k.not_executed)],["Execuções virtuais",num(k.executed)],["Diferença atual vs H2 original",last ? `${signed(last.difference, money)} em ${day(last.session)}` : ND]],"wide")}
    <h3>Decisões supervisionadas</h3>${table(["Sessão","Recomendação","Ação humana","Limites","Estado","Motivo"], s.proposals.slice().reverse().map(p => [day(p.decision_session),signal(p.direction || null),p.approval ? (p.approval.action === "APPROVE" ? "Aprovou" : "Rejeitou") + (p.cancel ? " · cancelou" : "") : "—",p.approval && Object.keys(p.approval.limits || {}).length ? Object.entries(p.approval.limits).map(([k,v]) => chip(limitText(k, v))).join(" ") : "—",stateChip(p.order_state),`<span class="wrap">${esc((p.outcome || {}).reason || p.reason)}</span>`]))}
    <h3>Linha do tempo: intervenção × patrimônio</h3>${table(["Fechamento","H2 original","Supervisionada","Diferença","Proposta da sessão"], s.timeline.slice().reverse().map(t => [day(t.session),money(t.original_equity),money(t.supervised_equity),t.difference == null ? ND : `<span class="${tone(t.difference)}">${signed(t.difference, money)}</span>`,t.order_state ? stateChip(t.order_state) : "—"]))}
    <p class="muted small">Diferença descritiva entre duas carteiras paralelas com mesmo início, capital, custos e preços observados. Com poucas sessões e julgamento humano não cego, ela não demonstra efeito causal da supervisão.</p></article>`;
}
function renderHistory() {
  $("history").innerHTML = records.length ? table(["Sessão","Estado","COMPRA / VENDA / MANTER","Sinal técnico","Decisão final","Alvo",""], records.slice().reverse().map(r=>[day(r.session),chip(r.status),r.vote_counts ? `${r.vote_counts.COMPRA ?? 0} / ${r.vote_counts.VENDA ?? 0} / ${r.vote_counts.MANTER ?? 0}` : ND,signal(r.technical_outcome),signal(r.final_decision),pct(r.target_weight),r.has_decision ? `<button data-session="${esc(r.session)}">Abrir</button>` : ""])) : empty("Nenhuma deliberação registrada");
}
async function loadDecision(session="") {
  const version = ++decisionVersion;
  const query = session ? `?session=${encodeURIComponent(session)}` : "";
  try {
    const [d, s] = await Promise.all([api(`decision${query}`), api(`supervision${query}`)]);
    if (version === decisionVersion) { supervisionView = s; renderDecision(d); renderComposition(); }
  } catch(e) { if (version === decisionVersion) error(e); }
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
    ${facts([["Patrimônio total",money(w.equity)],["Capital inicial",money(w.initial_capital)],["Exposição",pct(w.exposure)],["Custos acumulados",money(w.costs)],["Operações executadas",num(w.trades.length)],["Drawdown máximo",w.max_drawdown == null ? `${ND} · requer 2+ fechamentos` : pct(w.max_drawdown)],["Ordem pendente",w.pending ? `${day(w.pending.target_session)} · alvo ${pct(w.pending.target_weight)}` : "Nenhuma"],["Última decisão",w.last_decision ? `${day(w.last_decision.session)} · ${esc(STATES[w.last_decision.status]?.[0] || w.last_decision.status)} · alvo ${pct(w.last_decision.target_weight)}` : w.key === "buy_and_hold" ? "Compra única na primeira abertura após a inicialização" : "Sem decisão"],["Proventos","Ainda não contabilizados"]],"wide")}</article>`;
  $("trades").innerHTML = supervisionHistory(w) + `<article class="card"><h2>Operações executadas · ${esc(w.label)}</h2>${w.trades.length ? table(["Decisão","Execução","Ativo","Lado","Preço","Quantidade","Custo","Patrimônio no fechamento"], w.trades.map(t=>[t.decision_session ? day(t.decision_session) : w.key === "buy_and_hold" ? "Regra B&H" : ND,day(t.session),esc(t.asset),signal(t.type === "BUY" ? "COMPRA" : t.type === "SELL" ? "VENDA" : t.type),money(t.price),num(t.quantity),money(t.cost),money(t.equity_after)])) : empty("Nenhuma operação executada", "Ordens pendentes não são patrimônio investido.")}</article>`;
}
function renderWallets(data) {
  wallets = (data?.wallets || []).slice().sort((a, b) => ORDER.indexOf(a.key) - ORDER.indexOf(b.key));
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
    const [history, data, agents, last, status] = await Promise.all([api("history"), api("portfolios"), api("agents"), api("decision"), api("status")]);
    if (version !== refreshVersion) return;
    records = history || []; latest = last; agentsData = agents;
    const j=status?.job;
    $("job").innerHTML=j ? `<p>${chip(j.command)} ${chip(j.state)} · ${esc(j.session)}</p><p>${esc(j.stage)}${j.error ? ' · '+esc(j.error) : ''}</p><p class="muted">${esc(j.recovery_note || 'Registro histórico; nenhuma retomada pela interface.')}</p>` : empty("Nenhum job disponível para consulta", "Isso não comprova ausência de pendências financeiras.");
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
$("market-refresh").addEventListener("click", loadMarket);
if (typeof window !== "undefined") window.addEventListener("hashchange", route);
route(); simulate(); refresh();
