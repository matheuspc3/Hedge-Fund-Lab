/**
 * Hedge-fund-lab Dashboard
 * Dashboard completo: análise por ativo + portfólio multi-ativo
 *
 * Carrega data.json e renderiza:
 *   - Gráfico Preço + SMA + Bollinger (Chart.js)
 *   - Gráfico RSI com bandas 30/70
 *   - Gráfico MACD (linhas + histograma)
 *   - Cards de resumo e estatísticas
 *   - Tabela de dados
 *   - Alternância entre 10 tickers
 *   - Portfolio: equity curves comparativas
 *   - Portfolio: alocação (pizza)
 *   - Portfolio: tabela de métricas
 */

/* ═══════════════════════════════════════════════
   State
   ═══════════════════════════════════════════════ */
const STATE = {
    data: null,
    activeTicker: "PETR4.SA",
    charts: {},
};

/* ═══════════════════════════════════════════════
   Colors
   ═══════════════════════════════════════════════ */
const COLORS = {
    price: "#3b82f6",
    sma50: "#f59e0b",
    sma200: "#ef4444",
    bbUpper: "rgba(59, 130, 246, 0.25)",
    bbLower: "rgba(59, 130, 246, 0.25)",
    bbFill: "rgba(59, 130, 246, 0.06)",
    rsi: "#a855f7",
    macd: "#22c55e",
    signal: "#ef4444",
    histUp: "rgba(34, 197, 94, 0.6)",
    histDown: "rgba(239, 68, 68, 0.6)",
    strategies: [
        "#3b82f6", "#22c55e", "#f59e0b", "#ef4444", "#a855f7",
        "#06b6d4", "#ec4899", "#14b8a6",
    ],
    allocationPalette: [
        "#3b82f6", "#22c55e", "#f59e0b", "#ef4444", "#a855f7",
        "#06b6d4", "#ec4899", "#14b8a6", "#eab308", "#f97316",
    ],
};

// Registra plugin de anotação se disponível
if (typeof ChartAnnotation !== "undefined") {
    Chart.register(ChartAnnotation);
}

/* ═══════════════════════════════════════════════
   Tab switching
   ═══════════════════════════════════════════════ */
function setupTabs() {
    document.querySelectorAll(".tab").forEach((btn) => {
        btn.addEventListener("click", () => {
            // Desativa todas
            document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
            document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));
            // Ativa selecionada
            btn.classList.add("active");
            const tabName = btn.dataset.tab;
            document.getElementById("tab-" + tabName).classList.add("active");
            // Renderiza o conteudo da aba recem-ativada apos breve delay
            // para garantir que o DOM (display:block) ja foi aplicado.
            // Chart.js precisa de canvas visivel para medir dimensoes.
            setTimeout(() => {
                if (tabName === "portfolio" && STATE.data && STATE.data.portfolio) {
                    safe(() => renderPortfolioDashboard(), "Portfolio");
                } else if (tabName === "analise" && STATE.data) {
                    safe(() => updateDashboard(), "Analise");
                }
            }, 100);
        });
    });
}

/* ═══════════════════════════════════════════════
   Data Loading
   ═══════════════════════════════════════════════ */
async function loadData() {
    const resp = await fetch("data.json");
    if (!resp.ok) throw new Error(`HTTP ${resp.status}: ${resp.statusText}`);
    STATE.data = await resp.json();
    return STATE.data;
}

function getActiveAsset() {
    return STATE.data.ativos.find((a) => a.ticker === STATE.activeTicker);
}

/* ═══════════════════════════════════════════════
   Summary Cards
   ═══════════════════════════════════════════════ */
function renderSummary(asset) {
    const last = asset.ultimo;
    if (!last) return;

    setVal("ultimo-fechamento", last.fechamento, "neutral");
    setVal("sma50-valor", last.sma_50, "neutral");
    setVal("sma200-valor", last.sma_200, "neutral");

    const el = document.getElementById("tendencia");
    if (last.sma_50 != null && last.sma_200 != null) {
        if (last.sma_50 > last.sma_200) {
            el.textContent = "ALTA ↑";
            el.className = "value positive";
        } else {
            el.textContent = "BAIXA ↓";
            el.className = "value negative";
        }
    } else {
        el.textContent = "—";
        el.className = "value neutral";
    }

    const rsiEl = document.getElementById("rsi-valor");
    if (last.rsi != null) {
        rsiEl.textContent = last.rsi.toFixed(1);
        rsiEl.className =
            "value " + (last.rsi > 70 ? "overbought" : last.rsi < 30 ? "oversold" : "neutral");
    } else {
        rsiEl.textContent = "—";
        rsiEl.className = "value neutral";
    }

    const macdEl = document.getElementById("macd-valor");
    if (last.macd != null) {
        macdEl.textContent = last.macd.toFixed(4);
        macdEl.className = "value " + (last.macd > 0 ? "positive" : "negative");
    } else {
        macdEl.textContent = "—";
        macdEl.className = "value neutral";
    }
}

function setVal(id, val, cls) {
    const el = document.getElementById(id);
    el.textContent = val != null ? (typeof val === "number" ? val.toFixed(2) : val) : "—";
    el.className = "value " + cls;
}

/* ═══════════════════════════════════════════════
   Stats (Sharpe, Vol, MaxDD)
   ═══════════════════════════════════════════════ */
function renderStats(asset) {
    const prices = asset.data.map((d) => d.fechamento).filter((p) => p != null);
    if (prices.length < 2) return;

    const returns = [];
    for (let i = 1; i < prices.length; i++) {
        returns.push((prices[i] - prices[i - 1]) / prices[i - 1]);
    }

    const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
    const variance = returns.reduce((s, r) => s + (r - mean) ** 2, 0) / returns.length;
    const std = Math.sqrt(variance);

    const sharpe = std > 0 ? (mean / std) * Math.sqrt(252) : 0;

    let peak = prices[0];
    let maxDD = 0;
    for (const p of prices) {
        if (p > peak) peak = p;
        const dd = (p - peak) / peak;
        if (dd < maxDD) maxDD = dd;
    }

    document.getElementById("sharpe-valor").textContent = sharpe.toFixed(3);
    document.getElementById("sharpe-valor").className =
        "value " + (sharpe > 0.5 ? "positive" : sharpe > 0 ? "neutral" : "negative");

    document.getElementById("vol-valor").textContent =
        (std * Math.sqrt(252) * 100).toFixed(2) + "%";
    document.getElementById("vol-valor").className = "value neutral";

    document.getElementById("maxdd-valor").textContent = (maxDD * 100).toFixed(2) + "%";
    document.getElementById("maxdd-valor").className = "value negative";

    document.getElementById("pregoes-valor").textContent = prices.length.toLocaleString();
}

/* ═══════════════════════════════════════════════
   Helpers
   ═══════════════════════════════════════════════ */
function clean(arr) {
    return arr.map((v) => (v != null ? v : undefined));
}

function destroy(key) {
    if (STATE.charts[key]) {
        STATE.charts[key].destroy();
        delete STATE.charts[key];
    }
}

/* ═══════════════════════════════════════════════
   Chart: Price + SMA + Bollinger
   ═══════════════════════════════════════════════ */
function renderPriceChart(asset) {
    const ctx = document.getElementById("chart-price").getContext("2d");
    const dates = asset.data.map((d) => d.Data);
    const price = clean(asset.data.map((d) => d.fechamento));
    const sma50 = clean(asset.data.map((d) => d.sma_50));
    const sma200 = clean(asset.data.map((d) => d.sma_200));
    const bbU = clean(asset.data.map((d) => d.bb_upper));
    const bbL = clean(asset.data.map((d) => d.bb_lower));

    destroy("price");

    STATE.charts.price = new Chart(ctx, {
        type: "line",
        data: {
            labels: dates,
            datasets: [
                { label: "Fechamento", data: price, borderColor: COLORS.price, borderWidth: 2, pointRadius: 0, pointHoverRadius: 4, fill: false, tension: 0.1 },
                { label: "SMA 50", data: sma50, borderColor: COLORS.sma50, borderWidth: 1.5, pointRadius: 0, borderDash: [5, 4], fill: false, tension: 0.1 },
                { label: "SMA 200", data: sma200, borderColor: COLORS.sma200, borderWidth: 1.5, pointRadius: 0, borderDash: [5, 4], fill: false, tension: 0.1 },
                { label: "BB Superior", data: bbU, borderColor: COLORS.bbUpper, borderWidth: 1, pointRadius: 0, fill: false, tension: 0.1 },
                { label: "BB Inferior", data: bbL, borderColor: COLORS.bbLower, borderWidth: 1, pointRadius: 0, fill: "-1", backgroundColor: COLORS.bbFill, tension: 0.1 },
            ],
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            interaction: { intersect: false, mode: "index" },
            plugins: {
                legend: { position: "top", labels: { color: "#94a3b8", font: { size: 10, family: "'JetBrains Mono', monospace" }, boxWidth: 14, padding: 12 } },
                tooltip: { backgroundColor: "#1a2332", titleColor: "#e2e8f0", bodyColor: "#94a3b8", borderColor: "#1e293b", borderWidth: 1, padding: 10, cornerRadius: 8 },
            },
            scales: {
                x: { ticks: { color: "#64748b", maxTicksLimit: 10, font: { size: 10 } }, grid: { color: "rgba(255,255,255,0.03)" } },
                y: { ticks: { color: "#64748b", font: { size: 10 } }, grid: { color: "rgba(255,255,255,0.03)" } },
            },
        },
    });
}

/* ═══════════════════════════════════════════════
   Chart: RSI
   ═══════════════════════════════════════════════ */
function renderRSIChart(asset) {
    const ctx = document.getElementById("chart-rsi").getContext("2d");
    const dates = asset.data.map((d) => d.Data);
    const rsi = clean(asset.data.map((d) => d.rsi));

    destroy("rsi");

    const config = {
        type: "line",
        data: {
            labels: dates,
            datasets: [
                { label: "RSI", data: rsi, borderColor: COLORS.rsi, borderWidth: 1.5, pointRadius: 0, pointHoverRadius: 4, fill: false, tension: 0.1 },
            ],
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            interaction: { intersect: false, mode: "index" },
            plugins: {
                legend: { display: false },
                tooltip: { backgroundColor: "#1a2332", titleColor: "#e2e8f0", bodyColor: "#94a3b8", borderColor: "#1e293b", borderWidth: 1, padding: 10, cornerRadius: 8 },
            },
            scales: {
                y: { min: 0, max: 100, ticks: { color: "#64748b", font: { size: 10 } }, grid: { color: "rgba(255,255,255,0.03)" } },
                x: { ticks: { color: "#64748b", maxTicksLimit: 8, font: { size: 10 } }, grid: { color: "rgba(255,255,255,0.03)" } },
            },
        },
    };

    if (typeof ChartAnnotation !== "undefined") {
        config.options.plugins.annotation = {
            annotations: {
                overbought: { type: "line", yMin: 70, yMax: 70, borderColor: "rgba(239,68,68,0.5)", borderWidth: 1, borderDash: [6, 4], label: { display: true, content: "Sobrecompra (70)", position: "start", font: { size: 9, family: "'JetBrains Mono', monospace" }, color: "#ef4444", backgroundColor: "transparent" } },
                oversold: { type: "line", yMin: 30, yMax: 30, borderColor: "rgba(34,197,94,0.5)", borderWidth: 1, borderDash: [6, 4], label: { display: true, content: "Sobrevenda (30)", position: "start", font: { size: 9, family: "'JetBrains Mono', monospace" }, color: "#22c55e", backgroundColor: "transparent" } },
            },
        };
    }

    STATE.charts.rsi = new Chart(ctx, config);
}

/* ═══════════════════════════════════════════════
   Chart: MACD
   ═══════════════════════════════════════════════ */
function renderMACDChart(asset) {
    const ctx = document.getElementById("chart-macd").getContext("2d");
    const dates = asset.data.map((d) => d.Data);
    const macd = clean(asset.data.map((d) => d.macd));
    const signal = clean(asset.data.map((d) => d.macd_sinal));
    const hist = clean(asset.data.map((d) => d.macd_hist));

    destroy("macd");

    const histClean = hist.map((v) => (v != null ? v : 0));

    STATE.charts.macd = new Chart(ctx, {
        type: "bar",
        data: {
            labels: dates,
            datasets: [
                { label: "MACD", data: macd, type: "line", borderColor: COLORS.macd, borderWidth: 1.5, pointRadius: 0, fill: false, tension: 0.1, order: 1 },
                { label: "Sinal", data: signal, type: "line", borderColor: COLORS.signal, borderWidth: 1.5, pointRadius: 0, fill: false, borderDash: [5, 4], tension: 0.1, order: 1 },
                { label: "Histograma", data: histClean, backgroundColor: histClean.map((v) => v >= 0 ? COLORS.histUp : COLORS.histDown), borderWidth: 0, borderRadius: 1, order: 2 },
            ],
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            interaction: { intersect: false, mode: "index" },
            plugins: {
                legend: { position: "top", labels: { color: "#94a3b8", font: { size: 10, family: "'JetBrains Mono', monospace" }, boxWidth: 14, padding: 12 } },
                tooltip: { backgroundColor: "#1a2332", titleColor: "#e2e8f0", bodyColor: "#94a3b8", borderColor: "#1e293b", borderWidth: 1, padding: 10, cornerRadius: 8 },
            },
            scales: {
                x: { ticks: { color: "#64748b", maxTicksLimit: 8, font: { size: 10 } }, grid: { color: "rgba(255,255,255,0.03)" } },
                y: { ticks: { color: "#64748b", font: { size: 10 } }, grid: { color: "rgba(255,255,255,0.03)" } },
            },
        },
    });
}

/* ═══════════════════════════════════════════════
   Table (ticker data)
   ═══════════════════════════════════════════════ */
function renderTable(asset) {
    const tbody = document.getElementById("data-table-body");
    const recent = asset.data.slice(-20).reverse();

    tbody.innerHTML = recent
        .map(
            (r) => `
        <tr>
            <td>${r.Data}</td>
            <td>${fmt(r.fechamento, 2)}</td>
            <td>${fmt(r.sma_50, 2)}</td>
            <td>${fmt(r.sma_200, 2)}</td>
            <td>${fmt(r.rsi, 1)}</td>
            <td>${fmt(r.macd, 4)}</td>
            <td>${r.volume != null ? r.volume.toLocaleString() : "—"}</td>
        </tr>`
        )
        .join("");
}

function fmt(val, decimals) {
    return val != null ? val.toFixed(decimals) : "—";
}

/* ═══════════════════════════════════════════════════════════════
   PORTFOLIO — Métricas Cards
   ═══════════════════════════════════════════════════════════════ */
function renderPortfolioMetrics() {
    const pf = STATE.data.portfolio;
    if (!pf) return;

    const container = document.getElementById("portfolio-metrics");
    const stratNames = Object.keys(pf.strategies);

    // Pega a melhor estratégia por Sharpe
    let best = { name: "", sharpe: -999 };
    for (const [name, data] of Object.entries(pf.strategies)) {
        if (data.metrics.sharpe != null && data.metrics.sharpe > best.sharpe) {
            best = { name, sharpe: data.metrics.sharpe };
        }
    }

    let html = "";
    for (const [name, data] of Object.entries(pf.strategies)) {
        const m = data.metrics;
        const cls = m.sharpe > 0.5 ? "positive" : m.sharpe > 0 ? "neutral" : "negative";
        html += `
        <div class="portfolio-metric-card ${name === best.name ? "highlight" : ""}">
            <div class="portfolio-metric-name">${name}</div>
            <div class="portfolio-metric-value ${cls}">${m.sharpe != null ? m.sharpe.toFixed(4) : "—"}</div>
            <div class="portfolio-metric-label">Sharpe</div>
            <div class="portfolio-metric-sub">
                Sortino: ${m.sortino != null ? m.sortino.toFixed(4) : "—"} ·
                Retorno: ${m.retorno_percent != null ? m.retorno_percent.toFixed(1) + "%" : "—"} ·
                DD: ${m.max_drawdown != null ? (m.max_drawdown * 100).toFixed(1) + "%" : "—"}
            </div>
        </div>`;
    }

    container.innerHTML = html;
}

/* ═══════════════════════════════════════════════════════════════
   PORTFOLIO — Equity Comparison Chart
   ═══════════════════════════════════════════════════════════════ */
function renderEquityComparisonChart() {
    const pf = STATE.data.portfolio;
    if (!pf) return;

    const ctx = document.getElementById("chart-portfolio-equity").getContext("2d");
    destroy("portfolio-equity");

    // Encontra a maior série de datas
    let maxLen = 0;
    let bestDates = [];
    for (const data of Object.values(pf.strategies)) {
        if (data.dates && data.dates.length > maxLen) {
            maxLen = data.dates.length;
            bestDates = data.dates;
        }
    }

    const datasets = [];
    let ci = 0;
    for (const [name, data] of Object.entries(pf.strategies)) {
        const color = COLORS.strategies[ci % COLORS.strategies.length];
        datasets.push({
            label: name,
            data: data.equity || [],
            borderColor: color,
            borderWidth: name.includes("Min Variance") || name.includes("Equal Weight") ? 2.5 : 1.5,
            borderDash: name.includes("Min Variance") || name.includes("Equal Weight") ? [] : [4, 3],
            pointRadius: 0,
            fill: false,
            tension: 0.1,
        });
        ci++;
    }

    STATE.charts["portfolio-equity"] = new Chart(ctx, {
        type: "line",
        data: { labels: bestDates, datasets },
        options: {
            responsive: true, maintainAspectRatio: false,
            interaction: { intersect: false, mode: "index" },
            plugins: {
                legend: { position: "top", labels: { color: "#94a3b8", font: { size: 10, family: "'JetBrains Mono', monospace" }, boxWidth: 14, padding: 12 } },
                tooltip: { backgroundColor: "#1a2332", titleColor: "#e2e8f0", bodyColor: "#94a3b8", borderColor: "#1e293b", borderWidth: 1, padding: 10, cornerRadius: 8, callbacks: { label: (ctx) => ctx.dataset.label + ": R$ " + ctx.parsed.y.toLocaleString("pt-BR", { minimumFractionDigits: 2 }) } },
            },
            scales: {
                x: { ticks: { color: "#64748b", maxTicksLimit: 8, font: { size: 10 } }, grid: { color: "rgba(255,255,255,0.03)" } },
                y: { ticks: { color: "#64748b", font: { size: 10 }, callback: (v) => "R$ " + v.toLocaleString("pt-BR") }, grid: { color: "rgba(255,255,255,0.03)" } },
            },
        },
    });
}

/* ═══════════════════════════════════════════════════════════════
   PORTFOLIO — Allocation Pie Chart
   ═══════════════════════════════════════════════════════════════ */
function renderAllocationChart(canvasId, weights, title) {
    const ctx = document.getElementById(canvasId).getContext("2d");
    destroy(canvasId);

    if (!weights || Object.keys(weights).length === 0) return;

    const labels = Object.keys(weights);
    const values = Object.values(weights);

    const colors = labels.map((_, i) => COLORS.allocationPalette[i % COLORS.allocationPalette.length]);

    STATE.charts[canvasId] = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderColor: "#111827",
                borderWidth: 2,
            }],
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { position: "right", labels: { color: "#94a3b8", font: { size: 10, family: "'JetBrains Mono', monospace" }, padding: 8 } },
                tooltip: {
                    backgroundColor: "#1a2332", titleColor: "#e2e8f0", bodyColor: "#94a3b8",
                    borderColor: "#1e293b", borderWidth: 1, padding: 10, cornerRadius: 8,
                    callbacks: {
                        label: (ctx) => {
                            const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                            const pct = ((ctx.parsed / total) * 100).toFixed(1);
                            return ctx.label + ": " + pct + "%";
                        },
                    },
                },
            },
        },
    });
}

function renderAllocationCharts() {
    const pf = STATE.data.portfolio;
    if (!pf) return;

    // Equal Weight allocation
    const ew = pf.strategies["Equal Weight"];
    if (ew && ew.latest_weights) {
        renderAllocationChart("chart-allocation", ew.latest_weights, "Equal Weight");
    }

    // Min Variance allocation
    const mv = pf.strategies["Min Variance"];
    if (mv && mv.latest_weights) {
        renderAllocationChart("chart-allocation-mv", mv.latest_weights, "Min Variance");
    }
}

/* ═══════════════════════════════════════════════════════════════
   PORTFOLIO — Comparison Table
   ═══════════════════════════════════════════════════════════════ */
function renderComparisonTable() {
    const pf = STATE.data.portfolio;
    if (!pf || !pf.comparison) return;

    const tbody = document.getElementById("comparison-table-body");

    tbody.innerHTML = pf.comparison
        .map((r) => {
            const sharpeCls = r.sharpe > 0.5 ? "positive" : r.sharpe > 0 ? "neutral" : "negative";
            const ddStr = r.max_drawdown != null ? (r.max_drawdown * 100).toFixed(2) + "%" : "—";
            const retStr = r.retorno_percent != null ? r.retorno_percent.toFixed(2) + "%" : "—";
            return `
            <tr>
                <td><strong>${r.estrategia}</strong></td>
                <td><span class="badge ${r.tipo === 'Portfólio (10 Ativos)' ? 'badge-portfolio' : 'badge-single'}">${r.tipo}</span></td>
                <td class="${sharpeCls}">${r.sharpe != null ? r.sharpe.toFixed(4) : "—"}</td>
                <td>${r.sortino != null ? r.sortino.toFixed(4) : "—"}</td>
                <td class="negative">${ddStr}</td>
                <td class="${r.retorno_percent > 0 ? 'positive' : 'negative'}">${retStr}</td>
                <td>${r.n_trades != null ? r.n_trades : "—"}</td>
            </tr>`;
        })
        .join("");
}

/* ═══════════════════════════════════════════════════════════════
   PORTFOLIO — Drawdown Comparison Chart
   ═══════════════════════════════════════════════════════════════ */
function renderDrawdownChart() {
    const pf = STATE.data.portfolio;
    if (!pf) return;

    const ctx = document.getElementById("chart-portfolio-drawdown").getContext("2d");
    destroy("portfolio-drawdown");

    // Encontra a maior série de datas
    let maxLen = 0;
    let bestDates = [];
    for (const data of Object.values(pf.strategies)) {
        if (data.drawdown && data.drawdown.length > maxLen) {
            maxLen = data.drawdown.length;
            bestDates = data.dates || [];
        }
    }

    const datasets = [];
    let ci = 0;
    for (const [name, data] of Object.entries(pf.strategies)) {
        const color = COLORS.strategies[ci % COLORS.strategies.length];
        datasets.push({
            label: name,
            data: data.drawdown || [],
            borderColor: color,
            borderWidth: 1.5,
            pointRadius: 0,
            fill: false,
            tension: 0.1,
        });
        ci++;
    }

    STATE.charts["portfolio-drawdown"] = new Chart(ctx, {
        type: "line",
        data: { labels: bestDates, datasets },
        options: {
            responsive: true, maintainAspectRatio: false,
            interaction: { intersect: false, mode: "index" },
            plugins: {
                legend: { position: "top", labels: { color: "#94a3b8", font: { size: 10, family: "'JetBrains Mono', monospace" }, boxWidth: 14, padding: 12 } },
                tooltip: {
                    backgroundColor: "#1a2332", titleColor: "#e2e8f0", bodyColor: "#94a3b8",
                    borderColor: "#1e293b", borderWidth: 1, padding: 10, cornerRadius: 8,
                    callbacks: {
                        label: (ctx) => ctx.dataset.label + ": " + (ctx.parsed.y * 100).toFixed(2) + "%",
                    },
                },
            },
            scales: {
                x: { ticks: { color: "#64748b", maxTicksLimit: 8, font: { size: 10 } }, grid: { color: "rgba(255,255,255,0.03)" } },
                y: {
                    ticks: { color: "#64748b", font: { size: 10 }, callback: (v) => (v * 100).toFixed(0) + "%" },
                    grid: { color: "rgba(255,255,255,0.03)" },
                },
            },
        },
    });
}

/* ═══════════════════════════════════════════════════════════════
   PORTFOLIO — Risco × Retorno Scatter Chart
   ═══════════════════════════════════════════════════════════════ */
function renderScatterChart() {
    const pf = STATE.data.portfolio;
    if (!pf || !pf.scatter_data) return;

    const ctx = document.getElementById("chart-risk-return").getContext("2d");
    destroy("risk-return");

    const points = pf.scatter_data;
    const datasets = [
        {
            label: "Estratégias",
            data: points.map((p) => ({
                x: p.volatilidade || 0,
                y: p.retorno || 0,
                estrategia: p.estrategia,
                tipo: p.tipo,
                sharpe: p.sharpe,
            })),
            backgroundColor: points.map((p) => {
                const s = p.sharpe;
                if (s == null) return "rgba(148, 163, 184, 0.6)";
                if (s > 0.5) return "rgba(34, 197, 94, 0.7)";
                if (s > 0) return "rgba(250, 204, 21, 0.7)";
                return "rgba(239, 68, 68, 0.7)";
            }),
            borderColor: points.map((p) => {
                const s = p.sharpe;
                if (s == null) return "rgba(148, 163, 184, 1)";
                if (s > 0.5) return "rgba(34, 197, 94, 1)";
                if (s > 0) return "rgba(250, 204, 21, 1)";
                return "rgba(239, 68, 68, 1)";
            }),
            borderWidth: 2,
            pointRadius: 8,
            pointHoverRadius: 12,
        },
    ];

    STATE.charts["risk-return"] = new Chart(ctx, {
        type: "scatter",
        data: { datasets },
        options: {
            responsive: true, maintainAspectRatio: false,
            interaction: { intersect: false, mode: "nearest" },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: "#1a2332", titleColor: "#e2e8f0", bodyColor: "#94a3b8",
                    borderColor: "#1e293b", borderWidth: 1, padding: 10, cornerRadius: 8,
                    callbacks: {
                        title: () => "",
                        beforeBody: (items) => items[0].raw.estrategia,
                        label: (ctx) => {
                            const r = ctx.raw;
                            return [
                                "Retorno: " + r.y.toFixed(2) + "%",
                                "Volatilidade: " + r.x.toFixed(2) + "%",
                                "Sharpe: " + (r.sharpe != null ? r.sharpe.toFixed(4) : "—"),
                                "Tipo: " + r.tipo,
                            ];
                        },
                    },
                },
            },
            scales: {
                x: {
                    title: { display: true, text: "Volatilidade (%)", color: "#94a3b8", font: { size: 11, family: "'JetBrains Mono', monospace" } },
                    ticks: { color: "#64748b", font: { size: 10 } },
                    grid: { color: "rgba(255,255,255,0.03)" },
                },
                y: {
                    title: { display: true, text: "Retorno Acumulado (%)", color: "#94a3b8", font: { size: 11, family: "'JetBrains Mono', monospace" } },
                    ticks: { color: "#64748b", font: { size: 10 } },
                    grid: { color: "rgba(255,255,255,0.03)" },
                },
            },
        },
    });
}

/* ═══════════════════════════════════════════════════════════════
   PORTFOLIO — Full render
   ═══════════════════════════════════════════════════════════════ */
function renderPortfolioDashboard() {
    safe(renderPortfolioMetrics, "Portfolio Metrics");
    safe(renderEquityComparisonChart, "Equity Comparison Chart");
    safe(renderDrawdownChart, "Drawdown Chart");
    safe(renderScatterChart, "Scatter Chart");
    safe(renderAllocationCharts, "Allocation Charts");
    safe(renderComparisonTable, "Comparison Table");
}

/* ═══════════════════════════════════════════════════════════════
   Safe render wrapper — mostra erro visível no dashboard
   ═══════════════════════════════════════════════════════════════ */
function safe(fn, name) {
    try {
        fn();
    } catch (err) {
        const msg = "[dashboard] Erro ao renderizar " + name + ": " + (err.message || err);
        console.warn(msg, err);
        const el = document.getElementById("error-message");
        if (el) {
            el.style.display = "block";
            el.innerHTML += `<div>⚠️ ${name}: ${err.message || err}</div>`;
        }
    }
}

/* ═══════════════════════════════════════════════════════════════
   Philosophy
   ═══════════════════════════════════════════════════════════════ */
function renderPhilosophy() {
    const el = document.getElementById("philosophy-text");
    if (!el) return;
    el.innerHTML = `
        <h2>Filosofia do Projeto</h2>
        <p>
            O <strong>Hedge-fund-lab</strong> é um laboratório quantitativo de backtesting
            baseado em <strong>sistemas multiagentes</strong>, desenvolvido como Trabalho de
            Conclusão de Curso no Cefet/RJ.
        </p>
        <p>
            <strong>Problema:</strong> O mercado financeiro contemporâneo impõe desafios como
            alta volatilidade, não estacionariedade das séries e risco de <em>overfitting</em> em
            backtesting.
        </p>
        <p>
            <strong>Solução:</strong> Combinar engenharia de dados (Prefect + PostgreSQL),
            estratégias clássicas de <em>benchmark</em> e uma <strong>arquitetura multiagente</strong>
            coordenada por LangGraph, com agentes especializados em
            <em>Análise Técnica</em>, <em>Gestão de Risco</em> e <em>Gestão de Portfólio</em>.
        </p>
        <p>
            <strong>Status atual:</strong> Pipeline de dados com 10 ativos, 5 estratégias de
            backtesting (Buy & Hold, SMA Cross, Bollinger Bands, Equal Weight, Mínima Variância)
            e dashboard interativo. Próxima etapa: sistema multiagente com LLMs.
        </p>
        <p style="margin-top:1rem;font-size:0.75rem;color:#64748b;">
            TCC de Lucas Pereira da Silva e Matheus Pereira de Carvalho · Orientação: Eduardo S. Ogasawara, D.Sc.
        </p>
    `;
}

/* ═══════════════════════════════════════════════════════════════
   Update all (ticker tab)
   ═══════════════════════════════════════════════════════════════ */
function updateDashboard() {
    const asset = getActiveAsset();
    if (!asset) return;

    const statusEl = document.getElementById("data-status");
    statusEl.textContent = "● Online";
    statusEl.className = "status online";

    document.getElementById("data-count").textContent =
        asset.total_dias.toLocaleString() + " pregões";

    safe(() => renderSummary(asset), "Summary");
    safe(() => renderStats(asset), "Stats");
    safe(() => renderPriceChart(asset), "Price Chart");
    safe(() => renderRSIChart(asset), "RSI Chart");
    safe(() => renderMACDChart(asset), "MACD Chart");
    safe(() => renderTable(asset), "Table");
}

/* ═══════════════════════════════════════════════════════════════
   Event Listeners
   ═══════════════════════════════════════════════════════════════ */
document.getElementById("ticker-select").addEventListener("change", (e) => {
    STATE.activeTicker = e.target.value;
    updateDashboard();
});

function setPeriodoInfo() {
    const asset = getActiveAsset();
    if (asset && asset.periodo) {
        document.getElementById("periodo-info").textContent =
            asset.periodo.inicio + " – " + asset.periodo.fim;
    }
}

/* ═══════════════════════════════════════════════════════════════
   Init
   ═══════════════════════════════════════════════════════════════ */
async function init() {
    try {
        await loadData();
        setupTabs();
        renderPhilosophy();
        setPeriodoInfo();

        // Portfolio e a aba principal (primeira) — usa setTimeout para garantir
        // que o DOM ja esteja visivel e os canvases tenham dimensoes.
        if (STATE.data && STATE.data.portfolio) {
            setTimeout(() => {
                safe(() => renderPortfolioDashboard(), "Portfolio (init)");
            }, 150);
        }

        // Analise por ativo fica em segundo plano ate clicar na aba
        updateDashboard();

        document.getElementById("loading").style.display = "none";
    } catch (err) {
        console.error("Erro fatal:", err);
        document.getElementById("loading").style.display = "none";
        const errEl = document.getElementById("error-message");
        if (errEl) {
            errEl.style.display = "block";
            errEl.textContent = "Erro ao carregar dados: " + err.message;
        }
    }
}

document.addEventListener("DOMContentLoaded", init);
