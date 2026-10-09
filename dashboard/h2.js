/* H2 v6 dashboard — thin client. Every number arrives computed from the backend;
   this file only formats, draws and navigates. Demo and real payloads are never
   merged: a source switch replaces the whole state. */

const LLM = ["L01", "L02", "L03"];
const BENCH = ["buy_and_hold", "sma_regime_h2_proposed", "bollinger_state_h2_proposed"];
const css = getComputedStyle(document.documentElement);
const color = (id) => css.getPropertyValue(`--s-${id}`).trim();
const INK = { text2: "#c3c2b7", muted: "#898781", grid: "#2c2c2a", axis: "#383835", surface: "#1a1a19" };

const state = { tab: "overview", source: "provisional", status: null, data: null, focus: "L01", auditRun: "L01", detail: null, trace: null, session: null };
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
  const cls = /BLOQUEADO|INTERROMPIDA|INVALID|NOT_ESTIMABLE|ERRO/.test(t) ? "bad"
    : /EXECUÇÃO|PENDENTE|PENDING|STARTED|AUSENTE|NÃO APROVADO|NOT APPROVED/.test(t) ? "warn"
    : /COMPLETE|SELADA|CONCLU|REUSED|VALID|PRESENTE/.test(t) ? "good"
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
async function get(path) {
  const r = await fetch(path, { cache: "no-store" });
  return r.ok ? r.json() : null;
}
async function load() {
  const source = state.source;
  const [status, data] = await Promise.all([get("/api/h2/status"), get(`/api/h2/validation?source=${source}`)]);
  if (source !== state.source) return; // a newer switch won
  state.status = status;
  state.data = data;
  render();
  const running = data?.state === "EM EXECUÇÃO";
  document.getElementById("live-dot").classList.toggle("on", running);
  document.getElementById("live-text").textContent = running ? "ao vivo · 10 s" : `atualizado ${new Date().toLocaleTimeString("pt-BR")}`;
  clearTimeout(state.timer);
  if (running) state.timer = setTimeout(load, 10000);
}
async function loadDetail() {
  state.detail = await get(`/api/h2/run?source=${state.source}&run=${state.auditRun}`);
  state.trace = null; state.session = null;
  renderAudit();
}
async function loadTrace(session) {
  state.session = session;
  state.trace = await get(`/api/h2/trace?source=${state.source}&run=${state.auditRun}&session=${session}`);
  renderAudit();
}

// ── charts ──────────────────────────────────────────────────────────────────
function lineChart(id, dates, series, { percent = false, money = false } = {}) {
  charts[id]?.destroy();
  const el = document.getElementById(id);
  if (!el) return;
  const fmt = (v) => (percent ? pct(v, 1) : money ? brl(v) : num(v));
  charts[id] = new Chart(el, {
    type: "line",
    data: {
      labels: dates,
      datasets: series.map((s) => ({
        label: s.label, data: s.values, borderColor: color(s.id), backgroundColor: color(s.id),
        borderWidth: 2, borderDash: BENCH.includes(s.id) ? [6, 4] : [], pointRadius: 0, pointHoverRadius: 4,
        pointHoverBorderColor: INK.surface, pointHoverBorderWidth: 2, tension: 0,
      })),
    },
    options: {
      responsive: true, maintainAspectRatio: false, animation: { duration: 400 },
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: { backgroundColor: "#222220", borderColor: "rgba(255,255,255,.12)", borderWidth: 1, titleColor: "#fff", bodyColor: INK.text2, padding: 10, callbacks: { label: (c) => ` ${c.dataset.label}: ${fmt(c.parsed.y)}` } },
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
  if (!d) return (el.innerHTML = `<div class="banner info">API indisponível — inicie <code>python dashboard/server.py</code>.</div>`);
  if (d.synthetic) return (el.innerHTML = `<div class="banner demo">▨ ${esc(d.banner)} — valores fictícios gerados para prévia visual; não são resultados do experimento.</div>`);
  if (d.source === "provisional") return (el.innerHTML = `<div class="banner prov">! Execução provisória autorizada somente pelo autor (OA-1) — não é experimento academicamente ratificado. Estado: ${esc(d.state)}</div>`);
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
  if (d.curves) lineChart("c-overview", d.curves.dates, curveSeries([...LLM, "buy_and_hold"]), { money: true });
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
          ...spreads.map((sp) => ({ label: `${sp} bps · Sharpe`, n: 1, render: (r) => { const c = d.costs[sp]?.rows.find((x) => x.id === r.id); return !c ? "—" : c.sharpe == null ? `<span class="na" title="${esc(c.status)} ${esc(c.reason || "")}">N/A — replay inválido</span>` : num(c.sharpe, 3); } })),
        ],
        ids.map(part),
      ) + `<div class="row" style="margin-top:12px">${spreads.map((sp) => { const x = d.costs[sp]?.statistics; return `<span class="chip">${sp} bps · Δ ${x ? signed(x.delta, (v) => num(v, 3)) : '<span class="na">N/A (sem agregação de subconjunto)</span>'}</span>`; }).join("")}</div>`
    : empty("Sensibilidade 0/5/10/20 bps disponível após cost_closure.json.");
  el.innerHTML = `
    <h2>H2 v6 × Buy & Hold × SMA Regime × Bollinger Estado</h2>
    ${card("Patrimônio", d.curves ? `${legend(ids)}<div class="chart"><canvas id="c-equity"></canvas></div>` : empty("Sem curvas seladas."))}
    <div class="grid g-2" style="margin-top:16px">
      ${card("Drawdown", d.curves ? `${legend(ids)}<div class="chart sm"><canvas id="c-dd"></canvas></div>` : empty("Sem curvas seladas."))}
      ${card("Sharpe por participante", d.curves ? `<div class="chart sm"><canvas id="c-sharpe"></canvas></div>` : empty("Sem métricas."))}
    </div>
    <div style="margin-top:16px">${card("Métricas", metricTable)}</div>
    <div class="grid g-2" style="margin-top:16px">${card("Comparação dos três runs", runs)}${card("Sensibilidade de custos", costs)}</div>`;
  if (d.curves) {
    lineChart("c-equity", d.curves.dates, curveSeries(ids), { money: true });
    lineChart("c-dd", d.curves.dates, curveSeries(ids, "drawdown"), { percent: true });
    barChart("c-sharpe", ids.map(part).filter((p) => p.metrics).map((p) => ({ id: p.id, label: p.label, value: p.metrics.sharpe })));
  }
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
    : empty(det ? "Sem decisões LLM (benchmark determinístico)." : "Run não selado nesta fonte.");
  const tr = state.trace;
  const traceHtml = tr
    ? tr.calls.length
      ? tr.calls.map((c) => `<div class="card" style="margin-bottom:10px;padding:12px"><div class="row" style="margin-bottom:6px">${chip(c.status === "ok" ? "VALID" : `ERRO ${c.error_type || ""}`)}<b>${esc({ technical_analyst: "Technical", risk_manager: "Risk", portfolio_manager: "Portfolio" }[c.stage] || c.stage)}</b>${c.analyst_id ? `analista ${c.analyst_id}` : ""}<span style="color:var(--muted)">seq ${c.sequence} · ${num(c.duration_ms / 1000, 1)} s · tentativas ${c.attempt_count ?? "—"} · tokens ${c.token_usage?.prompt_tokens ?? "—"}/${c.token_usage?.completion_tokens ?? "—"}</span></div><pre>${esc(JSON.stringify(c.validated_response ?? c.error_message, null, 2))}</pre>${c.technical_evidence ? `<details><summary style="cursor:pointer;color:var(--muted);font-size:12px">evidência técnica</summary><pre>${esc(JSON.stringify(c.technical_evidence, null, 2))}</pre></details>` : ""}<details><summary style="cursor:pointer;color:var(--muted);font-size:12px">prompt do usuário</summary><pre>${esc(c.user_prompt)}</pre></details></div>`).join("")
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

function render() {
  renderBanner();
  ({ overview: renderOverview, experiments: renderExperiments, compare: renderCompare, audit: renderAudit })[state.tab]();
}

// ── events ──────────────────────────────────────────────────────────────────
document.querySelectorAll("nav [data-tab]").forEach((b) => b.addEventListener("click", () => {
  state.tab = b.dataset.tab;
  history.replaceState(null, "", `#${state.source}/${state.tab}`);
  document.querySelectorAll("nav [data-tab]").forEach((x) => x.setAttribute("aria-selected", x === b));
  document.querySelectorAll("main section").forEach((sec) => (sec.hidden = sec.id !== `tab-${state.tab}`));
  if (state.tab === "audit" && !state.detail) return loadDetail();
  render();
}));
document.querySelectorAll("[data-source]").forEach((b) => b.addEventListener("click", () => {
  state.source = b.dataset.source;
  history.replaceState(null, "", `#${state.source}/${state.tab}`);
  document.querySelectorAll("[data-source]").forEach((x) => x.setAttribute("aria-pressed", x === b));
  Object.assign(state, { data: null, detail: null, trace: null, session: null }); // never mix sources
  load().then(() => state.tab === "audit" && loadDetail());
}));
document.addEventListener("click", (e) => {
  const f = e.target.closest("[data-focus]");
  if (f) { state.focus = f.dataset.focus; renderOverview(); }
  const a = e.target.closest("[data-audit]");
  if (a) { state.auditRun = a.dataset.audit; loadDetail(); }
});
// Deep link: #demo/compare, #provisional/experiments, ...
const [hashSource, hashTab] = location.hash.slice(1).split("/");
document.querySelector(`[data-source="${hashSource}"]`)?.click();
document.querySelector(`nav [data-tab="${hashTab}"]`)?.click();
if (!hashSource || !document.querySelector(`[data-source="${hashSource}"]`)) load();
