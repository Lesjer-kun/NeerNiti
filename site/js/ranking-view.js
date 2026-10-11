/* Ranked ghat cards. */
(function () {
  const esc = s => String(s == null ? "" : s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const TREND = {
    en: { worsening: "worsening", improving: "improving", stable: "stable", "insufficient data": "trend: insufficient data" },
    hi: { worsening: "बिगड़ता", improving: "सुधरता", stable: "स्थिर", "insufficient data": "रुझान: अपर्याप्त डेटा" },
  };

  function paramLine(ghat, p, label, thr, hi) {
    const s = ghat.summary[p];
    if (!s.sampled) return `<div><span class="font-medium">${label}</span>: ${hi ? "कोई संख्यात्मक रीडिंग नहीं" : "no numeric readings"}</div>`;
    const worst = s.worst_value != null ? `${s.worst_value}` : "";
    const lim = thr.type === "min" ? `< ${thr.min}` : thr.type === "max" ? `> ${thr.max}` : `${hi ? "बाहर" : "outside"} ${thr.min}-${thr.max}`;
    return `<div><span class="font-medium">${label}</span> ${lim}: <span class="${s.breaches ? "text-red-700 font-semibold" : "text-green-700"}">${s.breaches}/${s.sampled}</span>` +
      ` <span class="text-slate-500">(${p === "Dissolved oxygen" ? (hi ? "न्यूनतम" : "lowest") : p === "BOD" ? (hi ? "अधिकतम" : "highest") : (hi ? "सबसे दूर" : "farthest")} ${worst}` +
      (s.missing ? `, ${s.missing} ${hi ? "अनुपलब्ध" : "missing"}` : "") + `)</span></div>`;
  }

  window.ghatCardHTML = function (ghat, lang, sortMode) {
    const hi = lang === "hi";
    const thr = window.APP.thresholds;
    const rankShown = sortMode === "testing" ? ghat.testing_priority.rank : ghat.rank;
    let h = `<article class="card tier-${ghat.tier.colour}" data-site="${esc(ghat.site)}" tabindex="0" role="button" aria-label="${esc(ghat.short_name)} evidence">`;
    h += `<div class="flex items-start gap-3">`;
    h += `<div class="text-3xl font-bold text-slate-400 leading-none">${rankShown}</div>`;
    h += `<div class="flex-1 min-w-0">`;
    h += `<div class="flex flex-wrap items-center gap-2 mb-1"><h3 class="font-semibold text-lg">${esc(ghat.short_name)}</h3><span class="text-slate-500 text-sm">${esc(ghat.water_body)}</span></div>`;
    h += `<div class="flex flex-wrap gap-2 mb-2">` +
      `<span class="badge tier-${ghat.tier.colour}" title="severity ${ghat.severity}/100">${hi ? ghat.tier.label_hi : ghat.tier.label_en} · ${ghat.severity}</span>` +
      `<span class="badge ev-${ghat.evidence.key}" title="${ghat.evidence.readings} DO/BOD/pH readings across ${ghat.evidence.combos} of ${ghat.evidence.expected_combos} year-festival-phase combinations">${hi ? ghat.evidence.label_hi : ghat.evidence.label_en} · ${ghat.evidence.readings} ${hi ? "रीडिंग" : "readings"}</span>` +
      `<span class="badge bg-slate-100 text-slate-700">${TREND[lang][ghat.year_trend]}</span>`;
    if (sortMode === "testing") h += `<span class="badge bg-sky-100 text-sky-900">${hi ? "जाँच प्राथमिकता" : "testing priority"} #${ghat.testing_priority.rank}</span>`;
    h += `</div>`;
    h += `<p class="text-sm mb-2">${esc((hi ? ghat.reason_hi : ghat.reason_en).split(": ").slice(1).join(": "))}</p>`;
    h += `<div class="text-xs space-y-0.5 mb-2">` +
      paramLine(ghat, "Dissolved oxygen", "DO", thr["Dissolved oxygen"], hi) +
      paramLine(ghat, "BOD", "BOD", thr["BOD"], hi) +
      paramLine(ghat, "pH", "pH", thr["pH"], hi) + `</div>`;
    if (ghat.coverage.gaps.length) {
      h += `<div class="text-xs bg-amber-50 border border-amber-300 rounded px-2 py-1 mb-2"><strong>${hi ? "डेटा अंतराल" : "Data gaps"}:</strong> ${ghat.coverage.gaps.length}/${ghat.coverage.expected} ${hi ? "वर्ष-त्योहार-चरण संयोजनों में DO/BOD/pH रीडिंग नहीं" : "year-festival-phase combinations have no DO/BOD/pH reading"}` +
        (ghat.testing_priority.missing_readings ? `; ${ghat.testing_priority.missing_readings} ${hi ? "रीडिंग अनुपलब्ध" : "readings missing"}` : "") + `</div>`;
    } else if (ghat.testing_priority.missing_readings) {
      h += `<div class="text-xs text-slate-600 mb-2">${ghat.testing_priority.missing_readings} ${hi ? "DO/BOD/pH रीडिंग अनुपलब्ध" : "DO/BOD/pH readings missing"}</div>`;
    }
    if (ghat.site_ambiguous) {
      h += `<div class="text-xs bg-amber-50 border border-amber-300 rounded px-2 py-1 mb-2"><strong>${hi ? "स्थल अस्पष्टता" : "Site ambiguity"}:</strong> ${hi ? "गणेश और दुर्गा तालिकाओं में अलग नाम; दो स्थान हो सकते हैं।" : "Ganesh and Durga tables print different names; may be two places."}</div>`;
    }
    h += `<div class="grid grid-cols-2 gap-2 text-xs text-slate-500">` +
      `<div>DO (${hi ? "रेखा" : "line"} = ${thr["Dissolved oxygen"].min})${window.phaseChartSVG(ghat.phase_series["Dissolved oxygen"], "Dissolved oxygen", thr["Dissolved oxygen"], { width: 260, height: 56 })}</div>` +
      `<div>BOD (${hi ? "रेखा" : "line"} = ${thr["BOD"].max})${window.phaseChartSVG(ghat.phase_series["BOD"], "BOD", thr["BOD"], { width: 260, height: 56 })}</div></div>`;
    h += `<div class="text-xs text-sky-800 mt-2">${hi ? "साक्ष्य देखने के लिए क्लिक करें →" : "Click for evidence and source pages →"}</div>`;
    h += `</div></div></article>`;
    return h;
  };

  window.summaryCardsHTML = function (ranking, lang) {
    const hi = lang === "hi";
    const h = ranking.headline;
    const assessedSampled = h["Dissolved oxygen"].sampled + h["BOD"].sampled + h["pH"].sampled;
    const assessedBreaches = h["Dissolved oxygen"].breaches + h["BOD"].breaches + h["pH"].breaches;
    const gaps = ranking.ghats.reduce((n, g) => n + g.coverage.gaps.length, 0);
    const cards = [
      [hi ? "कुल रीडिंग" : "Total readings", h.total_rows, `${h.readings_bdl} BDL · ${h.readings_missing} ${hi ? "अनुपलब्ध" : "missing"}`],
      [hi ? "सीमा से बाहर (DO/BOD/pH)" : "Breaches (DO/BOD/pH)", `${assessedBreaches}/${assessedSampled}`, `DO ${h["Dissolved oxygen"].breaches}/${h["Dissolved oxygen"].sampled} · BOD ${h["BOD"].breaches}/${h["BOD"].sampled} · pH ${h["pH"].breaches}/${h["pH"].sampled}`],
      [hi ? "डेटा अंतराल" : "Data gaps", gaps, hi ? "वर्ष-त्योहार-चरण संयोजन बिना रीडिंग" : "year-festival-phase combos without readings"],
      [hi ? "घाट" : "Ghats analysed", ranking.ghats.length, `${ranking.data_period} · Ganesh + Durga`],
    ];
    return cards.map(([t, v, s]) => `<div class="bg-white rounded shadow-sm p-3"><div class="text-xs text-slate-500">${t}</div><div class="text-2xl font-semibold">${v}</div><div class="text-xs text-slate-500">${s}</div></div>`).join("");
  };
})();
