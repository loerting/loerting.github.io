(() => {
  const path = location.pathname;
  const german = path === "/de" || path.startsWith("/de/");
  const rest = location.search + location.hash;
  let chosen = null;
  try {
    chosen = localStorage.getItem("lang");
  } catch {}
  const browser = (navigator.languages || [navigator.language || ""])
    .map((tag) => tag.slice(0, 2).toLowerCase())
    .find((code) => code === "de" || code === "en");

  if (!german && (chosen || browser) === "de") {
    location.replace("/de" + path + rest);
    return;
  }
  if (german && chosen === "en") {
    location.replace((path.slice(3) || "/") + rest);
    return;
  }
  const root = document.documentElement;
  if (root.hasAttribute("data-either-lang")) {
    root.lang = german ? "de" : "en";
    if (german) document.title = root.dataset.titleDe;
  }
  document.addEventListener("click", (event) => {
    const link = event.target.closest("[data-lang]");
    if (!link) return;
    try {
      localStorage.setItem("lang", link.dataset.lang);
    } catch {}
  });
})();
