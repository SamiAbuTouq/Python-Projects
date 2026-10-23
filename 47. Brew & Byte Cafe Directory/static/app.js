(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  let ctrl, timer;
  /* ---------- toasts ---------- */
  function toast(msg, type = "success") {
    const box = $("#toasts"), el = document.createElement("div");
    el.className = `flash ${type}`; el.textContent = msg; box.append(el);
    setTimeout(() => el.classList.add("hide"), 3500);
    setTimeout(() => el.remove(), 4200);
  }
  setTimeout(() => $$("#server-flashes .flash").forEach(f => f.classList.add("hide")), 4000);

  /* ---------- images: placeholder when broken ---------- */
  function guardImages(root = document) {
    $$(".img img, .photo img", root).forEach(img => {
      const giveUp = () => { img.parentElement.classList.add("noimg"); img.remove(); };
      // first try the stock coffee photo, then fall back to the letter placeholder
      const fail = () => {
        const fb = img.dataset.fallback;
        if (fb && img.src !== fb) { img.dataset.fallback = ""; img.src = fb; img.addEventListener("error", giveUp, { once: true }); }
        else giveUp();
      };
      // Google "image unavailable" placeholders are tiny/odd-sized: treat as missing
      const check = () => { if (img.naturalWidth === 0 || img.naturalWidth < 120) fail(); };
      img.addEventListener("error", fail, { once: true });
      img.addEventListener("load", () => { if (!img.dataset.fallback) return; check(); }, { once: true });
      if (img.complete) check();
    });
  }
  guardImages();

  /* ---------- image preview on the add/edit form ---------- */
  const urlInput = $("#img_url"), prev = $("#preview");
  if (urlInput && prev) {
    const show = () => {
      prev.innerHTML = "";
      if (!urlInput.value) { prev.innerHTML = "<span>Image preview</span>"; return; }
      const im = new Image(); im.referrerPolicy = "no-referrer"; im.src = urlInput.value;
      im.onerror = () => prev.innerHTML = "<span>⚠️ This link doesn't load — try another image</span>";
      prev.append(im);
    };
    urlInput.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(show, 400); });
    show();
  }

  /* ---------- confirm dialog ---------- */
  const dlg = $("#confirm");
  function askConfirm(message) {
    return new Promise(res => {
      $("#confirm-msg").textContent = message;
      dlg.returnValue = "cancel";
      dlg.addEventListener("close", () => res(dlg.returnValue === "ok"), { once: true });
      dlg.showModal();
    });
  }

  /* ---------- live filtering (no page refresh) ---------- */
  const form = $("#filters"), results = $("#results");
  

  function query() {
    const p = new URLSearchParams(new FormData(form));
    for (const [k, v] of [...p]) if (!v || (k === "sort" && v === "name")) p.delete(k);
    return p.toString();
  }

  async function refresh() {
    ctrl?.abort(); ctrl = new AbortController();
    const qs = query();
    results.classList.add("loading");
    try {
      const r = await fetch(`${location.pathname}${qs ? "?" + qs : ""}`,
        { headers: { "X-Requested-With": "fetch" }, signal: ctrl.signal });
      results.innerHTML = await r.text();
      history.replaceState(null, "", qs ? `?${qs}` : location.pathname);
      guardImages(results);
    } catch (e) {
      if (e.name !== "AbortError") toast("Couldn't load cafes. Check your connection.", "error");
    } finally { results.classList.remove("loading"); }
  }

  if (form) {
    form.addEventListener("submit", e => { e.preventDefault(); refresh(); });
    $("input[type=search]", form).addEventListener("input", () => {
      clearTimeout(timer); timer = setTimeout(refresh, 250);
    });
    $$("select, .chip input", form).forEach(el => el.addEventListener("change", refresh));
    document.addEventListener("click", e => {
      if (e.target.closest("[data-reset]")) { form.reset(); $$("select", form).forEach(s => s.selectedIndex = 0); refresh(); }
    });
  }

  /* ---------- delete (confirm → fetch → animate away) ---------- */
  document.addEventListener("submit", async e => {
    const f = e.target.closest("form[data-confirm]");
    if (!f) return;
    e.preventDefault();
    if (!(await askConfirm(f.dataset.confirm))) return;
    const card = f.closest(".card");
    if (!card) return f.submit();           // detail page: normal redirect
    try {
      const r = await fetch(f.action, { method: "POST", headers: { "X-Requested-With": "fetch" } });
      const data = await r.json();
      if (!data.ok) throw 0;
      card.classList.add("removing");
      setTimeout(() => { card.remove(); refresh(); }, 350);
      Object.entries(data.stats).forEach(([k, v]) => { const el = $(`[data-stat=${k}]`); if (el) el.textContent = v; });
      toast(`“${data.name}” was removed.`);
    } catch { toast("Couldn't remove that cafe.", "error"); }
  });
})();
