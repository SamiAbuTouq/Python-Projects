(() => {
  "use strict";

  const STATUSES = ["todo", "doing", "done"];
  let tasks = [];
  let filterPriority = "all";
  let query = "";
  let dragId = null;
  let editingId = null;

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

  // ------------------------------------------------------------- API
  async function api(url, method = "GET", body) {
    const res = await fetch(url, {
      method,
      headers: body ? { "Content-Type": "application/json" } : {},
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || "Something went wrong");
    }
    return res.status === 204 ? null : res.json();
  }

  async function load() {
    tasks = await api("/api/tasks");
    render();
  }

  // ------------------------------------------------------------- UI helpers
  function toast(msg) {
    const el = $("#toast");
    el.textContent = msg;
    el.classList.add("show");
    clearTimeout(toast.t);
    toast.t = setTimeout(() => el.classList.remove("show"), 2200);
  }

  function greeting() {
    const h = new Date().getHours();
    const part = h < 5 ? "Burning the midnight oil" : h < 12 ? "Good morning" : h < 18 ? "Good afternoon" : "Good evening";
    $("#greeting").textContent = `${part} — plan it, move it, finish it.`;
  }

  function matches(t) {
    if (filterPriority !== "all" && t.priority !== filterPriority) return false;
    const q = query.trim().toLowerCase();
    return !q || t.title.toLowerCase().includes(q) || (t.description || "").toLowerCase().includes(q);
  }

  function formatDue(iso) {
    const d = new Date(iso + "T00:00:00");
    const today = new Date(); today.setHours(0, 0, 0, 0);
    const overdue = d < today;
    return {
      text: "📅 " + d.toLocaleDateString(undefined, { month: "short", day: "numeric" }),
      overdue,
    };
  }

  function buildCard(t) {
    const card = document.createElement("article");
    card.className = `card ${t.priority}${t.status === "done" ? " is-done" : ""}`;
    card.draggable = true;
    card.dataset.id = t.id;

    const h = document.createElement("h4");
    h.textContent = t.title;
    card.appendChild(h);

    if (t.description) {
      const p = document.createElement("p");
      p.textContent = t.description;
      card.appendChild(p);
    }

    const meta = document.createElement("div");
    meta.className = "meta";
    const tag = document.createElement("span");
    tag.className = "tag";
    tag.textContent = t.priority;
    meta.appendChild(tag);
    if (t.due_date) {
      const { text, overdue } = formatDue(t.due_date);
      const due = document.createElement("span");
      due.className = "due" + (overdue && t.status !== "done" ? " overdue" : "");
      due.textContent = text;
      meta.appendChild(due);
    }
    card.appendChild(meta);

    card.addEventListener("click", () => openModal(t.id));
    card.addEventListener("dragstart", (e) => {
      dragId = t.id;
      card.classList.add("dragging");
      e.dataTransfer.effectAllowed = "move";
      e.dataTransfer.setData("text/plain", String(t.id));
    });
    card.addEventListener("dragend", () => {
      card.classList.remove("dragging");
      $$(".column").forEach((c) => c.classList.remove("over"));
      $$(".drop-line").forEach((l) => l.remove());
    });
    return card;
  }

  function render() {
    STATUSES.forEach((s) => {
      const list = $(`#list-${s}`);
      list.innerHTML = "";
      const all = tasks.filter((t) => t.status === s);
      all.filter(matches).forEach((t) => list.appendChild(buildCard(t)));
      $(`#c-${s}`).textContent = all.length;
    });

    const total = tasks.length;
    const done = tasks.filter((t) => t.status === "done").length;
    const doing = tasks.filter((t) => t.status === "doing").length;
    const pct = total ? Math.round((done / total) * 100) : 0;
    $("#s-total").textContent = total;
    $("#s-doing").textContent = doing;
    $("#s-done").textContent = done;
    $("#ring-text").textContent = pct + "%";
    $("#ring-bar").style.strokeDashoffset = 113.1 * (1 - pct / 100);
  }

  // ------------------------------------------------------------- drag & drop
  function afterElement(list, y) {
    const cards = [...list.querySelectorAll(".card:not(.dragging)")];
    return cards.reduce(
      (closest, el) => {
        const box = el.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        return offset < 0 && offset > closest.offset ? { offset, el } : closest;
      },
      { offset: Number.NEGATIVE_INFINITY, el: null }
    ).el;
  }

  $$(".column").forEach((col) => {
    const list = $(".list", col);

    col.addEventListener("dragover", (e) => {
      e.preventDefault();
      col.classList.add("over");
      $$(".drop-line").forEach((l) => l.remove());
      const line = document.createElement("div");
      line.className = "drop-line";
      const after = afterElement(list, e.clientY);
      after ? list.insertBefore(line, after) : list.appendChild(line);
    });

    col.addEventListener("dragleave", (e) => {
      if (!col.contains(e.relatedTarget)) {
        col.classList.remove("over");
        $$(".drop-line", col).forEach((l) => l.remove());
      }
    });

    col.addEventListener("drop", async (e) => {
      e.preventDefault();
      const status = col.dataset.status;
      const id = dragId;
      if (id == null) return;

      // Work out the new order of ids in this column
      const line = $(".drop-line", list);
      const ids = [...list.querySelectorAll(".card")]
        .map((c) => Number(c.dataset.id))
        .filter((x) => x !== id);
      let index = ids.length;
      if (line) {
        const before = [...list.children].slice(0, [...list.children].indexOf(line));
        index = before.filter((c) => c.classList.contains("card") && Number(c.dataset.id) !== id).length;
      }
      ids.splice(index, 0, id);

      const wasDone = tasks.find((t) => t.id === id).status === "done";
      // Optimistic update
      const moved = tasks.find((t) => t.id === id);
      moved.status = status;
      const others = tasks.filter((t) => t.status !== status || t.id === id);
      const colTasks = ids.map((i) => tasks.find((t) => t.id === i)).filter(Boolean);
      tasks = [...tasks.filter((t) => t.status !== status), ...colTasks];
      void others;
      render();
      dragId = null;

      try {
        await api("/api/reorder", "PUT", { status, ids });
        if (status === "done" && !wasDone) {
          toast("Nice work! 🎉");
          confetti();
        }
      } catch (err) {
        toast(err.message);
        load();
      }
    });
  });

  // ------------------------------------------------------------- quick add
  $$(".quick-add").forEach((form) => {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const input = $("input", form);
      const title = input.value.trim();
      if (!title) return;
      try {
        const t = await api("/api/tasks", "POST", { title, status: form.dataset.status });
        tasks.push(t);
        input.value = "";
        render();
      } catch (err) {
        toast(err.message);
      }
    });
  });

  // ------------------------------------------------------------- search + filters
  $("#search").addEventListener("input", (e) => { query = e.target.value; render(); });
  $("#filters").addEventListener("click", (e) => {
    const btn = e.target.closest(".chip");
    if (!btn) return;
    filterPriority = btn.dataset.p;
    $$(".chip").forEach((c) => c.classList.toggle("active", c === btn));
    render();
  });

  // ------------------------------------------------------------- modal
  const modal = $("#modal");
  const form = $("#edit-form");

  function openModal(id) {
    const t = tasks.find((x) => x.id === id);
    if (!t) return;
    editingId = id;
    form.title.value = t.title;
    form.description.value = t.description || "";
    form.priority.value = t.priority;
    form.status.value = t.status;
    form.due_date.value = t.due_date || "";
    modal.hidden = false;
    form.title.focus();
  }
  const closeModal = () => { modal.hidden = true; editingId = null; if (typeof resetDeleteBtn === "function") resetDeleteBtn(); };

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const body = {
      title: form.title.value,
      description: form.description.value,
      priority: form.priority.value,
      status: form.status.value,
      due_date: form.due_date.value || null,
    };
    try {
      const prev = tasks.find((t) => t.id === editingId);
      const updated = await api(`/api/tasks/${editingId}`, "PATCH", body);
      tasks = tasks.map((t) => (t.id === editingId ? updated : t));
      if (prev.status !== "done" && updated.status === "done") { toast("Nice work! 🎉"); confetti(); }
      else toast("Saved ✓");
      closeModal();
      render();
    } catch (err) {
      toast(err.message);
    }
  });

  const deleteBtn = $("#delete-btn");
  const resetDeleteBtn = () => {
    clearTimeout(resetDeleteBtn.t);
    deleteBtn.dataset.confirm = "";
    deleteBtn.textContent = "Delete";
  };

  deleteBtn.addEventListener("click", async () => {
    // First click arms the button, second click deletes (no native confirm()).
    if (!deleteBtn.dataset.confirm) {
      deleteBtn.dataset.confirm = "1";
      deleteBtn.textContent = "Click again to confirm";
      resetDeleteBtn.t = setTimeout(resetDeleteBtn, 3000);
      return;
    }
    resetDeleteBtn();
    const id = editingId;
    try {
      await api(`/api/tasks/${id}`, "DELETE");
    } catch (err) {
      // 404 means it is already gone on the server - just sync the UI.
      if (err.message !== "Task not found.") {
        toast(err.message);
        return;
      }
    }
    tasks = tasks.filter((t) => t.id !== id);
    closeModal();
    render();
    toast("Task deleted");
  });

  $("#cancel-btn").addEventListener("click", closeModal);
  modal.addEventListener("click", (e) => { if (e.target === modal) closeModal(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !modal.hidden) closeModal(); });

  // ------------------------------------------------------------- confetti
  function confetti() {
    const canvas = $("#confetti");
    const ctx = canvas.getContext("2d");
    canvas.width = innerWidth;
    canvas.height = innerHeight;
    const colors = ["#8b5cf6", "#22d3ee", "#fbbf24", "#fb7185", "#34d399", "#ffffff"];
    const bits = Array.from({ length: 140 }, () => ({
      x: innerWidth / 2 + (Math.random() - 0.5) * 200,
      y: innerHeight * 0.55,
      vx: (Math.random() - 0.5) * 14,
      vy: -Math.random() * 15 - 5,
      s: Math.random() * 7 + 4,
      r: Math.random() * Math.PI,
      vr: (Math.random() - 0.5) * 0.4,
      c: colors[(Math.random() * colors.length) | 0],
    }));
    let frames = 0;
    (function tick() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      bits.forEach((b) => {
        b.vy += 0.45; b.x += b.vx; b.y += b.vy; b.r += b.vr;
        ctx.save();
        ctx.translate(b.x, b.y);
        ctx.rotate(b.r);
        ctx.fillStyle = b.c;
        ctx.globalAlpha = Math.max(0, 1 - frames / 110);
        ctx.fillRect(-b.s / 2, -b.s / 2, b.s, b.s * 0.6);
        ctx.restore();
      });
      if (++frames < 110) requestAnimationFrame(tick);
      else ctx.clearRect(0, 0, canvas.width, canvas.height);
    })();
  }

  greeting();
  load();
})();