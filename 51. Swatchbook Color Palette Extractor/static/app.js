const $ = (id) => document.getElementById(id);
const drop = $("drop"), fileInput = $("file"), preview = $("preview");
const statusEl = $("status"), rows = $("rows"), actions = $("actions");
let palette = [];

// Pick dark or white text depending on how light the swatch is
const textOn = ([r, g, b]) => (0.299 * r + 0.587 * g + 0.114 * b) > 150 ? "#15171c" : "#ffffff";

function toast(msg) {
  const t = $("toast");
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(toast.id);
  toast.id = setTimeout(() => t.classList.remove("show"), 1600);
}

async function copy(text, msg) {
  try { await navigator.clipboard.writeText(text); toast(msg); }
  catch { toast("Couldn’t copy. Select the code manually."); }
}

function setStatus(msg, isError = false) {
  statusEl.textContent = msg;
  statusEl.classList.toggle("error", isError);
}

function render(colours) {
  palette = colours;
  const max = colours[0].percent;
  rows.innerHTML = "";
  colours.forEach((c, i) => {
    const li = document.createElement("li");
    li.className = "row";
    const width = Math.max(28, (c.percent / max) * 100);
    li.innerHTML = `
      <button class="bar" type="button" style="--i:${i};width:${width}%;background:${c.hex};color:${textOn(c.rgb)}"
              aria-label="Copy ${c.hex}">${c.hex}</button>
      <div class="meta"><b>${c.percent}%</b><span>rgb(${c.rgb.join(", ")})</span></div>`;
    li.querySelector(".bar").addEventListener("click", () => copy(c.hex, `Copied ${c.hex}`));
    rows.appendChild(li);
  });
  document.documentElement.style.setProperty("--tint", colours[0].hex);
  actions.hidden = false;
  setStatus(`Top ${colours.length} colours. Click any bar to copy its HEX code.`);
}

async function handleFile(file) {
  if (!file) return;
  if (!file.type.startsWith("image/")) { setStatus("That file isn’t an image. Try a PNG, JPG, WebP or GIF.", true); return; }

  // Revoke any previous blob URL to avoid memory leaks
  if (preview.src && preview.src.startsWith('blob:')) URL.revokeObjectURL(preview.src);

  const objectUrl = URL.createObjectURL(file);
  preview.onload = () => { preview.hidden = false; };
  preview.onerror = () => { setStatus("Couldn't display the image preview.", true); };
  preview.src = objectUrl;
  $("dropEmpty").hidden = true;
  drop.classList.add("has-image");
  $("again").hidden = false;
  rows.innerHTML = ""; actions.hidden = true;
  setStatus("Counting pixels…");

  const body = new FormData();
  body.append("image", file);
  try {
    const res = await fetch("/extract", { method: "POST", body });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Something went wrong.");
    render(data.colours);
  } catch (err) {
    setStatus(err.message, true);
  }
}

fileInput.addEventListener("change", () => handleFile(fileInput.files[0]));
$("again").addEventListener("click", () => { fileInput.value = ""; fileInput.click(); });
drop.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); fileInput.click(); } });
["dragenter", "dragover"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("over"); }));
["dragleave", "drop"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("over"); }));
drop.addEventListener("drop", (e) => handleFile(e.dataTransfer.files[0]));

$("copyCss").addEventListener("click", () => {
  const css = ":root {\n" + palette.map((c, i) => `  --colour-${i + 1}: ${c.hex};`).join("\n") + "\n}";
  copy(css, "Copied CSS variables");
});
