/* Bilingual brief: toggle, copy-to-clipboard, print. */
(function () {
  let brief = null, lang = "en";

  function render() {
    const pre = document.getElementById("brief-text");
    pre.textContent = brief[lang];
    pre.classList.toggle("hi", lang === "hi");
    pre.setAttribute("lang", lang);
    document.querySelectorAll(".brief-lang").forEach(b => b.classList.toggle("active", b.dataset.lang === lang));
    const v = brief.verification.texts["brief_" + lang];
    const badge = document.getElementById("brief-badge");
    badge.textContent = v.badge;
    badge.className = "badge " + (v.passed ? "bg-green-600 text-white" : "bg-red-600 text-white");
  }

  async function copyText() {
    const status = document.getElementById("copy-status");
    try {
      await navigator.clipboard.writeText(brief[lang]);
    } catch (e) {
      const ta = document.createElement("textarea");
      ta.value = brief[lang]; document.body.appendChild(ta); ta.select();
      document.execCommand("copy"); ta.remove();
    }
    status.textContent = lang === "hi" ? "कॉपी हो गया" : "Copied";
    setTimeout(() => { status.textContent = ""; }, 2000);
  }

  function print() {
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("print-me"));
    document.getElementById("tab-brief").classList.add("print-me");
    window.print();
  }

  window.initBriefView = function (briefDoc) {
    brief = briefDoc;
    document.querySelectorAll(".brief-lang").forEach(b => b.addEventListener("click", () => { lang = b.dataset.lang; render(); }));
    document.getElementById("brief-copy").addEventListener("click", copyText);
    document.getElementById("brief-print").addEventListener("click", print);
    render();
  };
  window.setBriefLang = function (l) { if (brief) { lang = l; render(); } };
})();
