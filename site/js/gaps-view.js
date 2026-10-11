/* "What we don't know" panel: coverage matrix + parameter gaps for one ghat. */
(function () {
  const YEARS = [2023, 2024, 2025], FESTS = ["Ganesh", "Durga"], PHASES = ["pre", "during", "after"];
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  window.gapsPanelHTML = function (ghat, lang) {
    const hi = lang === "hi";
    const cov = ghat.coverage;
    const byKey = {};
    (cov.combos || []).forEach(c => { byKey[`${c.year}|${c.festival}|${c.phase}`] = c; });
    let h = `<h4 class="font-semibold mb-1">${hi ? "हम क्या नहीं जानते" : "What we don't know"}</h4>`;
    h += `<p class="text-xs text-slate-600 mb-2">${hi
      ? `${cov.expected} में से ${cov.covered} वर्ष-त्योहार-चरण संयोजनों में DO/BOD/pH रीडिंग है।`
      : `${cov.covered} of ${cov.expected} year-festival-phase combinations have a DO/BOD/pH reading.`}</p>`;
    h += `<table class="text-xs mb-3"><thead><tr><th></th>${FESTS.map(f => `<th class="px-1 text-left">${f}</th>`).join("")}</tr></thead><tbody>`;
    YEARS.forEach(y => {
      h += `<tr><td class="pr-2 font-medium">${y}</td>`;
      FESTS.forEach(f => {
        h += "<td>";
        PHASES.forEach(p => {
          const c = byKey[`${y}|${f}|${p}`] || { status: "no_table" };
          const title = `${f} ${y} ${p}: ${c.status === "covered" ? c.assessed_readings + " readings" : c.status.replace(/_/g, " ")}`;
          h += `<span class="cov cov-${c.status}" title="${esc(title)}">${p[0].toUpperCase()}</span>`;
        });
        h += "</td>";
      });
      h += "</tr>";
    });
    h += "</tbody></table>";
    h += `<div class="text-xs text-slate-500 mb-3"><span class="cov cov-covered">P</span> ${hi ? "डेटा है" : "data"} <span class="cov cov-tabled_but_missing">D</span> ${hi ? "तालिका है, रीडिंग नहीं" : "table but no reading"} <span class="cov cov-no_table">A</span> ${hi ? "रिपोर्ट में तालिका नहीं" : "no table in report"}</div>`;

    if (cov.gaps && cov.gaps.length) {
      h += `<ul class="text-xs list-disc ml-4 mb-3">`;
      const noTable = {};
      cov.gaps.forEach(g => {
        if (g.status === "no_table") { noTable[`${g.festival} ${g.year}`] = true; }
        else h += `<li>${g.festival} ${g.year} ${g.phase}: ${hi ? "तालिका है पर DO/BOD/pH रीडिंग नहीं" : "table present but no DO/BOD/pH reading"}</li>`;
      });
      Object.keys(noTable).forEach(k => { h += `<li>${k}: ${hi ? "रिपोर्ट में कोई तालिका नहीं" : "no table in the report"}</li>`; });
      h += "</ul>";
    }
    if (ghat.parameter_gaps && ghat.parameter_gaps.length) {
      h += `<h5 class="font-medium text-sm mb-1">${hi ? "पैरामीटर अंतराल" : "Parameter gaps"}</h5><ul class="text-xs list-disc ml-4 mb-3">`;
      ghat.parameter_gaps.forEach(g => { h += `<li>${esc(g.parameter)}: ${esc(g.note)}</li>`; });
      h += "</ul>";
    }
    if (ghat.site_ambiguous) {
      h += `<div class="text-xs bg-amber-50 border border-amber-300 rounded p-2 mb-2"><strong>${hi ? "स्थल अस्पष्टता" : "Site ambiguity"}:</strong> ${hi
        ? "गणेश और दुर्गा तालिकाओं में अलग-अलग नाम छपे हैं; ये दो स्थान हो सकते हैं।"
        : "Ganesh and Durga tables print different names; these may be two places."} <br>${(ghat.names_as_printed || []).map(esc).join(" / ")}</div>`;
    }
    h += `<p class="text-xs text-slate-500">${hi
      ? "इकाइयाँ रिपोर्ट में नहीं छपीं (मानक मानी गईं)। BDL = बहुत कम, शून्य नहीं। अनुपलब्ध = कभी साफ़ नहीं माना।"
      : "Units are not printed in the reports (standard assumed). BDL = very low, not zero. Missing = never treated as clean."}</p>`;
    return h;
  };
})();
