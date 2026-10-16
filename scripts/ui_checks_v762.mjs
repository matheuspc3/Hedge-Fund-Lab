// V7.6.2 browser checks (navigation, design system, contextual help, V1 safety,
// responsiveness). Real headless Chrome; GET requests only; no provider call.
import fs from "node:fs";
import path from "node:path";
import { PAGES, VIEWPORTS, session, unsafeRequests } from "./ui_cdp_v762.mjs";

const RUN = "radar-2026-10-09-recovery-01";
const V1 = "v7-5a78ea5d15214e37bcae18f167ffcee3";
const V2 = "v74-76d07c0d32444cecaf07e875deacb519";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

export async function run(base, out, shotsDir) {
  const results = [];
  const check = (name, ok, detail = "") => results.push({ name, ok: Boolean(ok), detail: typeof detail === "string" ? detail : JSON.stringify(detail) });
  if (shotsDir) fs.mkdirSync(shotsDir, { recursive: true });
  const shot = async (page, name, full = true) => shotsDir && page.shot(path.join(shotsDir, name + ".png"), full);

  const report = await session(async (page) => {
    // Refuse writes/provider traffic before transport, including forced V1 clicks.
    page.listeners.push(msg => {
      if (msg.method !== 'Fetch.requestPaused') return;
      const {requestId, request} = msg.params;
      const safe = request.method === 'GET' && new URL(request.url).origin === base;
      page.send(safe ? 'Fetch.continueRequest' : 'Fetch.failRequest', safe ? {requestId} : {requestId, errorReason:'BlockedByClient'});
    });
    // Static data.json is a large local GET; API paths and providers remain intercepted.
    await page.send('Fetch.enable', {patterns:[{urlPattern:base+'/api/*',requestStage:'Request'}, {urlPattern:'*googleapis*',requestStage:'Request'}, {urlPattern:'*generativelanguage*',requestStage:'Request'}]});
    const shell = () => page.eval(`(() => {
      const s = document.querySelector('.hfl-shell');
      return {
        navs: document.querySelectorAll('nav[aria-label="Navegação principal"]').length,
        legacyNavs: document.querySelectorAll('.module-header nav:not([role=tablist]), nav.header-nav, .workspace').length,
        legacyLabels: [...document.querySelectorAll('a,button,h1,h2')].map(e => e.textContent.trim()).filter(t => /^(Gestor de Carteira|Radar de Ativos|Operação Paper|Radar Multiativos|Pesquisa e Auditoria|Sala de Decisão|Prontidão para 13\\/10)$/.test(t)),
        area: s.querySelector('.hfl-primary a[aria-current],.hfl-archive a[aria-current]')?.dataset.area,
        section: s.querySelector('.hfl-secondary a[aria-current]')?.textContent || null,
        crumbs: [...s.querySelectorAll('.hfl-crumbs li:not([hidden])')].map(li => li.textContent.trim()),
        env: s.querySelector('.hfl-env').textContent,
        versions: /PREMIUM V\\d|Premium V\\d/.test(document.title + ' ' + document.body.innerText),
        title: document.title,
        overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
        h1: document.querySelectorAll('main h1:not([hidden]), .module-header h1').length,
      };
    })()`);

    // 1. Every page: one global navigation, no legacy menus, correct area, no overflow.
    const expected = { home: ["inicio", null], radar: ["mercado", "Radar de comitês"], portfolio: ["carteira", "Consulta demonstrativa"], paper: ["legacy", "Piloto PETR4"], h2: ["legacy", "Pesquisa H2"], logs: ["auditoria", "Logs técnicos"], legacy: ["legacy", "Acervo histórico"] };
    for (const [vname, v] of Object.entries(VIEWPORTS)) {
      await page.viewport(v);
      for (const [name, route] of PAGES) {
        await page.go(base + route, name === "home" ? 3500 : name === "legacy" ? 5000 : 2000);
        const s = await shell();
        if (vname === "desktop") {
          check(`nav:${name}:single_global_nav`, s.navs === 1 && s.legacyNavs === 0, s);
          check(`nav:${name}:no_legacy_labels`, s.legacyLabels.length === 0, s.legacyLabels);
          check(`nav:${name}:area`, s.area === expected[name][0] && (!expected[name][1] || s.section === expected[name][1]), s);
          check(`nav:${name}:no_version_branding`, !s.versions, s.title);
          check(`nav:${name}:breadcrumb`, s.crumbs.length >= 2 && s.crumbs[0] === "Hedge-Fund-Lab", s.crumbs);
          const tokens = await page.eval(`(() => { const c = getComputedStyle(document.documentElement); return [c.getPropertyValue('--border-control').trim(), c.getPropertyValue('--border2').trim()]; })()`);
          check(`ds:${name}:tokens_loaded`, tokens[0] === "#6a8199" && tokens[1] === "#6a8199", tokens);
          const field = await page.eval(`(() => { const e = document.querySelector('main select, main input:not([type=checkbox]):not([type=radio]):not([type=hidden])'); return e ? getComputedStyle(e).borderTopColor : null; })()`);
          if (field) check(`ds:${name}:control_border_3to1`, field === "rgb(106, 129, 153)", field);
          const help = await page.eval(`[...document.querySelectorAll('[data-help]')].map(b => [b.dataset.help, !!window.HFL_GLOSSARY[b.dataset.help], b.disabled, b.getAttribute('aria-label')])`);
          check(`help:${name}:ids_valid`, help.every(([, ok, disabled, label]) => ok && !disabled && label?.startsWith("Ajuda: ")), help.filter(h => !h[1] || h[2]));
        }
        check(`layout:${name}:${vname}:no_horizontal_overflow`, s.overflow <= 1, s.overflow);
      }
    }

    // 2. Hash routes, deep links, reload, history.
    await page.viewport(VIEWPORTS.desktop);
    for (const [route, area, section] of [["/paper#agentes", "legacy", "Agentes H2"], ["/paper#supervisao", "legacy", "Decisões registradas"], ["/#audit", "auditoria", "Registros e processos"], ["/#wallets", "legacy", "Carteiras independentes"], ["/h2#provisional/audit", "legacy", "Pesquisa H2"], ["/portfolio#ai-proposal", "carteira", "Simulador demonstrativo"]]) {
      await page.go(base + route);
      const s = await shell();
      check(`route:${route}`, s.area === area && s.section === section, s);
    }
    await page.go(base + `/radar?run=${RUN}`, 2500);
    const deep = await page.eval(`({ search: location.search, select: document.getElementById('radar-run')?.value, carteira: document.querySelector('.hfl-primary a[data-area=carteira]').getAttribute('href') })`);
    check("deeplink:radar_run_kept", deep.search.includes(RUN) && deep.select === RUN, deep);
    check("deeplink:run_carried_to_carteira", deep.carteira.includes("run=" + RUN), deep);
    await page.send("Page.reload");
    await page.once("Page.loadEventFired");
    await sleep(2000);
    check("deeplink:reload_keeps_run", (await page.eval("location.search")).includes(RUN));
    await page.go(base + `/portfolio?run=${RUN}`, 2500);
    const pdeep = await page.eval(`({ search: location.search, mercado: document.querySelector('.hfl-primary a[data-area=mercado]').getAttribute('href'), mode: !document.getElementById('workflow-mode') })`);
    check("deeplink:portfolio_run_kept", pdeep.search.includes(RUN) && pdeep.mercado.includes("run=" + RUN) && pdeep.mode === true, pdeep);
    await page.go(base + "/paper#sala");
    await page.click('.hfl-secondary a[href="/legacy/paper#carteiras"]');
    await sleep(400);
    const afterClick = await shell();
    await page.eval("history.back()");
    await sleep(600);
    const afterBack = await shell();
    check("history:hash_navigation_and_back", afterClick.section === "Carteiras independentes" && afterBack.section === "Decisões registradas", { afterClick: afterClick.section, afterBack: afterBack.section });

    // 3. Keyboard: skip link first, then the global navigation with a visible focus ring.
    await page.go(base + "/");
    await page.key("Tab");
    const first = await page.eval("document.activeElement.className");
    let reached = null;
    for (let i = 0; i < 12 && !reached; i++) {
      await page.key("Tab");
      reached = await page.eval(`(() => { const a = document.activeElement; return a.closest('.hfl-primary') ? { text: a.textContent, outline: getComputedStyle(a).outlineStyle, width: getComputedStyle(a).outlineWidth } : null; })()`);
    }
    check("keyboard:skip_link_first", first.includes("hfl-skip"), first);
    check("keyboard:reaches_primary_nav_with_focus_ring", reached && reached.outline !== "none" && parseFloat(reached.width) >= 2, reached);

    // 4. Contextual help: click, keyboard, Escape, close button, touch, viewport bounds.
    await page.go(base + "/", 3500);
    await page.click("#home-laboratory > summary");
    await page.click('.home-facts .ds-help[data-help="sem-ordens-reais"]');
    let h = await page.eval(`(() => { const p = document.getElementById('ds-help-popover'); const b = document.querySelector('.home-facts .ds-help[data-help="sem-ordens-reais"]'); return { open: p && !p.hidden, expanded: b.getAttribute('aria-expanded'), focusInside: p?.contains(document.activeElement), title: p?.querySelector('h2')?.textContent, role: p?.getAttribute('role') }; })()`);
    check("help:opens_on_click", h.open && h.expanded === "true" && h.focusInside && h.title === window_term("sem-ordens-reais") && h.role === "dialog", h);
    await shot(page, "after-help-open-desktop", false);
    await page.key("Escape");
    h = await page.eval(`({ open: !document.getElementById('ds-help-popover').hidden, focus: document.activeElement.dataset.help, expanded: document.activeElement.getAttribute('aria-expanded') })`);
    check("help:escape_closes_and_returns_focus", !h.open && h.focus === "sem-ordens-reais" && h.expanded === "false", h);
    await page.key("Enter");
    h = await page.eval(`({ open: !document.getElementById('ds-help-popover').hidden })`);
    check("help:opens_with_keyboard_enter", h.open, h);
    await page.click(".ds-popover-close");
    h = await page.eval(`({ open: !document.getElementById('ds-help-popover').hidden, focus: document.activeElement.dataset.help })`);
    check("help:close_button", !h.open && h.focus === "sem-ordens-reais", h);
    await sleep(2500);
    await page.click('.ds-flow .ds-help[data-help="veto"]');
    await sleep(3000);
    h = await page.eval(`({ open: !document.getElementById('ds-help-popover').hidden })`);
    check("help:stays_open_while_reading", h.open, h);
    await page.key("Escape");
    await page.click("#hfl-help-open");
    h = await page.eval(`(() => { const d = document.getElementById('hfl-help-center'); const s = d.querySelector('#hfl-help-search'); s.value = 'drawdown'; s.dispatchEvent(new Event('input')); return { open: d.open, visible: [...d.querySelectorAll('article')].filter(a => !a.hidden).map(a => a.id), total: d.querySelectorAll('article').length }; })()`);
    check("help:center_lists_and_filters_glossary", h.open && h.total >= 28 && h.visible.length === 1 && h.visible[0] === "glossario-drawdown", h);
    await shot(page, "after-help-center-desktop", false);
    await page.key("Escape");

    await page.viewport(VIEWPORTS.phone);
    await page.go(base + "/", 3500);
    await page.click("#home-laboratory > summary");
    await page.eval('document.querySelector(".home-facts .ds-help[data-help=inferencia-paga]").scrollIntoView({block:"center"})');
    await page.tap('.home-facts .ds-help[data-help="inferencia-paga"]');
    h = await page.eval(`(() => { const p = document.getElementById('ds-help-popover'); const r = p.getBoundingClientRect(); return { open: !p.hidden, left: r.left, right: r.right, vw: innerWidth }; })()`);
    check("help:touch_opens_within_viewport", h.open && h.left >= 0 && h.right <= h.vw, h);
    await shot(page, "after-help-open-phone", false);
    await page.key("Escape");

    // 5. Mobile menu: hidden by default, opens by tap, Escape closes.
    let m = await page.eval(`({ menu: getComputedStyle(document.querySelector('.hfl-menu')).display, nav: getComputedStyle(document.querySelector('.hfl-links')).display })`);
    check("mobile:menu_collapsed", m.menu !== "none" && m.nav === "none", m);
    await page.eval('document.querySelector(".hfl-menu").scrollIntoView({block:"center"})');
    await page.tap(".hfl-menu");
    m = await page.eval(`({ expanded: document.querySelector('.hfl-menu').getAttribute('aria-expanded'), nav: getComputedStyle(document.querySelector('.hfl-links')).display, links: document.querySelectorAll('.hfl-primary a').length, safety: getComputedStyle(document.querySelector('.hfl-local')).display })`);
    check("mobile:menu_opens_by_tap", m.expanded === "true" && m.nav !== "none" && m.links === 4 && m.safety !== "none", m);
    await shot(page, "after-mobile-menu-phone", false);
    await page.key("Escape");
    m = await page.eval(`({ expanded: document.querySelector('.hfl-menu').getAttribute('aria-expanded'), focus: document.activeElement.className })`);
    check("mobile:escape_closes_menu", m.expanded === "false" && m.focus.includes("hfl-menu"), m);

    // 6. Closed V1 paid action and history.
    await page.viewport(VIEWPORTS.desktop);
    await page.go(base + "/portfolio#global-workflow", 2500);
    let v = await page.eval(`(() => { const ids = ['workflow-prepare','workflow-preflight','workflow-run','workflow-authorize']; return { controls: ids.map(id => { const e = document.getElementById(id); return [id, !e || e.disabled, !e || e.offsetParent === null]; }), notice: document.getElementById('v1-closed')?.innerText, dialog: document.getElementById('workflow-confirm')?.open || false }; })()`);
    check("v1:paid_triggers_disabled_and_hidden", v.controls.every(([, disabled, hidden]) => disabled && hidden), v.controls);
    check("v1:closed_notice_visible", /encerrado para novas inferências/.test(v.notice || "") && /consulta e auditoria/.test(v.notice || ""), v.notice);
    const before = page.requests.length;
    await page.eval(`(() => { ['workflow-prepare','workflow-preflight','workflow-run','workflow-authorize'].forEach(id => { const e = document.getElementById(id); if(e){ e.disabled = false; e.hidden = false; e.closest('[hidden]')?.removeAttribute('hidden'); e.click(); } }); })()`);
    await sleep(800);
    v = await page.eval(`({ dialog: document.getElementById('workflow-confirm')?.open || false })`);
    const triggered = page.requests.slice(before).filter((r) => r.method !== "GET" || /global-(prepare|run|preflight)/.test(r.url));
    check("v1:forced_clicks_do_nothing", !v.dialog && triggered.length === 0, { dialog: v.dialog, triggered });
    await page.go(base + `/portfolio?analysis=${V1}#global-workflow`, 3000);
    v = await page.eval(`({ current: document.getElementById('decision-detail').innerText, replay: !document.getElementById('workflow-replay') })`);
    check("v1:history_still_consultable_and_rejected", /REJECTED_BY_VALIDATOR/.test(v.current) && /GLOBAL-PM-V1/.test(v.current) && v.replay === true, v.current.slice(0, 300));
    await shot(page, "after-portfolio-v1-history-desktop", false);
    await page.go(base + `/portfolio?analysis=${V2}#global-workflow`, 3000);
    v = await page.eval(`({ current: document.getElementById('decision-detail').innerText, run: !document.getElementById('workflow-run'), preflight: !document.getElementById('workflow-preflight') })`);
    check("v2:still_valid_and_no_paid_shortcut", /VALID_PROPOSAL/.test(v.current) && v.run && v.preflight, v);

    // 7. States and action natures are distinguishable without color.
    await page.go(base + "/", 3500);
    await page.click("#home-laboratory > summary");
    await sleep(1800);
    const st = await page.eval(`[...document.querySelectorAll('#home-state .ds-state')].map(e => ({ state: e.dataset.state, tone: e.dataset.tone, text: e.innerText.trim(), icon: e.querySelector('.ds-state-icon')?.textContent }))`);
    const valid = st.find((s) => s.state === "VALID_PROPOSAL"), rejected = st.find((s) => s.state === "REJECTED_BY_VALIDATOR");
    check("states:home_shows_real_v1_v2", valid && rejected && valid.tone !== rejected.tone && valid.icon !== rejected.icon && /validada/.test(valid.text) && /Rejeitada/.test(rejected.text), st);
    await page.go(base + `/radar?run=${RUN}`, 2500);
    const act = await page.eval(`[...document.querySelectorAll('button[data-action]')].map(b => [b.id, b.dataset.action, getComputedStyle(b, '::before').content])`);
    const paid = act.filter((a) => a[1] === "paid"), read = act.filter((a) => a[1] === "read");
    check("actions:paid_vs_read_distinct", paid.length && read.length && paid.every((a) => a[2].includes("¤")) && read.every((a) => !a[2].includes("¤")), act);

    // 8. No control can enable the H2 Final Test.
    await page.go(base + "/h2", 2500);
    const ft = await page.eval(`[...document.querySelectorAll('button,a')].filter(e => /final test/i.test(e.textContent) && !e.disabled).map(e => e.textContent.trim())`);
    check("h2:no_final_test_control", ft.length === 0, ft);

    // Evidence screenshots (after).
    for (const [vname, vp] of [["desktop", VIEWPORTS.desktop], ["phone", VIEWPORTS.phone]]) {
      await page.viewport(vp);
      for (const [name, route] of PAGES) {
        await page.go(base + route, name === "home" ? 3500 : name === "legacy" ? 5000 : 2000);
        await shot(page, `${name}-${vname}`);
      }
    }
    return { requests: page.requests.length, unsafe: unsafeRequests(page), console: page.console };
  });
  check("safety:only_get_no_provider", report.unsafe.length === 0, report.unsafe);
  check("console:no_errors", report.console.length === 0, report.console);
  const summary = { passed: results.filter((r) => r.ok).length, failed: results.filter((r) => !r.ok).length, requests: report.requests, results };
  fs.writeFileSync(out, JSON.stringify(summary, null, 1) + "\n");
  console.log(JSON.stringify({ passed: summary.passed, failed: summary.failed, failures: results.filter((r) => !r.ok) }, null, 1));
  if (summary.failed) process.exitCode = 1;
}

function window_term(id) {
  return { "sem-ordens-reais": "Sem ordens reais" }[id];
}
