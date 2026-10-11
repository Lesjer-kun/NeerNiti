/* Mini phase charts: SVG bar groups (pre / during / after) per year-festival for one parameter. */
(function () {
  const COLOUR = { breach: "#dc2626", ok: "#16a34a", bdl: "#2563eb", missing: "#94a3b8", no_table: "transparent" };

  function scaleFor(param, thr) {
    if (param === "Dissolved oxygen") return { max: 10, line: thr.min };
    if (param === "BOD") return { max: 25, line: thr.max };
    return { max: 10, min: 5, line: [thr.min, thr.max] };
  }

  /** series: [{year, festival, points:[{phase,value,outcome}]}] */
  window.phaseChartSVG = function (series, param, thr, opts) {
    opts = opts || {};
    const W = opts.width || 300, H = opts.height || 64, pad = 14, bottom = 12;
    const groups = series.length || 1;
    const gw = (W - pad * 2) / groups;
    const bw = Math.max(3, (gw - 8) / 3);
    const sc = scaleFor(param, thr);
    const lo = sc.min || 0;
    const yOf = v => H - bottom - ((Math.min(v, sc.max) - lo) / (sc.max - lo)) * (H - bottom - 6);
    let s = `<svg class="spark" viewBox="0 0 ${W} ${H}" width="100%" height="${H}" role="img" aria-label="${param} pre/during/after">`;
    const lines = Array.isArray(sc.line) ? sc.line : [sc.line];
    lines.forEach(l => {
      s += `<line x1="${pad}" x2="${W - pad}" y1="${yOf(l)}" y2="${yOf(l)}" stroke="#f59e0b" stroke-dasharray="3 2" stroke-width="1"/>`;
    });
    series.forEach((g, i) => {
      const x0 = pad + i * gw + 4;
      g.points.forEach((p, j) => {
        const x = x0 + j * bw;
        if (p.outcome === "no_table") return;
        if (p.value == null) {
          s += `<rect x="${x}" y="${H - bottom - 4}" width="${bw - 1}" height="4" fill="${COLOUR[p.outcome] || COLOUR.missing}" opacity="0.8"><title>${g.festival} ${g.year} ${p.phase}: ${p.outcome}</title></rect>`;
          return;
        }
        const y = yOf(p.value);
        s += `<rect x="${x}" y="${y}" width="${bw - 1}" height="${H - bottom - y}" fill="${COLOUR[p.outcome] || "#64748b"}"><title>${g.festival} ${g.year} ${p.phase}: ${p.value}</title></rect>`;
      });
      s += `<text x="${x0 + bw * 1.5}" y="${H - 2}" text-anchor="middle">${g.festival[0]}${String(g.year).slice(2)}</text>`;
    });
    s += "</svg>";
    return s;
  };
})();
