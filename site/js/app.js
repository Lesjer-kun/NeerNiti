/* Main controller: loads build artifacts, wires tabs, language, cards, drawer, evidence filters. */
(function () {
  const APP = window.APP = { lang: "en", sort: "severity", ranking: null, evidence: null, brief: null, thresholds: null };
  const $ = id => document.getElementById(id);
  const I18N = {
    en: { subtitle: "Pre-festival water-quality briefing for Bhopal ghats", tab_dashboard: "Dashboard", tab_evidence: "Evidence", tab_brief: "Brief",
          ranked_heading: "Ghats ranked by concern (CPCB Class B limits, Durga weighted 2x)",
          ranked_note: "Severity and evidence strength are separate axes. A ghat with limited evidence is never shown as implicitly safe; its gaps are listed on the card.",
          sort_severity: "By severity", sort_testing: "By testing priority" },
    hi: { subtitle: "भोपाल घाटों के लिए त्योहार-पूर्व जल-गुणवत्ता ब्रीफ", tab_dashboard: "डैशबोर्ड", tab_evidence: "साक्ष्य", tab_brief: "ब्रीफ",
          ranked_heading: "चिंता के क्रम में घाट (CPCB क्लास B सीमाएँ, दुर्गा 2x भारित)",
          ranked_note: "गंभीरता और साक्ष्य-शक्ति अलग-अलग धुरी हैं। सीमित साक्ष्य वाला घाट कभी अप्रत्यक्ष रूप से ठीक नहीं दिखाया जाता; उसके अंतराल कार्ड पर सूचीबद्ध हैं।",
          sort_severity: "गंभीरता से", sort_testing: "जाँच प्राथमिकता से" },
  };

  async function loadJSON(name) {
    const r = await fetch(`data/${name}?v=${Date.now()}`);
    if (!r.ok) throw new Error(`${name}: HTTP ${r.status}`);
    return r.json();
  }

  function ghatBySite(site) { return APP.ranking.ghats.find(g => g.site === site); }

  function applyI18n() {
    document.querySelectorAll("[data-i18n]").forEach(el => { el.textContent = I18N[APP.lang][el.dataset.i18n] || el.textContent; });
    $("lang-toggle").textContent = APP.lang === "en" ? "हिंदी" : "English";
    document.documentElement.lang = APP.lang;
  }

  function renderDashboard() {
    $("summary-cards").innerHTML = window.summaryCardsHTML(APP.ranking, APP.lang);
    const list = APP.ranking.ghats.slice();
    if (APP.sort === "testing") list.sort((a, b) => a.testing_priority.rank - b.testing_priority.rank);
    $("ghat-cards").innerHTML = list.map(g => window.ghatCardHTML(g, APP.lang, APP.sort)).join("");
    document.querySelectorAll(".sort-btn").forEach(b => b.classList.toggle("active", b.dataset.sort === APP.sort));
    const m = APP.ranking.method;
    $("method").innerHTML = `<strong>Method (implementation choices, not source-stated):</strong> severity = 0.35 DO + 0.35 BOD + 0.15 pH + 0.15 worst-value penalty, each parameter = weighted breach rate x (1 + worst-value factor); Durga readings weighted ${m.festival_weight.Durga}x. Tiers: critical >= 75, high >= 50, moderate >= 25, else lower. Evidence strength: ${m.evidence_strength}. BDL readings are not evaluated; missing readings count in no direction. Generated: ${APP.ranking.generated}.`;
  }

  function renderEvidence() {
    const site = $("ev-site").value;
    const ghat = ghatBySite(site);
    const rows = APP.evidence.sites[site] || [];
    $("ev-site-note").innerHTML = window.siteNoteHTML(ghat, APP.lang);
    $("ev-table").innerHTML = window.evidenceTableHTML(rows, { param: $("ev-param").value, year: $("ev-year").value, fest: $("ev-fest").value }, $("ev-sort").value, APP.lang);
    $("gaps-panel").innerHTML = window.gapsPanelHTML(ghat, APP.lang);
  }

  function openDrawer(site) {
    const ghat = ghatBySite(site);
    const rows = APP.evidence.sites[site] || [];
    $("drawer-title").textContent = ghat.short_name;
    $("drawer-body").innerHTML =
      `<div class="mb-3">${window.siteNoteHTML(ghat, APP.lang)}</div>` +
      `<div class="grid md:grid-cols-3 gap-3 mb-3">` +
      `<div class="md:col-span-2 overflow-x-auto"><table class="min-w-full text-xs ev-mini">${window.evidenceTableHTML(rows, { param: "" }, "outcome", APP.lang)}</table></div>` +
      `<div>${window.gapsPanelHTML(ghat, APP.lang)}</div></div>`;
    $("drawer").classList.remove("hidden"); $("drawer-backdrop").classList.remove("hidden");
    $("drawer-full").onclick = () => { closeDrawer(); switchTab("evidence"); $("ev-site").value = site; renderEvidence(); };
    document.body.style.overflow = "hidden";
  }
  function closeDrawer() {
    $("drawer").classList.add("hidden"); $("drawer-backdrop").classList.add("hidden");
    document.body.style.overflow = "";
  }

  function switchTab(name) {
    document.querySelectorAll(".tab").forEach(t => t.classList.toggle("active", t.dataset.tab === name));
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.toggle("hidden", p.id !== "tab-" + name));
    if (name === "evidence") renderEvidence();
    history.replaceState(null, "", "#" + name);
  }

  function fillSelect(sel, values, labelFn) {
    values.forEach(v => { const o = document.createElement("option"); o.value = v; o.textContent = labelFn ? labelFn(v) : v; sel.appendChild(o); });
  }

  async function init() {
    try {
      const [ranking, evidence, brief] = await Promise.all([loadJSON("ranking.json"), loadJSON("evidence.json"), loadJSON("brief.json")]);
      APP.ranking = ranking; APP.evidence = evidence; APP.brief = brief; APP.thresholds = ranking.thresholds;
    } catch (e) {
      $("loading").classList.add("hidden");
      $("error").classList.remove("hidden");
      $("error").innerHTML = `Could not load build artifacts (${e.message}). Run <code>python build.py</code> and serve this folder over HTTP, e.g. <code>python -m http.server 8000 --directory site</code>.`;
      return;
    }
    $("loading").classList.add("hidden");
    $("badge-period").textContent = `Data ${APP.ranking.data_period}`;
    const vb = $("badge-verify");
    vb.textContent = APP.ranking.verification.badge;
    vb.className = "badge " + (APP.ranking.verification.passed ? "bg-green-600" : "bg-red-600");

    fillSelect($("ev-site"), APP.ranking.ghats.map(g => g.site), s => ghatBySite(s).short_name);
    fillSelect($("ev-param"), APP.evidence.parameters);
    fillSelect($("ev-year"), [2023, 2024, 2025]);
    fillSelect($("ev-fest"), ["Ganesh", "Durga"]);
    ["ev-site", "ev-param", "ev-year", "ev-fest", "ev-sort"].forEach(id => $(id).addEventListener("change", renderEvidence));

    document.querySelectorAll(".tab").forEach(t => t.addEventListener("click", () => switchTab(t.dataset.tab)));
    document.querySelectorAll(".sort-btn").forEach(b => b.addEventListener("click", () => { APP.sort = b.dataset.sort; renderDashboard(); }));
    $("ghat-cards").addEventListener("click", e => { const c = e.target.closest(".card"); if (c) openDrawer(c.dataset.site); });
    $("ghat-cards").addEventListener("keydown", e => { const c = e.target.closest(".card"); if (c && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); openDrawer(c.dataset.site); } });
    $("drawer-close").addEventListener("click", closeDrawer);
    $("drawer-backdrop").addEventListener("click", closeDrawer);
    document.addEventListener("keydown", e => { if (e.key === "Escape") closeDrawer(); });
    $("lang-toggle").addEventListener("click", () => {
      APP.lang = APP.lang === "en" ? "hi" : "en";
      applyI18n(); renderDashboard(); if (!$("tab-evidence").classList.contains("hidden")) renderEvidence();
      window.setBriefLang(APP.lang);
    });

    window.initBriefView(APP.brief);
    applyI18n();
    renderDashboard();
    const tab = (location.hash || "#dashboard").slice(1);
    switchTab(["dashboard", "evidence", "brief"].includes(tab) ? tab : "dashboard");
  }

  document.addEventListener("DOMContentLoaded", init);
})();
