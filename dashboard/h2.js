/* H2 v6 dashboard — thin client. Every number arrives computed from the backend;
   this file only formats, draws and navigates. Demo and real payloads are never
   merged: a source switch replaces the whole state. */

const LLM = ["L01", "L02", "L03"];
const BENCH = ["buy_and_hold", "sma_regime_h2_proposed", "bollinger_state_h2_proposed"];
const css = getComputedStyle(document.documentElement);
const color = (id) => css.getPropertyValue(`--s-${id}`).trim();
const INK = { text2: "#c3c2b7", muted: "#898781", grid: "#2c2c2a", axis: "#383835", surface: "#1a1a19" };

const state = {
  tab: "overview", source: "provisional", status: null, data: null, focus: "L01", auditRun: "L01", detail: null, trace: null, session: null,
  // post-Validation analysis: undefined = not requested, "loading", null = unavailable
  analysis: undefined, runsOn: new Set(LLM), showBoll: true, showSma: true, dRun: "L01", decision: null, pending: null, bollEvent: null, cycle: null, agentRun: "L01",
};
const charts = {};

// ── formatting ──────────────────────────────────────────────────────────────
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const num = (v, d = 2) => (v == null || Number.isNaN(v) ? "N/A" : v.toLocaleString("pt-BR", { minimumFractionDigits: d, maximumFractionDigits: d }));
const pct = (v, d = 2) => (v == null ? "N/A" : `${num(v * 100, d)}%`);
const brl = (v) => (v == null ? "N/A" : v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" }));
const signed = (v, f = num) => (v == null ? "N/A" : `${v > 0 ? "+" : ""}${f(v)}`);
const tone = (v) => (v == null ? "" : v > 0 ? "up" : v < 0 ? "down" : "");
const short = (h) => (h ? `${h.slice(0, 12)}…` : "—");
const sw = (id) => `<span class="swatch" style="background:${color(id)}"></span>`;
const card = (title, body, extra = "") => `<div class="card" ${extra}>${title ? `<h3>${esc(title)}</h3>` : ""}${body}</div>`;
const kpi = (label, value, sub = "", cls = "") => `<div class="card kpi"><div class="label">${esc(label)}</div><div class="value ${cls}">${value}</div><div class="sub">${sub}</div></div>`;
const empty = (text) => `<div class="empty">${esc(text)}</div>`;
function chip(text) {
  const t = String(text);
  const cls = /BLOQUEADO|INTERROMPIDA|INVALID|NOT_ESTIMABLE|ERRO|DISPAROU|EFETIVO/.test(t) ? "bad"
    : /EXECUÇÃO|PENDENTE|PENDING|STARTED|AUSENTE|NÃO APROVADO|NOT APPROVED|NÃO RATIFICADA|VETADO|SEM EFEITO/.test(t) ? "warn"
    : /COMPLETE|SELADA|CONCLU|REUSED|VALID|PRESENTE|PASSOU|APLICADA|APROVADO|SEGUIU/.test(t) ? "good"
    : /PROVIS/.test(t) ? "serious" : "";
  const icon = { bad: "✕", warn: "◐", good: "✓", serious: "!" }[cls] || "•";
  return `<span class="chip ${cls}">${icon} ${esc(t)}</span>`;
}
function table(cols, rows, opts = {}) {
  const head = cols.map((c) => `<th class="${c.n ? "n" : ""}">${esc(c.label)}</th>`).join("");
  const body = rows.map((r, i) => `<tr class="${opts.click ? "click" : ""} ${opts.selected?.(r) ? "sel" : ""}" ${opts.click ? `data-i="${i}"` : ""}>${cols.map((c) => `<td class="${c.n ? "n" : ""}">${c.render(r)}</td>`).join("")}</tr>`).join("");
  return `<div class="scroll"><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
}

// ── data ────────────────────────────────────────────────────────────────────
// Each request owns a slot: a newer request in the same slot, or a source switch,
// aborts the older one, and an aborted or stale answer is never applied.
const STALE = Symbol("stale");
const inflight = new Map();
async function request(slot, path) {
  inflight.get(slot)?.abort();
  const ctl = new AbortController(), source = state.source;
  inflight.set(slot, ctl);
  try {
    const r = await fetch(path, { cache: "no-store", signal: ctl.signal });
    const body = r.ok ? await r.json() : null;
    return ctl.signal.aborted || source !== state.source ? STALE : body;
  } catch (e) {
    return ctl.signal.aborted || source !== state.source ? STALE : null;
  } finally {
    if (inflight.get(slot) === ctl) inflight.delete(slot);
  }
}
const abort = (slot) => inflight.get(slot)?.abort();
async function load() {
  const source = state.source;
  state.loading = true;
  const [status, data] = await Promise.all([request("status", "/api/h2/status"), request("validation", `/api/h2/validation?source=${source}`)]);
  if (status === STALE || data === STALE) return; // a newer switch won
  Object.assign(state, { status, data, loading: false });
  render();
  const running = data?.state === "EM EXECUÇÃO";
  document.getElementById("live-dot").classList.toggle("on", running);
  document.getElementById("live-text").textContent = running ? "ao vivo · 10 s" : `atualizado ${new Date().toLocaleTimeString("pt-BR")}`;
  clearTimeout(state.timer);
  if (running) state.timer = setTimeout(load, 10000);
}
function setSource(source) {
  inflight.forEach((c) => c.abort());
  clearTimeout(state.timer);
  history.replaceState(null, "", `#${source}/${state.tab}`);
  document.querySelectorAll("[data-source]").forEach((x) => x.setAttribute("aria-pressed", x.dataset.source === source));
  // never mix sources: drop everything the previous source produced before rendering
  Object.assign(state, { source, status: null, data: null, detail: null, trace: null, session: null, analysis: undefined, decision: null, pending: null, bollEvent: null, cycle: null });
  render();
  return load().then(() => {
    if (source !== state.source || !state.data) return;
    if (state.tab === "audit") loadDetail();
    if (["decisions", "compare", "agents"].includes(state.tab) && !state.data.synthetic) loadAnalysis();
    else if (state.data.synthetic) { state.analysis = null; render(); }
  });
}
async function loadAnalysis() {
  if (state.analysis !== undefined) return;
  state.analysis = "loading";
  render();
  const a = await request("analysis", `/api/h2/analysis?source=${state.source}`);
  if (a === STALE) return;
  state.analysis = a;
  render();
}
async function loadDecision(run, session) {
  Object.assign(state, { dRun: run, bollEvent: null, pending: session });
  renderDecisionPanel();
  const d = await request("decision", `/api/h2/decision?source=${state.source}&run=${run}&session=${session}`);
  if (d === STALE) return; // a newer click or source won
  Object.assign(state, { decision: d || { missing: session, run }, pending: null });
  renderDecisionPanel();
  renderCycles();
  updateBands();
}
async function loadDetail() {
  abort("trace"); // a trace belongs to the previous run
  Object.assign(state, { detail: null, trace: null, session: null });
  const pending = request("detail", `/api/h2/run?source=${state.source}&run=${state.auditRun}`);
  renderAudit();
  const d = await pending;
  if (d === STALE) return;
  state.detail = d;
  renderAudit();
}
async function loadTrace(session) {
  state.session = session;
  const t = await request("trace", `/api/h2/trace?source=${state.source}&run=${state.auditRun}&session=${session}`);
  if (t === STALE) return;
  state.trace = t;
  renderAudit();
}

// ── charts ──────────────────────────────────────────────────────────────────
function lineChart(id, dates, series, { percent = false, money = false, returns = null } = {}) {
  charts[id]?.destroy();
  const el = document.getElementById(id);
  if (!el) return;
  const fmt = (v) => (percent ? pct(v, 1) : money ? brl(v) : num(v));
  charts[id] = new Chart(el, {
    type: "line",
    data: {
      labels: dates,
      datasets: series.map((s) => ({
        id: s.id, label: s.label, data: s.values, borderColor: color(s.id), backgroundColor: color(s.id),
        borderWidth: 2, borderDash: BENCH.includes(s.id) ? [6, 4] : [], pointRadius: 0, pointHoverRadius: 4,
        pointHoverBorderColor: INK.surface, pointHoverBorderWidth: 2, tension: 0,
      })),
    },
    options: {
      responsive: true, maintainAspectRatio: false, animation: { duration: 400 },
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: { backgroundColor: "#222220", borderColor: "rgba(255,255,255,.12)", borderWidth: 1, titleColor: "#fff", bodyColor: INK.text2, padding: 10, callbacks: { label: (c) => ` ${c.dataset.label}: ${fmt(c.parsed.y)}${returns?.[c.dataset.id] ? ` · acumulado ${signed(returns[c.dataset.id][c.dataIndex], (v) => pct(v))}` : ""}` } },
      },
      scales: {
        x: { ticks: { color: INK.muted, maxTicksLimit: 8, maxRotation: 0 }, grid: { display: false }, border: { color: INK.axis } },
        y: { ticks: { color: INK.muted, callback: fmt }, grid: { color: INK.grid }, border: { display: false } },
      },
    },
  });
}
function barChart(id, rows) {
  charts[id]?.destroy();
  const el = document.getElementById(id);
  if (!el) return;
  charts[id] = new Chart(el, {
    type: "bar",
    data: { labels: rows.map((r) => r.label), datasets: [{ data: rows.map((r) => r.value), backgroundColor: rows.map((r) => color(r.id)), borderRadius: 4, borderSkipped: "start", barThickness: 18 }] },
    options: {
      indexAxis: "y", responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: (c) => ` Sharpe: ${num(c.parsed.x, 3)}` } } },
      scales: { x: { ticks: { color: INK.muted }, grid: { color: INK.grid }, border: { color: INK.axis } }, y: { ticks: { color: INK.text2 }, grid: { display: false } } },
    },
  });
}
const legend = (ids) => `<div class="legend">${ids.map((id) => `<span><i class="${BENCH.includes(id) ? "dash" : "solid"}" style="border-color:${color(id)}"></i>${esc(label(id))}</span>`).join("")}</div>`;
const label = (id) => state.data?.participants.find((p) => p.id === id)?.label || id;
const part = (id) => state.data?.participants.find((p) => p.id === id);
const curveSeries = (ids, key = "equity") => ids.filter((id) => state.data.curves?.[key][id]).map((id) => ({ id, label: label(id), values: state.data.curves[key][id] }));

// ── sections ────────────────────────────────────────────────────────────────
function renderBanner() {
  const d = state.data;
  const el = document.getElementById("banner");
  if (!d) return (el.innerHTML = state.loading ? `<div class="banner info">Carregando fonte ${esc(state.source)}…</div>` : `<div class="banner info">API indisponível — inicie <code>python dashboard/server.py</code>.</div>`);
  if (d.synthetic) return (el.innerHTML = `<div class="banner demo">▨ ${esc(d.banner)} — valores fictícios gerados para prévia visual; não são resultados do experimento.</div>`);
  if (d.source === "provisional") return (el.innerHTML = `<div class="banner prov">! VALIDATION OA-1 — NÃO RATIFICADA ACADEMICAMENTE · execução provisória autorizada somente pelo autor; análise exploratória, não confirmatória. Estado: ${esc(d.state)}</div>`);
  el.innerHTML = `<div class="banner info">Validation oficial — exige aprovação de autor, coautor e orientador, System Freeze e consentimento próprio. Estado: ${esc(d.state)}</div>`;
}

function renderOverview() {
  const d = state.data, s = state.status;
  const el = document.getElementById("tab-overview");
  if (!d) return (el.innerHTML = "");
  const p = part(state.focus), bh = part("buy_and_hold"), m = p?.metrics;
  const picks = LLM.map((id) => `<button class="pick" data-focus="${id}" aria-pressed="${id === state.focus}">${sw(id)}${esc(label(id))}</button>`).join("");
  const kpis = m
    ? [
        kpi("Patrimônio inicial", brl(m.initial)),
        kpi("Patrimônio final", brl(m.final), `B&H: ${brl(bh?.metrics?.final)}`),
        kpi("Retorno líquido", pct(m.net_return), `B&H: ${pct(bh?.metrics?.net_return)}`, tone(m.net_return)),
        kpi("Sharpe", num(m.sharpe, 3), `ΔSharpe vs B&H: ${signed(m.delta_sharpe, (v) => num(v, 3))}`, tone(m.delta_sharpe)),
        kpi("Sortino", num(m.sortino, 3)),
        kpi("Max Drawdown", pct(m.max_drawdown), "", "down"),
        kpi("Turnover", `${num(m.turnover, 2)}×`, `${m.trades} ordens · custos ${brl(m.total_cost)}`),
      ].join("")
    : empty(`Run ${state.focus}: ${p?.state || "sem dados"} — métricas aparecem quando o run é selado.`);
  const st = d.statistics;
  const agg = st
    ? [kpi("Sharpe médio R=3", num(st.mean, 3), `min ${num(st.min, 3)} · max ${num(st.max, 3)}`), kpi("ΔSharpe (média − B&H)", signed(st.delta, (v) => num(v, 3)), `B&H ${num(st.sharpe_buy_and_hold, 3)} · ${esc(st.inference || "")}`, tone(st.delta))].join("")
    : kpi("Estatística R=3", "Pendente", "summary.json é gravado ao concluir os três runs");
  const id = s?.identity;
  el.innerHTML = `
    <div class="row">${picks}</div>
    <div class="grid g-kpi">${kpis}</div>
    <div class="grid g-kpi" style="margin-top:16px">${agg}</div>
    <div class="grid g-3" style="margin-top:16px">
      ${card("Curva de patrimônio vs Buy & Hold", d.curves ? `${legend([...LLM, "buy_and_hold"])}<div class="chart"><canvas id="c-overview"></canvas></div>` : empty("Nenhum run selado nesta fonte."))}
      ${card("Status e identidade científica", id ? `<dl>
        <dt>Fonte</dt><dd>${chip(d.state)}</dd>
        <dt>Acadêmico</dt><dd>${chip(id.state)}</dd>
        <dt>Manifesto</dt><dd class="mono" title="${esc(id.manifest_sha256)}">${short(id.manifest_sha256)}</dd>
        <dt>Tratamento</dt><dd class="mono" title="${esc(id.participant_sha256)}">${short(id.participant_sha256)}</dd>
        <dt>Modelo</dt><dd>${esc(id.model.model)} · T=${id.model.temperature} · thinking ${esc(id.model.thinking_level)}</dd>
        <dt>Janela</dt><dd>${esc(id.windows.VALIDATION.decision_start)} → ${esc(id.windows.VALIDATION.decision_end)}</dd>
        <dt>R / agregação</dt><dd>${id.R} · média aritmética dos Sharpes</dd>
        <dt>CAL-B4</dt><dd>${esc(id.cal_b4_status)}</dd>
        <dt>Final Test</dt><dd>${chip("BLOQUEADO")}</dd></dl>` : "")}
    </div>`;
  if (d.curves) lineChart("c-overview", d.curves.dates, curveSeries([...LLM, "buy_and_hold"]), { money: true, returns: d.curves.return });
}

function renderExperiments() {
  const d = state.data, s = state.status;
  const el = document.getElementById("tab-experiments");
  if (!d || !s) return (el.innerHTML = "");
  const prog = d.progress || {};
  const rows = LLM.map((id) => ({ id, p: part(id), g: prog[id] }));
  const runTable = table(
    [
      { label: "Run", render: (r) => `${sw(r.id)} ${esc(r.p.label)}` },
      { label: "Estado", render: (r) => chip(r.p.state) },
      { label: "Sessões", render: (r) => (r.g ? `<div class="progress" title="${r.g.sessions_started}/${r.g.sessions_total}"><div style="width:${(100 * r.g.sessions_started) / r.g.sessions_total}%"></div></div><span class="mono">${r.g.sessions_started}/${r.g.sessions_total}</span>` : "—") },
      { label: "Última sessão", render: (r) => esc(r.g?.last_session || "—") },
      { label: "Chamadas", n: 1, render: (r) => (r.g ? `${r.g.calls_recorded}/${r.g.calls_reserved}` : "—") },
      { label: "Tentativas HTTP", n: 1, render: (r) => r.g?.http_attempts ?? "—" },
      { label: "Retries", n: 1, render: (r) => r.g?.retries ?? "—" },
      { label: "Erros transporte", n: 1, render: (r) => r.g?.transport_errors ?? "—" },
      { label: "Registros com erro", n: 1, render: (r) => (r.g?.error_records ? `<span class="na">${r.g.error_records}</span>` : r.g ? 0 : "—") },
      { label: "Em voo", n: 1, render: (r) => r.g?.in_flight ?? "—" },
    ],
    rows,
  );
  const bench = table(
    [{ label: "Benchmark", render: (r) => `${sw(r.id)} ${esc(r.label)}` }, { label: "Estado", render: (r) => chip(r.state) }, { label: "Run ID", render: (r) => `<span class="mono">${esc(r.run_id || "—")}</span>` }],
    BENCH.map(part),
  );
  const g = s.governance, a = g.author_authorization;
  const disp = d.dispositions.reduce((acc, x) => ((acc[x.state] = (acc[x.state] || 0) + 1), acc), {});
  el.innerHTML = `
    <h2>Validation · R=3</h2>
    ${card("Runs L01 / L02 / L03", runTable)}
    <div class="grid g-2" style="margin-top:16px">
      ${card("Benchmarks determinísticos", bench)}
      ${card("Autorização e execução", `<dl>
        <dt>Aprovação acadêmica</dt><dd>${chip(g.academic)}</dd>
        <dt>Amendment OA-1</dt><dd>${g.amendment.present ? `<span class="mono">${short(g.amendment.sha256)}</span> · aceite manual exigido` : chip("AUSENTE")}</dd>
        <dt>Autorização do autor</dt><dd>${a ? `${chip("PRESENTE")} ${esc(a.signatory)} · ${esc(a.recorded_at)}${a.binds_current_amendment ? "" : ` ${chip("INVALID — amendment divergente")}`}<br><span class="mono">${short(a.sha256)}</span> · ${esc(a.note)}` : chip("AUSENTE — aguardando autor")}</dd>
        <dt>Validation provisória</dt><dd>${chip(s.phases.VALIDATION.provisional)}</dd>
        <dt>Validation oficial</dt><dd>${chip(s.phases.VALIDATION.official)}</dd>
        <dt>Checkpoint provisório</dt><dd>${g.provisional_checkpoint_sha256 ? `<span class="mono">${short(g.provisional_checkpoint_sha256)}</span>` : "—"}</dd>
        <dt>Final Test</dt><dd>${chip("BLOQUEADO")} <span style="color:var(--muted)">${esc(s.phases.FINAL_TEST)}</span></dd></dl>`)}
    </div>
    <div class="grid g-2" style="margin-top:16px">
      ${card("Journal e selos", d.root_files.length ? table([{ label: "Arquivo", render: (r) => esc(r.name) }, { label: "SHA256", render: (r) => `<span class="mono" title="${esc(r.sha256)}">${short(r.sha256)}</span>` }], d.root_files) : empty(d.synthetic ? "Demonstração não possui selos." : "Nenhum selo de fase ainda."))}
      ${card("Disposições de custo (24)", Object.keys(disp).length ? Object.entries(disp).map(([k, v]) => `<div class="row">${chip(k)} <b>${v}</b></div>`).join("") : empty("Sem disposições registradas."))}
    </div>`;
}

function renderCompare() {
  const d = state.data;
  const el = document.getElementById("tab-compare");
  if (!d) return (el.innerHTML = "");
  const ids = [...LLM, ...BENCH];
  const metricTable = table(
    [
      { label: "Participante", render: (r) => `${sw(r.id)} ${esc(r.label)}` },
      { label: "Retorno líquido", n: 1, render: (r) => `<span class="${tone(r.metrics?.net_return)}">${pct(r.metrics?.net_return)}</span>` },
      { label: "Retorno anualizado", n: 1, render: (r) => pct(r.metrics?.annualized_return) },
      { label: "Volatilidade", n: 1, render: (r) => pct(r.metrics?.volatility) },
      { label: "Sharpe", n: 1, render: (r) => num(r.metrics?.sharpe, 3) },
      { label: "ΔSharpe vs B&H", n: 1, render: (r) => `<span class="${tone(r.metrics?.delta_sharpe)}">${signed(r.metrics?.delta_sharpe, (v) => num(v, 3))}</span>` },
      { label: "Sortino", n: 1, render: (r) => num(r.metrics?.sortino, 3) },
      { label: "Max DD", n: 1, render: (r) => pct(r.metrics?.max_drawdown) },
      { label: "Turnover", n: 1, render: (r) => (r.metrics ? `${num(r.metrics.turnover)}×` : "N/A") },
      { label: "Ordens", n: 1, render: (r) => r.metrics?.trades ?? "N/A" },
      { label: "Custos", n: 1, render: (r) => brl(r.metrics?.total_cost) },
    ],
    ids.map(part),
  );
  const st = d.statistics;
  const runs = st ? `<dl><dt>Sharpe L01 / L02 / L03</dt><dd>${st.sharpe_individual.map((v) => num(v, 3)).join(" · ")}</dd><dt>Média · DP entre runs</dt><dd>${num(st.mean, 3)} · ${num(st.sd_between_runs_ddof1, 3)}</dd><dt>Δ individual</dt><dd>${st.delta_individual.map((v) => signed(v, (x) => num(x, 3))).join(" · ")}</dd><dt>Δ (média − B&H)</dt><dd class="${tone(st.delta)}">${signed(st.delta, (v) => num(v, 3))}</dd><dt>Inferência</dt><dd>${esc(st.inference || "")} · contrastes confirmatórios: ${st.confirmatory_contrasts ?? 0}</dd><dt>Degenerado</dt><dd>${st.sharpe_degenerate ? chip("SIM") : "não"}</dd></dl>` : empty("Comparação R=3 disponível após summary.json.");
  const spreads = ["0", "5", "10", "20"];
  const costs = d.costs
    ? table(
        [
          { label: "Participante", render: (r) => `${sw(r.id)} ${esc(r.label)}` },
          ...spreads.map((sp) => ({ label: `${sp} bps · Sharpe`, n: 1, render: (r) => { const c = d.costs[sp]?.rows.find((x) => x.id === r.id); return !c ? "—" : c.sharpe == null ? `<span class="na" title="${esc(c.status)} ${esc(c.reason || "")}">N/A — EXACT_REPLAY_INVALID</span>` : `${num(c.sharpe, 3)}<div class="muted">${signed(c.net_return, (v) => pct(v))}</div>`; } })),
        ],
        ids.map(part),
      ) + `<div class="row" style="margin-top:12px">${spreads.map((sp) => { const x = d.costs[sp]?.statistics; return `<span class="chip">${sp} bps · Δ ${x ? signed(x.delta, (v) => num(v, 3)) : '<span class="na">N/A (sem agregação de subconjunto)</span>'}</span>`; }).join("")}</div>`
    : empty("Sensibilidade 0/5/10/20 bps disponível após cost_closure.json.");
  el.innerHTML = `
    <h2>H2 v6 × Buy & Hold × SMA Regime × Bollinger Estado</h2>
    ${card("Evolução do patrimônio · capital inicial R$ 100.000", d.curves ? `${legend(ids)}<div class="chart"><canvas id="c-equity"></canvas></div>` : empty("Sem curvas seladas."))}
    <div class="grid g-2" style="margin-top:16px">
      ${card("Drawdown", d.curves ? `${legend(ids)}<div class="chart sm"><canvas id="c-dd"></canvas></div>` : empty("Sem curvas seladas."))}
      ${card("Sharpe por participante", d.curves ? `<div class="chart sm"><canvas id="c-sharpe"></canvas></div>` : empty("Sem métricas."))}
    </div>
    <div style="margin-top:16px">${card("Métricas", metricTable)}</div>
    <div style="margin-top:16px">${d.synthetic ? "" : exposureSection()}</div>
    <div style="margin-top:16px">${card("Comparação dos três runs", runs)}</div>
    <div style="margin-top:16px">${card("Sensibilidade de custos · Sharpe e retorno líquido", costs + `<p class="muted" style="margin-top:8px">H2 fora de 5 bps: o replay exato diverge na chamada #67 (o prompt do PM embute o drawdown após custos). O valor não é interpolado nem estimado.</p>`)}</div>`;
  if (d.curves) {
    lineChart("c-equity", d.curves.dates, curveSeries(ids), { money: true, returns: d.curves.return });
    lineChart("c-dd", d.curves.dates, curveSeries(ids, "drawdown"), { percent: true });
    barChart("c-sharpe", ids.map(part).filter((p) => p.metrics).map((p) => ({ id: p.id, label: p.label, value: p.metrics.sharpe })));
  }
  exposureCharts();
}

function renderAudit() {
  const d = state.data, s = state.status;
  const el = document.getElementById("tab-audit");
  if (!d || !s) return (el.innerHTML = "");
  const id = s.identity;
  const picks = [...LLM, ...BENCH].map((r) => `<button class="pick" data-audit="${r}" aria-pressed="${r === state.auditRun}">${sw(r)}${esc(label(r))}</button>`).join("");
  const det = state.detail;
  const decisions = det?.decisions?.length
    ? table(
        [
          { label: "Sessão", render: (r) => `<span class="mono">${esc(r.decision_session)}</span>` },
          { label: "Votos C/M/V", render: (r) => (r.vote_counts ? `${r.vote_counts.COMPRA}/${r.vote_counts.MANTER}/${r.vote_counts.VENDA}` : "—") },
          { label: "Technical", render: (r) => esc(r.technical_outcome) },
          { label: "Risk", render: (r) => `${esc(r.risk_verdict)} <span style="color:var(--muted)">${esc(r.risk_source)}</span>` },
          { label: "Portfolio", render: (r) => `${esc(r.portfolio_decision)} <span style="color:var(--muted)">${esc(r.portfolio_source)}</span>` },
          { label: "Causa", render: (r) => `<span class="mono">${esc(r.final_cause)}</span>` },
          { label: "Erros", n: 1, render: (r) => r.errors },
        ],
        det.decisions,
        { click: true, selected: (r) => r.decision_session === state.session },
      )
    : empty(inflight.has("detail") ? "Carregando…" : det ? "Sem decisões LLM (benchmark determinístico)." : "Run não selado nesta fonte.");
  const tr = state.trace;
  const traceHtml = tr
    ? tr.calls.length
      ? tr.calls.map((c) => `<div class="card" style="margin-bottom:10px;padding:12px"><div class="row" style="margin-bottom:6px">${chip(c.status === "ok" ? "VALID" : `ERRO ${c.error_type || ""}`)}<b>${esc({ technical_analyst: "Technical", risk_manager: "Risk", portfolio_manager: "Portfolio" }[c.stage] || c.stage)}</b>${c.analyst_id ? `analista ${c.analyst_id}` : ""}<span style="color:var(--muted)">seq ${c.sequence} · ${num(c.duration_ms / 1000, 1)} s · tentativas ${c.attempt_count ?? "—"} · tokens ${c.token_usage?.prompt_tokens ?? "—"}/${c.token_usage?.completion_tokens ?? "—"}</span></div><pre>${esc(JSON.stringify(c.response ?? c.error_message, null, 2))}</pre>${c.explanation ? `<details><summary style="cursor:pointer;color:var(--muted);font-size:12px">justificativa registrada</summary><pre>${esc(c.explanation)}</pre></details>` : ""}${c.inputs ? `<details><summary style="cursor:pointer;color:var(--muted);font-size:12px">entradas estruturadas</summary><pre>${esc(JSON.stringify(c.inputs, null, 2))}</pre></details>` : ""}</div>`).join("")
      : empty("Nenhuma chamada LLM nesta sessão.")
    : empty("Clique numa sessão para ver as evidências Technical, Risk e Portfolio.");
  const trades = det?.trades?.length
    ? table(
        [
          { label: "Data", render: (r) => `<span class="mono">${esc(r.date)}</span>` },
          { label: "Operação", render: (r) => `<span class="${r.type === "BUY" ? "up" : "down"}">${r.type === "BUY" ? "▲ COMPRA" : "▼ VENDA"}</span>` },
          { label: "Preço", n: 1, render: (r) => brl(r.price) },
          { label: "Quantidade", n: 1, render: (r) => num(r.quantity, 2) },
          { label: "Notional", n: 1, render: (r) => brl(r.price * r.quantity) },
          { label: "Custo", n: 1, render: (r) => brl(r.cost) },
        ],
        det.trades,
      )
    : empty("Sem operações.");
  const files = d.files[state.auditRun] || [];
  const dl = (run, f) => `<a href="/api/h2/artifact?source=${d.source}&run=${run}&name=${encodeURIComponent(f.name)}">${esc(f.name)}</a>`;
  const downloads = d.synthetic
    ? empty("Downloads indisponíveis na demonstração.")
    : files.length || d.root_files.length
      ? table([{ label: "Arquivo", render: (f) => dl(f.run, f) }, { label: "Bytes", n: 1, render: (f) => f.bytes?.toLocaleString("pt-BR") ?? "—" }, { label: "SHA256", render: (f) => `<span class="mono" title="${esc(f.sha256)}">${short(f.sha256)}</span>` }], [...d.root_files.map((f) => ({ ...f, run: "_root" })), ...files.map((f) => ({ ...f, run: state.auditRun }))])
      : empty("Nenhum artifact selado.");
  el.innerHTML = `
    <h2>Auditoria</h2>
    <div class="grid g-2">
      ${card("Manifesto e hashes", `<dl>
        <dt>Manifesto (SHA externo)</dt><dd class="mono">${esc(id.manifest_sha256)}</dd>
        <dt>Estado</dt><dd>${chip(id.state)} live_authorized=${id.live_authorized}</dd>
        <dt>Aprovações</dt><dd>autor ${id.approvals.author ? "✓" : "—"} · coautor ${id.approvals.coauthor ? "✓" : "—"} · orientador ${id.approvals.advisor ? "✓" : "—"} · freeze ${id.freeze_record ? "✓" : "—"}</dd>
        <dt>ParticipantSpec</dt><dd class="mono">${esc(id.participant_sha256)}</dd>
        <dt>Snapshot</dt><dd class="mono">${esc(id.snapshot.id)}<br>${esc(id.snapshot.identity)}</dd>
        <dt>Inventário</dt><dd>${id.inventory_sizes.sources_sha256} fontes · ${id.inventory_sizes.documents_sha256} documentos · ${id.inventory_sizes.historical_bindings_sha256} bindings CAL-B4</dd>
        <dt>Ambiente</dt><dd>Python ${esc(id.environment.python)} · SQLite ${esc(id.environment.sqlite_version)} (${esc(id.environment.sqlite_synchronous)}) · ${esc(id.environment.platform)}</dd>
        <dt>Custos</dt><dd>spread ${id.costs.spread_bps} bps · taxa ${num(id.costs.tax_rate * 100, 3)}% · grade ${id.cost_grid.join("/")} bps</dd>
        <dt>Teste</dt><dd>Bootstrap ${esc(id.test.candidate)} · B=${id.test.B} · seed ${id.test.seed} · bloco ${id.test.mean_block} · α=${id.test.alpha}</dd>
        <dt>Benchmarks</dt><dd>${id.benchmarks.map((b) => `${esc(b.spec.kind)} <span class="mono">${short(b.sha256)}</span>`).join("<br>")}</dd></dl>`)}
      ${card("Downloads de artifacts", downloads)}
    </div>
    <div class="row" style="margin-top:16px">${picks}</div>
    <div class="grid g-2">
      ${card("Decisions", decisions, 'id="decisions-card"')}
      ${card(state.session ? `Traces · ${state.session}` : "Traces", `<div class="scroll">${traceHtml}</div>`)}
    </div>
    <div style="margin-top:16px">${card("Timeline de operações", trades)}</div>`;
  el.querySelectorAll("#decisions-card tr.click").forEach((row) => row.addEventListener("click", () => loadTrace(det.decisions[row.dataset.i].decision_session)));
}

// ── post-Validation analysis ────────────────────────────────────────────────
const SIG = { COMPRA: "#0ca30c", VENDA: "#ec835a", MANTER: "#5f5e5a" };
const SIDE = { BUY: "▲ COMPRA", SELL: "▼ VENDA" };
const nr = (v, f = esc) => (v == null || v === "" ? `<span class="nr">Não registrado</span>` : f(v));
const TAGS = { f: ["FATO", "fato observado nos artifacts selados"], h: ["HIPÓTESE", "hipótese interpretativa — não demonstrada"], l: ["LIMITAÇÃO", "limitação de evidência"] };
const tag = (k) => `<span class="tag ${k}" title="${TAGS[k][1]}">${TAGS[k][0]}</span>`;
const int = (v) => (v == null ? "—" : v.toLocaleString("pt-BR"));
const CAUSE = {
  ACTION_BUY: "Consenso COMPRA aprovado pelo Risk e seguido pelo PM: alvo 100%",
  ACTION_SELL: "Consenso VENDA (auto-aprovado) seguido pelo PM: alvo 0%",
  BUY_AT_TARGET_NOOP: "Consenso COMPRA com a carteira já em 100%: veto de concentração sem efeito",
  TECH_EXPLICIT_HOLD: "Consenso MANTER: nenhuma ordem",
  TECH_NO_MAJORITY: "Sem maioria técnica: nenhuma ordem",
};
const FEATURE = { sma50_gap: ["Fech. / SMA50 − 1", "pct"], sma200_gap: ["Fech. / SMA200 − 1", "pct"], macd_ratio: ["MACD / fech.", "pct"], macd_signal_ratio: ["Sinal do MACD / fech.", "pct"], rsi: ["RSI", "num"], bb_upper_gap: ["Fech. / banda superior − 1", "pct"], bb_lower_gap: ["Fech. / banda inferior − 1", "pct"], bb_width: ["Largura das bandas de Bollinger", "pct"] };
const roleCls = (r) => ({ SUPPORTS_COMPRA: "buy", SUPPORTS_VENDA: "sell", CAUTION: "caution" }[r] || "");
const sig = (s) => (s ? `<b style="color:${SIG[s] || "inherit"}">${{ COMPRA: "▲ ", VENDA: "▼ ", MANTER: "■ " }[s] || ""}${esc(s)}</b>` : `<span class="nr">Não registrado</span>`);
const A = () => (state.analysis && state.analysis !== "loading" ? state.analysis : null);
const dateIndex = () => new Map(A().market.dates.map((d, i) => [d, i]));

function analysisGate(el, head = "") {
  if (A()) return true;
  el.innerHTML = head + (state.analysis === "loading" || state.analysis === undefined
    ? `<div class="empty">Carregando artifacts selados…</div>`
    : empty(state.data?.synthetic
      ? "A demonstração não possui traces de decisão. Selecione a fonte Provisória OA-1 para a análise real."
      : `Sem runs selados nesta fonte (estado: ${state.data?.state || "desconhecido"}). A análise usa apenas runs COMPLETE.`));
  return false;
}
function spans(flags) {
  const out = [];
  let start = null;
  flags.forEach((v, i) => {
    if (v && start == null) start = i;
    if (!v && start != null) { out.push([start, i - 1]); start = null; }
  });
  if (start != null) out.push([start, flags.length - 1]);
  return out;
}
// Shades index ranges behind the data: long periods, the selected cycle, t → t+1.
const bandsPlugin = {
  id: "bands",
  beforeDatasetsDraw(chart, _args, opts) {
    const x = chart.scales.x, { top, bottom } = chart.chartArea, ctx = chart.ctx;
    if (!opts?.spans?.length) return;
    const half = (x.getPixelForValue(1) - x.getPixelForValue(0)) / 2;
    ctx.save();
    for (const s of opts.spans) {
      const x0 = x.getPixelForValue(s.from) - half, w = x.getPixelForValue(s.to) + half - x0;
      ctx.fillStyle = s.fill;
      ctx.fillRect(x0, top, w, bottom - top);
      if (s.stroke) { ctx.strokeStyle = s.stroke; ctx.lineWidth = 1.5; ctx.strokeRect(x0, top + 1, w, bottom - top - 2); }
    }
    ctx.restore();
  },
};
function bandSpecs() {
  const p = A()?.participants[state.dRun];
  if (!p) return [];
  const c = color(state.dRun), idx = dateIndex();
  const out = spans(p.long).map(([from, to]) => ({ from, to, fill: `${c}1c` }));
  const cy = state.cycle != null ? p.cycles[state.cycle] : null;
  if (cy) out.push({ from: idx.get(cy.entry), to: idx.get(cy.exit), fill: `${c}33`, stroke: c });
  const d = state.decision;
  if (d?.session && idx.has(d.session)) out.push({ from: idx.get(d.session), to: idx.get(d.execution_session ?? d.session), fill: "rgba(255,255,255,.14)" });
  return out;
}
function updateBands() {
  const ch = charts["c-price"];
  if (!ch) return;
  ch.options.plugins.bands.spans = bandSpecs();
  ch.update("none");
}

function priceChart() {
  charts["c-price"]?.destroy();
  const el = document.getElementById("c-price");
  if (!el) return;
  const a = A(), m = a.market, idx = dateIndex();
  const datasets = [{ label: "PETR4 · fechamento ajustado", data: m.close, borderColor: INK.text2, borderWidth: 1.5, pointRadius: 0, pointHoverRadius: 3, order: 9 }];
  if (state.showSma) datasets.push(
    { label: "SMA50 (reconstruída)", data: m.sma50, borderColor: "#8f8d86", borderDash: [6, 4], borderWidth: 1.2, pointRadius: 0, order: 8 },
    { label: "SMA200 (reconstruída)", data: m.sma200, borderColor: "#6b6a65", borderDash: [2, 3], borderWidth: 1.2, pointRadius: 0, order: 8 },
  );
  const BOLL = "bollinger_state_h2_proposed";
  const marker = (id, kind, rows, xy, filled) => {
    const pts = rows.map((t) => ({ ...xy(t), ev: t })).filter((p) => p.y != null);
    return {
      label: `${label(id)} · ${kind === "decision" ? "decisão (fech. t)" : "execução (abertura t+1)"}`, kind, run: id, showLine: false, data: pts,
      pointStyle: id === BOLL ? "rectRot" : "triangle",
      pointRotation: pts.map((p) => (p.ev.type === "SELL" && id !== BOLL ? 180 : 0)),
      pointRadius: filled ? 7 : 6, pointHoverRadius: 9, pointHitRadius: 12, pointBorderWidth: 2,
      pointBackgroundColor: filled ? color(id) : INK.surface, pointBorderColor: filled ? INK.surface : color(id), order: filled ? 1 : 2,
    };
  };
  for (const id of LLM.filter((r) => state.runsOn.has(r) && a.participants[r])) {
    const t = a.participants[id].trades;
    datasets.push(marker(id, "decision", t, (x) => ({ x: x.decision_session, y: m.close[idx.get(x.decision_session)] }), false));
    datasets.push(marker(id, "exec", t, (x) => ({ x: x.date, y: x.price }), true));
  }
  if (state.showBoll && a.participants[BOLL]) datasets.push(marker(BOLL, "exec", a.participants[BOLL].trades, (x) => ({ x: x.date, y: x.price }), true));
  charts["c-price"] = new Chart(el, {
    type: "line",
    data: { labels: m.dates, datasets },
    plugins: [bandsPlugin],
    options: {
      responsive: true, maintainAspectRatio: false, animation: { duration: 300 },
      interaction: { mode: "x", intersect: false },
      onHover: (_e, _els, ch) => { ch.canvas.style.cursor = "pointer"; },
      onClick: (e, _els, ch) => {
        const hit = ch.getElementsAtEventForMode(e, "nearest", { intersect: true }, false)
          .map((x) => ({ ds: ch.data.datasets[x.datasetIndex], raw: ch.data.datasets[x.datasetIndex].data[x.index] }))
          .find((h) => h.raw?.ev);
        if (hit && LLM.includes(hit.ds.run)) return loadDecision(hit.ds.run, hit.raw.ev.decision_session);
        if (hit) { abort("decision"); Object.assign(state, { bollEvent: hit.raw.ev, decision: null, pending: null }); updateBands(); return renderDecisionPanel(); }
        const i = Math.round(ch.scales.x.getValueForPixel(e.x));
        if (i >= 0 && i < m.dates.length - 1) loadDecision(state.dRun, m.dates[i]);
      },
      plugins: {
        legend: { display: false },
        bands: { spans: bandSpecs() },
        tooltip: {
          backgroundColor: "#222220", borderColor: "rgba(255,255,255,.12)", borderWidth: 1, titleColor: "#fff", bodyColor: INK.text2, padding: 10,
          filter: (c) => c.parsed.y != null,
          callbacks: {
            label: (c) => {
              const ev = c.raw?.ev, ds = c.dataset;
              if (ds.kind === "decision") return ` ${label(ds.run)} · DECISÃO ${SIDE[ev.type]} no fechamento ${brl(c.parsed.y)} → executa ${ev.date}`;
              if (ds.kind === "exec") return ` ${label(ds.run)} · EXECUÇÃO ${SIDE[ev.type]} na abertura ${brl(ev.price)} · qtd ${num(ev.quantity, 2)} · custo ${brl(ev.cost)} (decidida em ${ev.decision_session})`;
              return ` ${ds.label}: ${brl(c.parsed.y)}`;
            },
          },
        },
      },
      scales: {
        x: { ticks: { color: INK.muted, maxTicksLimit: 9, maxRotation: 0 }, grid: { display: false }, border: { color: INK.axis } },
        y: { ticks: { color: INK.muted, callback: (v) => brl(v) }, grid: { color: INK.grid }, border: { display: false } },
      },
    },
  });
}

function renderDecisions() {
  const el = document.getElementById("tab-decisions");
  if (!state.data) return (el.innerHTML = "");
  const head = `<h2>Análise de Decisões</h2>
    <p class="note">Cada operação aparece em dois momentos: <b>decisão no fechamento de t</b> (marcador vazado sobre o fechamento) e <b>execução na abertura de t+1</b> (marcador cheio no preço executado). ▲ compra · ▼ venda · ◆ Bollinger. A faixa sombreada é a posição comprada do run do painel. Clique num marcador ou em qualquer data para abrir a explicação da sessão.</p>`;
  if (!analysisGate(el, head)) return;
  const a = A();
  const toggles = LLM.map((id) => `<button class="pick" data-run-toggle="${id}" aria-pressed="${state.runsOn.has(id)}">${sw(id)}${esc(label(id))}</button>`).join("");
  const focus = LLM.filter((id) => a.participants[id]).map((id) => `<button class="pick" data-drun="${id}" aria-pressed="${id === state.dRun}">${sw(id)}${id}</button>`).join("");
  const legendItems = [
    `<span><i class="solid" style="border-color:${INK.text2}"></i>PETR4 fechamento</span>`,
    state.showSma ? `<span><i class="dash" style="border-color:#8f8d86"></i>SMA50</span><span><i class="dash" style="border-color:#6b6a65;border-top-style:dotted"></i>SMA200</span>` : "",
    ...LLM.filter((id) => state.runsOn.has(id)).map((id) => `<span>${sw(id)}${esc(label(id))} △ decisão ▲ execução</span>`),
    state.showBoll ? `<span>${sw("bollinger_state_h2_proposed")}Bollinger ◆ execução</span>` : "",
    `<span><i class="swatch" style="background:${color(state.dRun)}40"></i>${state.dRun} comprado</span>`,
  ].join("");
  el.innerHTML = `${head}
    <div class="row">${toggles}<span class="sep"></span>
      <button class="pick" data-toggle="showBoll" aria-pressed="${state.showBoll}">${sw("bollinger_state_h2_proposed")}Trades Bollinger</button>
      <button class="pick" data-toggle="showSma" aria-pressed="${state.showSma}">SMA50 / SMA200</button>
      <span class="sep"></span><span class="muted">Painel e faixa:</span>${focus}</div>
    ${card("Preço × decisões · PETR4.SA · Validation 2024-09-02 → 2025-08-29", `<div class="legend">${legendItems}</div><div class="chart lg"><canvas id="c-price"></canvas></div>
      <p class="muted" style="margin-top:8px">Preços: fechamentos ajustados implícitos na curva selada do Buy &amp; Hold (2024-09-03 → 2025-08-29; o fechamento de 2024-09-02 não é recuperável, por isso a decisão dessa data não tem marcador) e aberturas apenas nos dias com execução. SMA = fechamento / (1 + gap enviado aos analistas, 6 casas). Nenhum preço externo; o snapshot não é aberto.</p>`)}
    <div id="decision-panel" style="margin-top:16px"></div>
    <div id="cycles" style="margin-top:16px"></div>`;
  priceChart();
  renderDecisionPanel();
  renderCycles();
  if (!state.decision && !state.pending && !state.bollEvent) {
    const first = a.participants[state.dRun]?.trades[0];
    if (first) loadDecision(state.dRun, first.decision_session);
  }
}

function voteBar(v) {
  const total = (v.COMPRA || 0) + (v.VENDA || 0) + (v.MANTER || 0) || 1;
  return `<div class="votebar" role="img" aria-label="COMPRA ${v.COMPRA}, VENDA ${v.VENDA}, MANTER ${v.MANTER}">${["COMPRA", "VENDA", "MANTER"].filter((k) => v[k]).map((k) => `<span title="${k}: ${v[k]}" style="width:${(100 * v[k]) / total}%;background:${SIG[k]}"></span>`).join("")}</div>
    <div class="muted">▲ COMPRA ${v.COMPRA ?? 0} · ▼ VENDA ${v.VENDA ?? 0} · ■ MANTER ${v.MANTER ?? 0}</div>`;
}

function renderDecisionPanel() {
  const el = document.getElementById("decision-panel");
  if (!el || !A()) return;
  const b = state.bollEvent;
  if (b) {
    el.innerHTML = card("Bollinger Estado 20/2 · benchmark determinístico", `<p class="note" style="margin:0 0 10px">Regra fixa, sem agentes: compra com fechamento na banda inferior ou abaixo, vende na banda superior ou acima. Não há votos, Risk ou Portfolio a explicar.</p>
      <dl><dt>Decisão (fech. t)</dt><dd class="mono">${esc(b.decision_session)}</dd><dt>Execução (abertura t+1)</dt><dd class="mono">${esc(b.date)}</dd><dt>Ordem</dt><dd>${SIDE[b.type]}</dd><dt>Preço</dt><dd>${brl(b.price)}</dd><dt>Quantidade</dt><dd>${num(b.quantity, 4)}</dd><dt>Custo</dt><dd>${brl(b.cost)}</dd><dt>Patrimônio no fech.</dt><dd>${brl(b.equity_close)}</dd></dl>`);
    return;
  }
  const d = state.decision;
  if (!d) { el.innerHTML = card("Explicação da decisão", `<div class="empty">${state.pending ? "Carregando sessão…" : "Clique num marcador ou numa data do gráfico."}</div>`); return; }
  if (d.missing) { el.innerHTML = card("Explicação da decisão", empty(`Sessão ${d.missing}: sem registro de decisão no run ${d.run}.`)); return; }
  const t = d.technical, r = d.risk, p = d.portfolio, x = d.execution, tr = x.trade;
  const nav = `<button class="pick" data-session="${esc(d.prev_session || "")}" ${d.prev_session ? "" : "disabled"} aria-label="Sessão anterior">←</button>
    <input type="date" id="session-pick" value="${esc(d.session)}" min="${esc(A().market.dates[0])}" max="${esc(A().market.dates.at(-2))}" aria-label="Ir para sessão">
    <button class="pick" data-session="${esc(d.next_session || "")}" ${d.next_session ? "" : "disabled"} aria-label="Próxima sessão">→</button>`;
  const analysts = t.analysts.length
    ? `<table><thead><tr><th>#</th><th>Voto</th><th class="n">Conf.</th><th>Evidências citadas</th></tr></thead><tbody>${t.analysts.map((c) => `<tr><td>${c.analyst_id}</td><td>${sig(c.signal)}</td><td class="n">${nr(c.confidence, (v) => num(v, 2))}</td><td>${(c.evidence || []).map((e) => `<span class="ev ${roleCls(e.role)}" title="${esc(e.role)}">${esc(e.code)}</span>`).join("") || nr(null)}${c.explanation ? `<details><summary class="muted" style="cursor:pointer">justificativa registrada</summary><div class="muted" style="margin-top:4px">${esc(c.explanation)}</div></details>` : ""}</td></tr>`).join("")}</tbody></table>`
    : empty("Nenhuma chamada técnica registrada.");
  const feats = t.features ? `<table><tbody>${Object.entries(t.features).map(([k, v]) => `<tr><td class="muted">${esc(FEATURE[k]?.[0] || k)}</td><td class="n mono">${FEATURE[k]?.[1] === "num" ? num(v, 2) : signed(v, (z) => pct(z, 2))}</td></tr>`).join("")}</tbody></table>` : nr(null);
  const rules = `<table><thead><tr><th>Regra</th><th>Limite</th><th class="n">Valor</th><th>Status</th></tr></thead><tbody>${r.rules.map((q) => `<tr><td class="mono">${esc(q.rule)}</td><td class="mono">${esc(q.limit || "—")}</td><td class="n mono">${q.rule === "AUTO_APPROVE" || q.rule === "RISK_LLM" ? "—" : nr(q.value, (v) => num(v, 6))}</td><td>${chip(q.status)}</td></tr>`).join("")}</tbody></table>`;
  const veto = r.veto_effect === "SEM EFEITO"
    ? "Veto <b>sem efeito</b>: a carteira já estava no alvo de 100%; sem o veto também não haveria ordem."
    : r.veto_effect === "EFETIVO" ? "<b>Intervenção efetiva</b>: sem o veto o consenso COMPRA geraria uma ordem." : "Sem veto nesta sessão.";
  const pmNote = p.called
    ? chip(p.followed_consensus ? "SEGUIU o consenso técnico" : "ALTEROU o consenso técnico")
    : r.verdict === "VETADO" ? "Não chamado: o Risk vetou antes." : p.rule === "TECH_HOLD" ? "Não chamado: consenso MANTER resolvido por regra (TECH_HOLD)." : "Não chamado.";
  const noOrder = d.final_cause === "ACTION_SELL" && p.weight_before === 0 ? "alvo 0% já satisfeito (carteira em caixa)"
    : d.final_cause === "BUY_AT_TARGET_NOOP" ? "carteira já 100% comprada"
    : d.final_cause === "TECH_EXPLICIT_HOLD" ? "consenso MANTER" : esc(d.final_cause);
  const same = (x.implied_by_consensus || null) === (tr?.type || null);
  el.innerHTML = `<div class="card ${state.pending ? "loading" : ""}">
    <div class="panel-head">${sw(d.slot)}<span class="title">${esc(label(d.slot))} · decisão ${esc(d.session)} <span class="muted">(fechamento de t)</span> → execução ${esc(d.execution_session || "—")} <span class="muted">(abertura de t+1)</span></span>${nav}<span class="spacer"></span>${chip(d.final_cause)}</div>
    <p class="note" style="margin:0 0 14px">${tag("f")} ${esc(CAUSE[d.final_cause] || d.final_cause)}.${d.errors.length ? ` Erros: ${esc(d.errors.join("; "))}` : ""}</p>
    <div class="grid g-2">
      <div class="card sub"><h3>Technical Analysts · 5</h3>
        <div>Consenso ${sig(t.outcome)} · ${t.vote_counts ? `${Math.max(...Object.values(t.vote_counts))}/${t.valid_votes}` : "—"} votos · limiar ${pct(t.threshold, 0)} ${t.consensus_reached ? "" : chip("SEM MAIORIA")}</div>
        ${t.vote_counts ? voteBar(t.vote_counts) : ""}
        <div style="margin-top:10px">${analysts}</div>
        <details style="margin-top:10px"><summary class="muted" style="cursor:pointer">Indicadores recebidos no prompt</summary>${feats}</details>
        <div style="margin-top:8px" class="muted">Indicadores citados: ${t.evidence_summary.length ? t.evidence_summary.map((e) => `<span class="ev ${roleCls(e.role)}" title="${esc(e.role)}">${esc(e.code)} ×${e.count}</span>`).join("") : nr(null)}</div>
      </div>
      <div class="card sub"><h3>Risk Manager</h3>
        <div class="row">${chip(r.verdict)}<span class="muted">fonte ${esc(r.source)}${r.rule ? ` · regra ${esc(r.rule)}` : ""}</span></div>
        ${rules}
        <p class="muted" style="margin-top:6px">VENDA/MANTER são auto-aprovadas; uma COMPRA passa por volatilidade → drawdown → concentração → Risk LLM. "PASSOU" sem valor: verificada antes da regra que disparou, mas a métrica não foi gravada.</p>
        <dl style="margin-top:10px"><dt>Drawdown em t</dt><dd>${pct(r.drawdown, 2)} <span class="muted">(recalculado de equity.csv; igual ao enviado nos prompts)</span></dd><dt>Efeito do veto</dt><dd>${veto}</dd><dt>Parecer LLM</dt><dd>${nr(r.analysis)}</dd></dl>
      </div>
      <div class="card sub"><h3>Portfolio Manager</h3>
        <div class="row">${p.decision ? sig(p.decision) : `<span class="nr">Sem decisão do PM</span>`}<span class="muted">${p.source ? `fonte ${esc(p.source)}` : ""}${p.rule ? ` · regra ${esc(p.rule)}` : ""}</span></div>
        <div style="margin-bottom:10px">${pmNote}</div>
        <dl><dt>Posição antes</dt><dd>${nr(p.weight_before, (v) => pct(v, 0))}</dd><dt>Posição depois</dt><dd>${nr(p.weight_after, (v) => pct(v, 0))}</dd><dt>Peso-alvo</dt><dd>${nr(p.target_weight, (v) => pct(v, 0))}</dd>
        <dt>Sinal recebido</dt><dd>${t.signal_sent ? `${sig(t.signal_sent.signal)} conf. ${num(t.signal_sent.confidence, 2)} · ${esc(t.signal_sent.justification)}` : nr(null)}</dd>
        <dt>Justificativa</dt><dd>${nr(p.reasoning)}</dd></dl>
      </div>
      <div class="card sub"><h3>Execução</h3>
        ${tr ? `<div class="row"><b class="${tr.type === "BUY" ? "up" : "down"}">${SIDE[tr.type]}</b><span class="muted">abertura de ${esc(tr.date)}</span></div>
        <dl><dt>Preço</dt><dd>${brl(tr.price)}</dd><dt>Quantidade</dt><dd>${num(tr.quantity, 4)}</dd><dt>Nocional</dt><dd>${brl(tr.notional)}</dd><dt>Custos</dt><dd>${brl(tr.cost)} <span class="muted">(5 bps + 0,032%)</span></dd><dt>Caixa após</dt><dd>${brl(Math.abs(tr.cash_after) < 0.005 ? 0 : tr.cash_after)}</dd><dt>Patrimônio (fech. ${esc(tr.date)})</dt><dd>${brl(tr.equity_close)}</dd></dl>`
        : `<div class="row">${chip("SEM ORDEM")}<span class="muted">${esc(d.execution_session || "fim da janela")}</span></div><p class="muted">Motivo: ${noOrder}.</p>`}
        <dl style="margin-top:10px"><dt>Ordem implicada pelo consenso</dt><dd>${x.implied_by_consensus ? SIDE[x.implied_by_consensus] : "nenhuma"} ${chip(same ? "= executada" : "DIFERE da executada")}</dd><dt>Patrimônio em t</dt><dd>${brl(x.equity_at_decision)}</dd></dl>
      </div>
    </div></div>`;
}

function renderCycles() {
  const el = document.getElementById("cycles");
  const p = A()?.participants[state.dRun];
  if (!el || !p) return;
  const cy = p.cycles;
  const rows = cy.map((c, i) => ({ ...c, i, cashUntil: cy[i + 1]?.entry || "fim da janela" }));
  const total = cy.reduce((s, c) => s + (c.pnl ?? 0), 0);
  el.innerHTML = card(`Timeline das operações · ${label(state.dRun)}`, rows.length ? table(
    [
      { label: "#", render: (c) => c.i + 1 },
      { label: "Entrada · decisão → execução", render: (c) => `<span class="mono">${esc(c.entry_decision)} → ${esc(c.entry)}</span>` },
      { label: "Saída · decisão → execução", render: (c) => (c.status === "OPEN" ? chip("ABERTA") : `<span class="mono">${esc(c.exit_decision)} → ${esc(c.exit)}</span>`) },
      { label: "Pregões", n: 1, render: (c) => c.sessions },
      { label: "Preço entrada → saída", n: 1, render: (c) => `${num(c.entry_price, 4)} → ${num(c.exit_price, 4)}` },
      { label: "Var. preço", n: 1, render: (c) => `<span class="${tone(c.price_change)}">${signed(c.price_change, (v) => pct(v))}</span>` },
      { label: "Resultado líquido", n: 1, render: (c) => `<span class="${tone(c.pnl)}">${c.pnl == null ? "N/A" : `${c.pnl > 0 ? "+" : ""}${brl(c.pnl)}`}</span>` },
      { label: "Custos", n: 1, render: (c) => brl(c.costs) },
      { label: "Patrimônio após", n: 1, render: (c) => brl(c.equity_after) },
      { label: "Carteira depois", render: (c) => (c.status === "OPEN" ? "comprada" : `caixa até ${esc(c.cashUntil)}`) },
    ],
    rows,
    { click: true, selected: (c) => c.i === state.cycle },
  ) + `<p class="muted" style="margin-top:8px">${tag("f")} Soma dos ciclos: ${brl(total)} · ${cy.filter((c) => (c.pnl ?? 0) > 0).length} de ${cy.length} ciclos lucrativos. Clique num ciclo para destacá-lo no gráfico.</p>` : empty("Nenhuma operação."));
  el.querySelectorAll("tr.click").forEach((row) => row.addEventListener("click", () => {
    const i = Number(row.dataset.i);
    state.cycle = state.cycle === i ? null : i;
    renderCycles();
    updateBands();
    document.getElementById("c-price")?.scrollIntoView({ behavior: "smooth", block: "center" });
  }));
}

// Exposure: PETR4 above, long periods per participant below, same x positions.
function exposureSection() {
  const a = A();
  if (!a) return card("Exposição ao mercado", state.analysis === "loading" ? `<div class="empty">Carregando…</div>` : empty("Exposição disponível apenas para runs reais selados."));
  const ids = [...LLM, ...BENCH].filter((id) => a.participants[id]);
  const f = (x) => `${x.days} <span class="muted">(${signed(x.asset_return, (v) => pct(v, 1))})</span>`;
  const rows = table(
    [
      { label: "Participante", render: (id) => `${sw(id)} ${esc(label(id))}` },
      { label: "Comprado no fech.", n: 1, render: (id) => a.participants[id].exposure.closes.long },
      { label: "Em caixa no fech.", n: 1, render: (id) => a.participants[id].exposure.closes.cash },
      { label: "% comprado", n: 1, render: (id) => pct(a.participants[id].exposure.closes.share, 1) },
      { label: "Dias comprado inteiro", n: 1, render: (id) => f(a.participants[id].exposure.daily.long) },
      { label: "Dias em caixa inteiro", n: 1, render: (id) => f(a.participants[id].exposure.daily.cash) },
      { label: "Dias de entrada", n: 1, render: (id) => f(a.participants[id].exposure.daily.entry) },
      { label: "Dias de saída", n: 1, render: (id) => f(a.participants[id].exposure.daily.exit) },
    ],
    ids,
  );
  const e = a.participants[ids[0]].exposure;
  return card("Exposição ao mercado", `<div class="legend">${ids.map((id) => `<span>${sw(id)}${esc(label(id))}</span>`).join("")}<span class="muted">barra = comprado no fechamento</span></div>
    <div class="chart xs"><canvas id="c-exp-price"></canvas></div><div class="chart strip"><canvas id="c-exp-strip"></canvas></div>
    <div style="margin-top:12px">${rows}</div>
    <p class="muted" style="margin-top:8px">${tag("f")} Dois denominadores, não equivalentes: <b>contagem de posições</b> no fechamento das ${e.closes.total} sessões de decisão (${esc(a.market.dates[0])} → ${esc(a.market.dates.at(-2))}) e <b>atribuição dos ${e.daily_total} retornos diários</b> (${esc(a.market.dates[1])} → ${esc(a.market.dates.at(-1))}), em que dias de entrada/saída ficam à parte. Entre parênteses: retorno do Buy &amp; Hold (proxy de PETR4 100% investida) acumulado nesses dias.</p>`);
}
function exposureCharts() {
  const a = A(), p = document.getElementById("c-exp-price"), s = document.getElementById("c-exp-strip");
  charts["c-exp-price"]?.destroy();
  charts["c-exp-strip"]?.destroy();
  if (!a || !p || !s) return;
  const m = a.market, ids = [...LLM, ...BENCH].filter((id) => a.participants[id]);
  const fitY = { afterFit: (scale) => { scale.width = 132; } };
  const tip = { backgroundColor: "#222220", borderColor: "rgba(255,255,255,.12)", borderWidth: 1, titleColor: "#fff", bodyColor: INK.text2, padding: 10 };
  charts["c-exp-price"] = new Chart(p, {
    type: "line",
    data: { labels: m.dates, datasets: [{ label: "PETR4", data: m.close, borderColor: INK.text2, borderWidth: 1.5, pointRadius: 0, pointHoverRadius: 3 }] },
    options: {
      responsive: true, maintainAspectRatio: false, animation: false, interaction: { mode: "index", intersect: false },
      plugins: { legend: { display: false }, tooltip: { ...tip, callbacks: { label: (c) => ` PETR4 fechamento: ${brl(c.parsed.y)}` } } },
      scales: { x: { display: false }, y: { ...fitY, ticks: { color: INK.muted, maxTicksLimit: 4, callback: (v) => brl(v) }, grid: { color: INK.grid }, border: { display: false } } },
    },
  });
  charts["c-exp-strip"] = new Chart(s, {
    type: "bar",
    data: {
      labels: ids.map(label),
      datasets: ids.map((id) => ({
        label: label(id), grouped: false, barThickness: 16, borderRadius: 2, borderSkipped: false, backgroundColor: color(id),
        data: spans(a.participants[id].long).map(([f, t]) => ({ x: [f - 0.5, t + 0.5], y: label(id), f, t })),
      })),
    },
    options: {
      indexAxis: "y", responsive: true, maintainAspectRatio: false, animation: false,
      plugins: { legend: { display: false }, tooltip: { ...tip, callbacks: { title: (c) => c[0].dataset.label, label: (c) => ` comprado ${m.dates[c.raw.f]} → ${m.dates[c.raw.t]} (${c.raw.t - c.raw.f + 1} fechamentos)` } } },
      scales: {
        x: { type: "linear", min: 0, max: m.dates.length - 1, ticks: { color: INK.muted, maxTicksLimit: 9, callback: (v) => m.dates[v] ?? "" }, grid: { color: INK.grid }, border: { color: INK.axis } },
        y: { ...fitY, ticks: { color: INK.text2 }, grid: { display: false } },
      },
    },
  });
}

function renderAgents() {
  const el = document.getElementById("tab-agents");
  if (!state.data) return (el.innerHTML = "");
  const head = `<h2>Explicabilidade Multiagente</h2>
    <p class="note">Três conceitos distintos para cada camada: <b>1 · foi chamada</b>, <b>2 · produziu uma decisão</b> e <b>3 · alterou a trajetória financeira</b>, isto é, a ordem executada difere da que o consenso técnico sozinho implicaria dada a posição em t. Todas as contagens vêm de decisions.jsonl, llm_calls.jsonl e trades.csv selados.</p>`;
  if (!analysisGate(el, head)) return;
  const a = A(), runs = LLM.filter((id) => a.agents[id]), g = (id) => a.agents[id];
  const lines = (f) => `<div class="lines">${runs.map((id) => `<div>${sw(id)}<span class="muted">${id}</span> ${f(g(id))}</div>`).join("")}</div>`;
  const concepts = table(
    [
      { label: "Camada", render: (r) => `<b>${r.layer}</b><div class="muted">${r.sub}</div>` },
      { label: "1 · Chamada", render: (r) => lines(r.called) },
      { label: "2 · Produziu decisão", render: (r) => lines(r.decided) },
      { label: "3 · Alterou a trajetória", render: (r) => lines(r.changed) },
    ],
    [
      { layer: "Technical Analysts", sub: "5 analistas · consenso ≥ 3/5", called: (x) => `${int(x.technical.calls)} chamadas · ${x.sessions} sessões`, decided: (x) => `${x.sessions} consensos · ${int(x.technical.valid_votes)} votos válidos`, changed: (x) => `<b>${x.technical.implied_orders}</b> sessões originaram ordem` },
      { layer: "Risk Manager", sub: "regras duras + Risk LLM", called: (x) => `${x.risk.evaluated} avaliações · ${x.risk.llm_calls} chamadas LLM`, decided: (x) => `${x.risk.evaluated - x.risk.vetoes} aprovações · ${x.risk.vetoes} vetos`, changed: (x) => `<b>${x.risk.vetoes_effective}</b> vetos efetivos · ${x.risk.vetoes - x.risk.vetoes_effective} sem efeito` },
      { layer: "Portfolio Manager", sub: "LLM; MANTER resolvido por regra", called: (x) => `${x.portfolio.called} chamadas`, decided: (x) => `${Object.entries(x.portfolio.decisions).map(([k, v]) => `${esc(k)} ${v}`).join(" · ")}`, changed: (x) => `<b>${x.portfolio.changed_effective}</b> ordens alteradas · ${x.portfolio.changed} divergências do consenso` },
      { layer: "Execução", sub: "abertura de t+1", called: () => "—", decided: (x) => `${x.orders.executed} ordens executadas`, changed: (x) => `<b>${x.orders.differs_from_consensus}</b> ordens diferentes da implicada` },
    ],
  );
  const inert = runs.every((id) => g(id).risk.vetoes_effective === 0 && g(id).portfolio.changed_effective === 0 && g(id).orders.differs_from_consensus === 0);
  const fired = new Set(runs.flatMap((id) => g(id).risk.rules.map((r) => r.rule)));
  const untested = ["DRAWDOWN", "VOLATILITY"].filter((r) => !fired.has(r));
  const callout = `<div class="callout">
    <p>${tag("f")} ${inert
      ? `<b>Nesta janela, Risk Manager e Portfolio Manager foram chamados e produziram decisões, mas não alteraram nenhuma ordem executada</b> em ${runs.join(", ")}: nenhuma contribuição incremental observada. Os vetos (${runs.map((id) => g(id).risk.vetoes).join(" / ")}) ocorreram em COMPRA com a carteira já no alvo; o PM seguiu o consenso em ${runs.map((id) => `${g(id).portfolio.followed}/${g(id).portfolio.called}`).join(", ")} chamadas. A trajetória financeira foi função do consenso técnico e do sizing 0%/100%.`
      : "Há sessões em que Risk ou PM alteraram a ordem executada; ver a coluna 3."}</p>
    ${untested.length ? `<p>${tag("l")} As regras ${untested.join(" e ")} nunca dispararam; a Validation não traz evidência sobre o efeito delas.</p>` : ""}
    <p>${tag("h")} Se essas camadas agiriam em outro regime de mercado (drawdown > 25% sob consenso COMPRA, volatilidade > 50%) não pode ser afirmado com esta janela.</p></div>`;
  const run = runs.includes(state.agentRun) ? state.agentRun : runs[0], x = g(run);
  const picks = runs.map((id) => `<button class="pick" data-agent-run="${id}" aria-pressed="${id === run}">${sw(id)}${esc(label(id))}</button>`).join("");
  const voteRows = [...Object.entries(x.technical.analysts).map(([k, v]) => ({ name: `Analista ${k}`, v })), { name: "Consenso", v: x.technical.consensus }];
  const tot = (v) => (v.COMPRA || 0) + (v.VENDA || 0) + (v.MANTER || 0);
  const voteTable = table(
    [{ label: "", render: (r) => esc(r.name) }, ...["COMPRA", "VENDA", "MANTER"].map((k) => ({ label: k, n: 1, render: (r) => `${r.v[k] || 0} <span class="muted">${pct((r.v[k] || 0) / tot(r.v), 1)}</span>` }))],
    voteRows,
  );
  const margins = table(
    [{ label: "Run", render: (id) => `${sw(id)} ${id}` }, ...["5/5", "4/5", "3/5", "sem maioria"].map((k) => ({ label: k, n: 1, render: (id) => g(id).technical.margins[k] || 0 })), { label: "Consenso C/V/M", n: 1, render: (id) => ["COMPRA", "VENDA", "MANTER"].map((k) => g(id).technical.consensus[k] || 0).join(" / ") }],
    runs,
  );
  const c = a.cross_runs;
  const cross = c ? `<p style="margin-bottom:10px">${tag("f")} ${c.outcome_divergent} das ${c.sessions} sessões tiveram resultado técnico diferente entre os três runs; em <b>${c.order_divergent}</b> a ordem executada diferiu.</p>` + table(
    [
      { label: "Par", render: (r) => esc(r.pair) },
      { label: "Mesmo voto", n: 1, render: (r) => `${int(r.same_votes)}/${int(r.votes)} <span class="muted">${pct(r.same_votes / r.votes, 1)}</span>` },
      { label: "Contagens diferentes", n: 1, render: (r) => r.vote_counts_divergent },
      { label: "Resultado diferente", n: 1, render: (r) => r.outcome_divergent },
      { label: "Ordem diferente", n: 1, render: (r) => r.order_divergent },
      { label: "equity/trades", render: (r) => (r.identical_equity_and_trades ? chip("IDÊNTICOS (bytes)") : "distintos") },
    ],
    c.pairs,
  ) + `<p class="muted" style="margin-top:8px">Trajetórias financeiras idênticas com chamadas operacionalmente independentes (sem reuso de respostas; independência estatística não testada): as divergências caíram em sessões em que nenhuma alternativa muda a posição (VENDA × MANTER em caixa, COMPRA × MANTER já comprado).</p>` : empty("Requer ao menos dois runs selados.");
  const ruleKeys = [...new Set(runs.flatMap((id) => g(id).risk.rules.map((r) => `${r.source}|${r.rule ?? ""}|${r.verdict}`)))];
  const risk = table(
    [
      { label: "Fonte · regra · veredito", render: (k) => { const [s, r, v] = k.split("|"); return `<span class="mono">${esc(s)}${r ? ` · ${esc(r)}` : ""}</span> ${chip(v)}`; } },
      ...runs.map((id) => ({ label: id, n: 1, render: (k) => g(id).risk.rules.find((r) => `${r.source}|${r.rule ?? ""}|${r.verdict}` === k)?.count ?? 0 })),
    ],
    ruleKeys,
  ) + `<p class="muted" style="margin-top:8px">Risk LLM (COMPRA com carteira em caixa): ${runs.map((id) => `${id} ${g(id).risk.llm_approved}/${g(id).risk.llm_calls} aprovações`).join(" · ")}.</p>`;
  const flowKeys = [...new Set(runs.flatMap((id) => g(id).flow.map((f) => `${f.technical}|${f.final}|${f.executed}`)))].sort();
  const flow = table(
    [
      { label: "Sinal técnico", render: (k) => sig(k.split("|")[0]) },
      { label: "Decisão final (Risk/PM)", render: (k) => { const v = k.split("|")[1]; return v === "VETADO" ? chip("VETADO pelo Risk") : sig(v); } },
      { label: "Ação executada", render: (k) => { const v = k.split("|")[2]; return SIDE[v] ? `<b class="${v === "BUY" ? "up" : "down"}">${SIDE[v]}</b>` : `<span class="muted">nenhuma ordem</span>`; } },
      ...runs.map((id) => ({ label: id, n: 1, render: (k) => g(id).flow.find((f) => `${f.technical}|${f.final}|${f.executed}` === k)?.count ?? 0 })),
    ],
    flowKeys,
  );
  el.innerHTML = `${head}${callout}
    ${card("Chamado · decidiu · alterou", concepts)}
    <div class="grid g-2" style="margin-top:16px">
      ${card("Votos por analista", `<div class="row">${picks}</div><div class="legend">${["COMPRA", "VENDA", "MANTER"].map((k) => `<span><i class="swatch" style="background:${SIG[k]}"></i>${k}</span>`).join("")}</div><div class="chart sm"><canvas id="c-votes"></canvas></div><div style="margin-top:10px">${voteTable}</div>`)}
      ${card("Frequência de consenso (maioria vencedora)", margins)}
    </div>
    <div style="margin-top:16px">${card("Divergência entre L01 / L02 / L03", cross)}</div>
    <div class="grid g-2" style="margin-top:16px">
      ${card("Sinal técnico → decisão final → ação executada", flow)}
      ${card("Risk Manager · vereditos por fonte", risk)}
    </div>`;
  charts["c-votes"]?.destroy();
  charts["c-votes"] = new Chart(document.getElementById("c-votes"), {
    type: "bar",
    data: { labels: voteRows.map((r) => r.name), datasets: ["COMPRA", "VENDA", "MANTER"].map((k) => ({ label: k, data: voteRows.map((r) => r.v[k] || 0), backgroundColor: SIG[k], borderColor: INK.surface, borderWidth: { right: 2 }, borderSkipped: false, barThickness: 18 })) },
    options: {
      indexAxis: "y", responsive: true, maintainAspectRatio: false, animation: { duration: 300 },
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: (q) => ` ${q.dataset.label}: ${q.parsed.x} (${pct(q.parsed.x / tot(voteRows[q.dataIndex].v), 1)})` } } },
      scales: { x: { stacked: true, ticks: { color: INK.muted }, grid: { color: INK.grid }, border: { color: INK.axis } }, y: { stacked: true, ticks: { color: INK.text2 }, grid: { display: false } } },
    },
  });
}

function render() {
  renderBanner();
  ({ overview: renderOverview, decisions: renderDecisions, compare: renderCompare, agents: renderAgents, experiments: renderExperiments, audit: renderAudit })[state.tab]();
}

// ── events ──────────────────────────────────────────────────────────────────
document.querySelectorAll("nav [data-tab]").forEach((b) => b.addEventListener("click", () => {
  state.tab = b.dataset.tab;
  history.replaceState(null, "", `#${state.source}/${state.tab}`);
  document.querySelectorAll("nav [data-tab]").forEach((x) => x.setAttribute("aria-selected", x === b));
  document.querySelectorAll("main section").forEach((sec) => (sec.hidden = sec.id !== `tab-${state.tab}`));
  if (state.tab === "audit" && !state.detail) return loadDetail();
  render();
  if (["decisions", "compare", "agents"].includes(state.tab) && !state.data?.synthetic) loadAnalysis();
}));
document.querySelectorAll("[data-source]").forEach((b) => b.addEventListener("click", () => setSource(b.dataset.source)));
document.addEventListener("click", (e) => {
  const f = e.target.closest("[data-focus]");
  if (f) { state.focus = f.dataset.focus; renderOverview(); }
  const a = e.target.closest("[data-audit]");
  if (a) { state.auditRun = a.dataset.audit; loadDetail(); }
  const rt = e.target.closest("[data-run-toggle]");
  if (rt) { const id = rt.dataset.runToggle; state.runsOn.has(id) ? state.runsOn.delete(id) : state.runsOn.add(id); renderDecisions(); }
  const tg = e.target.closest("[data-toggle]");
  if (tg) { state[tg.dataset.toggle] = !state[tg.dataset.toggle]; renderDecisions(); }
  const dr = e.target.closest("[data-drun]");
  if (dr) { Object.assign(state, { cycle: null }); loadDecision(dr.dataset.drun, state.decision?.session || A().participants[dr.dataset.drun].trades[0].decision_session); renderDecisions(); }
  const ss = e.target.closest("[data-session]");
  if (ss?.dataset.session) loadDecision(state.dRun, ss.dataset.session);
  const ar = e.target.closest("[data-agent-run]");
  if (ar) { state.agentRun = ar.dataset.agentRun; renderAgents(); }
});
document.addEventListener("change", (e) => {
  if (e.target.id !== "session-pick" || !e.target.value) return;
  // weekends/holidays snap to the next decision session
  const day = A()?.market.dates.slice(0, -1).find((d) => d >= e.target.value);
  if (day) loadDecision(state.dRun, day);
});
// Deep link: #demo/compare, #provisional/experiments, ...
const [hashSource, hashTab] = location.hash.slice(1).split("/");
document.querySelector(`[data-source="${hashSource}"]`)?.click();
document.querySelector(`nav [data-tab="${hashTab}"]`)?.click();
if (!hashSource || !document.querySelector(`[data-source="${hashSource}"]`)) load();
