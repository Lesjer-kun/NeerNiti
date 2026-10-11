/* Evidence table: readings per ghat with filters, sorting and colour-coded outcomes. */
(function () {
  const esc = s => String(s == null ? "" : s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const PHASE_ORDER = { pre: 0, during: 1, after: 2 };
  const OUT_ORDER = { breach: 0, bdl: 1, ok: 2, not_assessed: 3, missing: 4 };
  const REPORT_URL = {
    2023: "https://www.mppcb.mp.gov.in/proc/mon/Idol_immer._Report_23_CPCB.pdf",
    2024: "https://www.mppcb.mp.gov.in/proc/mon/Ganesh_and_Durga_visarjan_report-2024.pdf",
    2025: "https://www.mppcb.mp.gov.in/proc/mon/Ganesh_and_Durga_visarjan_report-2025.pdf",
  };

  function displayValue(r) {
    if (r.state === "numeric") return `${r.value}${r.unit ? " " + r.unit : ""}`;
    if (r.state === "bdl") return r.value_as_printed || "BDL";
    return r.flag || r.value_as_printed || "not sampled";
  }

  function filterRows(rows, f) {
    return rows.filter(r =>
      (!f.param || r.parameter === f.param) &&
      (!f.year || String(r.year) === String(f.year)) &&
      (!f.fest || r.festival === f.fest));
  }

  function sortRows(rows, mode) {
    const r = rows.slice();
    if (mode === "value_desc") r.sort((a, b) => (b.value ?? -Infinity) - (a.value ?? -Infinity));
    else if (mode === "value_asc") r.sort((a, b) => (a.value ?? Infinity) - (b.value ?? Infinity));
    else if (mode === "outcome") r.sort((a, b) => OUT_ORDER[a.outcome] - OUT_ORDER[b.outcome] || b.exceedance - a.exceedance);
    else r.sort((a, b) => a.year - b.year || a.festival.localeCompare(b.festival) || (a.source_page - b.source_page) ||
      a.parameter.localeCompare(b.parameter) || PHASE_ORDER[a.phase] - PHASE_ORDER[b.phase]);
    return r;
  }

  window.evidenceTableHTML = function (rows, filters, sortMode, lang) {
    const hi = lang === "hi";
    const list = sortRows(filterRows(rows, filters || {}), sortMode || "report");
    const head = hi ? ["वर्ष", "त्योहार", "चरण", "पैरामीटर", "मान", "सीमा", "स्थिति", "छपा हुआ", "पृष्ठ"]
                    : ["Year", "Festival", "Phase", "Parameter", "Value", "Limit", "Outcome", "As printed", "Page"];
    let h = `<thead><tr>${head.map(x => `<th>${x}</th>`).join("")}</tr></thead><tbody>`;
    const thr = window.APP.thresholds;
    list.forEach(r => {
      const t = thr[r.parameter];
      const lim = !t ? "" : t.type === "min" ? `>= ${t.min}` : t.type === "max" ? `<= ${t.max}` : `${t.min}-${t.max}`;
      const out = { breach: hi ? "सीमा से बाहर" : "breach", ok: hi ? "सीमा के भीतर" : "within limit", bdl: "BDL",
                    missing: hi ? "अनुपलब्ध" : "missing", not_assessed: hi ? "कोई सीमा नहीं" : "no limit" }[r.outcome];
      const page = r.source_page ? `<a class="underline text-sky-800" target="_blank" rel="noopener" href="${REPORT_URL[r.year] || "#"}#page=${r.source_page}">p.${r.source_page}</a>` : "";
      h += `<tr class="row-${r.outcome}"><td>${r.year}</td><td>${r.festival}</td><td>${r.phase}</td><td>${esc(r.parameter)}</td>` +
           `<td class="val">${esc(displayValue(r))}</td><td class="text-slate-500">${lim}</td><td>${out}</td>` +
           `<td class="text-slate-500">${esc(r.value_as_printed)}</td><td>${page}</td></tr>`;
    });
    if (!list.length) h += `<tr><td colspan="9" class="text-center text-slate-500 py-4">${hi ? "कोई रीडिंग नहीं" : "No readings match"}</td></tr>`;
    h += "</tbody>";
    return h;
  };

  window.siteNoteHTML = function (ghat, lang) {
    const hi = lang === "hi";
    let h = `<div class="flex flex-wrap items-center gap-2 text-sm">` +
      `<span class="badge tier-${ghat.tier.colour}">${hi ? ghat.tier.label_hi : ghat.tier.label_en}</span>` +
      `<span class="badge ev-${ghat.evidence.key}">${hi ? ghat.evidence.label_hi : ghat.evidence.label_en} (${ghat.evidence.readings} ${hi ? "रीडिंग" : "readings"}, ${ghat.evidence.combos}/${ghat.evidence.expected_combos} ${hi ? "संयोजन" : "combos"})</span>` +
      `<span class="text-slate-600">${esc(ghat.site)} - ${esc(ghat.water_body)}</span>`;
    if (ghat.site_ambiguous) h += `<span class="badge bg-amber-100 text-amber-900 border border-amber-400">${hi ? "स्थल नाम अस्पष्ट" : "site name ambiguous"}</span>`;
    h += `</div><p class="text-sm mt-1">${esc((hi ? ghat.reason_hi : ghat.reason_en).split(": ").slice(1).join(": "))}</p>`;
    return h;
  };
})();
