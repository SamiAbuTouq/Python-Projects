// Sticky header shadow
const header = document.querySelector(".site-header");
const onScroll = () => header.classList.toggle("scrolled", window.scrollY > 8);
onScroll();
window.addEventListener("scroll", onScroll, { passive: true });

// Auto-dismiss toasts
document.querySelectorAll(".toast").forEach((t, i) => {
  setTimeout(() => {
    t.classList.add("hide");
    setTimeout(() => t.remove(), 450);
  }, 4200 + i * 600);
});

// Toast helper
function showToast(message, type = "ok") {
  let box = document.querySelector(".toasts");
  if (!box) {
    box = document.createElement("div");
    box.className = "toasts";
    box.setAttribute("role", "status");
    box.setAttribute("aria-live", "polite");
    document.body.appendChild(box);
  }
  const t = document.createElement("div");
  t.className = "toast " + type;
  t.textContent = message;
  box.appendChild(t);
  setTimeout(() => {
    t.classList.add("hide");
    setTimeout(() => t.remove(), 450);
  }, 3000);
}

// Add to cart without reloading the page
document.querySelectorAll("form.js-add").forEach((form) => {
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = form.querySelector("button[type=submit]");
    const label = btn.textContent;
    btn.disabled = true;
    try {
      const res = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: { "X-Requested-With": "fetch" },
      });
      if (!res.ok) throw new Error("bad response");
      const data = await res.json();
      const badge = document.getElementById("cart-badge");
      badge.textContent = data.count;
      badge.hidden = data.count === 0;
      document.querySelector(".cart-link").setAttribute("aria-label", `Cart, ${data.count} items`);
      showToast(data.message);
      btn.textContent = "Added";
      setTimeout(() => { btn.textContent = label; btn.disabled = false; }, 1200);
    } catch (err) {
      form.submit();   // fall back to a normal page load
    }
  });
});

// Cart page: change quantity / remove items without reloading
function setCartBadge(count) {
  const badge = document.getElementById("cart-badge");
  badge.textContent = count;
  badge.hidden = count === 0;
  document.querySelector(".cart-link").setAttribute("aria-label", `Cart, ${count} items`);
}

function renderCart(data) {
  setCartBadge(data.count);

  if (data.empty) {
    const page = document.querySelector(".cart-page");
    const grid = page.querySelector(".cart-grid");
    const box = document.createElement("div");
    box.className = "empty";
    box.innerHTML = '<h3>Your cart is empty.</h3><p>Pick something warm from the <a href="' +
      page.dataset.shopUrl + '">shop</a>.</p>';
    grid.replaceWith(box);
    return;
  }

  for (const [id, info] of Object.entries(data.lines)) {
    const line = document.querySelector(`.line[data-line="${id}"]`);
    if (!line) continue;
    line.querySelector("[data-qty]").textContent = info.qty;
    line.querySelector("[data-total]").textContent = info.total;
    const [minus, plus] = line.querySelectorAll(".stepper button");
    minus.value = info.qty - 1;
    plus.value = info.qty + 1;
  }

  document.getElementById("sum-subtotal").textContent = data.subtotal;
  document.getElementById("sum-shipping").textContent = data.shipping;
  document.getElementById("sum-total").textContent = data.total;
  document.getElementById("bar-fill").style.width = data.progress + "%";
  document.getElementById("ship-meter").querySelector("p").innerHTML = data.to_free > 0
    ? `Add <strong>${data.to_free_fmt}</strong> more for free shipping.`
    : "<strong>You've unlocked free shipping.</strong>";
}

document.querySelectorAll("form.js-cart").forEach((form) => {
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const line = form.closest(".line");
    const body = new FormData(form);

    if (form.dataset.action === "update") {
      const current = parseInt(line.querySelector("[data-qty]").textContent, 10);
      const delta = parseInt(e.submitter?.dataset.delta || "0", 10);
      body.set("qty", current + delta);
    }

    line.classList.add("busy");
    try {
      const res = await fetch(form.action, {
        method: "POST",
        body,
        headers: { "X-Requested-With": "fetch" },
      });
      if (!res.ok) throw new Error("bad response");
      const data = await res.json();
      line.classList.remove("busy");

      if (data.removed) {
        line.classList.add("removing");
        setTimeout(() => { line.remove(); renderCart(data); }, 250);
        showToast("Item removed.");
      } else {
        renderCart(data);
      }
    } catch (err) {
      form.submit();   // fall back to a normal page load
    }
  });
});
