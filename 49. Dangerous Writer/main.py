import math
import random
import time
import tkinter as tk
import tkinter.font as tkfont

LIMIT_OPTIONS = (5, 10, 15)   # selectable inactivity limits (seconds)
DEFAULT_LIMIT = 5
FADE_TIME = 0.5   # text dissolves
BURN_TIME = 1.5   # total length of the wipe animation

# Cursor blink (ms), driven by our own timer (Tk built-in blink is off, since reconfiguring every frame keeps resetting it).
CURSOR_ON_MS = 500
CURSOR_OFF_MS = 500

# ---------- palette (RGB tuples) ----------
BG_TOP = (9, 11, 18)
BG_BOT = (22, 14, 34)
BG_MID = (15, 12, 26)
CARD = (16, 19, 28)
TEXT = (232, 235, 244)
MUTED = (104, 112, 138)
IDLE = (128, 112, 255)   # violet while waiting
TEAL = (38, 232, 192)
AMBER = (255, 178, 36)
RED = (255, 60, 92)


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def hx(c):
    return "#%02x%02x%02x" % tuple(int(max(0, min(255, v))) for v in c)


def danger_color(d):
    return mix(TEAL, AMBER, d * 2) if d < 0.5 else mix(AMBER, RED, (d - 0.5) * 2)


def pick(options, fallback):
    families = set(tkfont.families())
    for name in options:
        if name in families:
            return name
    return fallback


def rounded(canvas, x1, y1, x2, y2, r, **kw):
    r = min(r, (x2 - x1) / 2, (y2 - y1) / 2)
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return canvas.create_polygon(pts, smooth=True, **kw)


class DangerousWriter(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Dangerous Writer")
        self.geometry("980x700")
        self.minsize(720, 520)

        ui = pick(["Segoe UI", "SF Pro Display", "Helvetica Neue", "Inter", "DejaVu Sans"], "Helvetica")
        serif = pick(["Georgia", "Palatino Linotype", "Charter", "Times New Roman", "DejaVu Serif"], "Times")
        mono = pick(["JetBrains Mono", "Consolas", "Menlo", "DejaVu Sans Mono"], "Courier")
        self.f_title = tkfont.Font(family=ui, size=22, weight="bold")
        self.f_small = tkfont.Font(family=ui, size=11)
        self.f_pill = tkfont.Font(family=ui, size=11, weight="bold")
        self.f_timer = tkfont.Font(family=mono, size=14, weight="bold")
        self.f_text = tkfont.Font(family=serif, size=18)

        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0, bg=hx(BG_TOP))
        self.canvas.pack(fill="both", expand=True)

        self.editor = tk.Text(
            self.canvas, font=self.f_text, bg=hx(CARD), fg=hx(TEXT), wrap="word",
            relief="flat", bd=0, highlightthickness=0, padx=0, pady=0,
            insertwidth=2, spacing2=8, undo=False, selectbackground="#2b3556",
            insertbackground=hx(IDLE),
            insertontime=1, insertofftime=0,   # built-in blink off; we blink manually
        )
        self.win = self.canvas.create_window(0, 0, window=self.editor, anchor="nw")

        self.limit = float(DEFAULT_LIMIT)
        self.W = self.H = 0
        self.mode = "idle"          # idle | writing | burning
        self.last_key = None
        self.burn_start = 0.0
        self.cleared = False
        self.after_burn = False
        self.words = 0
        self.embers = []
        self.dust = []
        self.remaining, self.danger = self.limit, 0.0
        self.accent, self.glow = IDLE, 0.3
        self.dx = self.dy = 0.0
        self.msg, self.msg_color = "", MUTED
        self.blink_origin = time.perf_counter()

        self.canvas.bind("<Configure>", self.on_resize)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Motion>", self.on_motion)
        self.editor.bind("<Key>", self.on_key)
        self.editor.bind("<KeyRelease>", self.count_words)
        self.editor.bind("<<Paste>>", self.on_paste)
        self.editor.focus_set()

        self.prev = time.perf_counter()
        self.after(16, self.frame)

    # ---------- layout ----------
    def card_rect(self):
        return 40, 112, self.W - 40, self.H - 70

    def pill_rects(self):
        """Hit boxes for the 5s / 10s / 15s selector, to the left of the timer ring."""
        w, h, gap = 54, 30, 6
        total = len(LIMIT_OPTIONS) * w + (len(LIMIT_OPTIONS) - 1) * gap
        x = self.W - 166 - total
        cy = 62
        rects = []
        for v in LIMIT_OPTIONS:
            rects.append((x, cy - h / 2, x + w, cy + h / 2, v))
            x += w + gap
        return rects

    def on_resize(self, e):
        self.W, self.H = e.width, e.height
        c = self.canvas
        c.delete("static")
        n = 96
        for i in range(n):
            c.create_rectangle(0, self.H * i / n, self.W, self.H * (i + 1) / n + 1,
                               fill=hx(mix(BG_TOP, BG_BOT, i / n)), outline="", tags="static")
        c.create_text(40, 44, text="DANGEROUS", anchor="w", font=self.f_title,
                      fill=hx(TEXT), tags="static")
        w = self.f_title.measure("DANGEROUS ")
        c.create_text(40 + w, 44, text="WRITER", anchor="w", font=self.f_title,
                      fill=hx(IDLE), tags="static")
        c.tag_lower("static")

        x1, y1, x2, y2 = self.card_rect()
        c.itemconfigure(self.win, width=max(50, x2 - x1 - 64), height=max(50, y2 - y1 - 52))

        if not self.dust:
            for _ in range(45):
                self.dust.append(dict(
                    x=random.uniform(0, self.W), y=random.uniform(0, self.H),
                    vy=random.uniform(6, 18), s=random.uniform(0.8, 2.0),
                    ph=random.uniform(0, 6.28)))

    # ---------- input ----------
    def pill_at(self, x, y):
        for x1, y1, x2, y2, v in self.pill_rects():
            if x1 <= x <= x2 and y1 <= y <= y2:
                return v
        return None

    def on_click(self, e):
        v = self.pill_at(e.x, e.y)
        # the limit can only be changed while waiting to start
        if v is not None and self.mode == "idle":
            self.limit = float(v)
        self.editor.focus_set()

    def on_motion(self, e):
        hand = self.mode == "idle" and self.pill_at(e.x, e.y) is not None
        self.canvas.config(cursor="hand2" if hand else "")

    def on_key(self, e):
        if self.mode == "burning":
            return "break"
        counts = (e.char and (e.char.isprintable() or e.char in "\r\n\t")) \
            or e.keysym in ("BackSpace", "Delete", "Return")
        if counts:
            self.touch()

    def on_paste(self, e):
        if self.mode == "burning":
            return "break"
        self.touch()
        self.after_idle(self.count_words)

    def touch(self):
        self.last_key = time.perf_counter()
        self.blink_origin = self.last_key   # cursor stays solid right after typing
        self.after_burn = False
        if self.mode == "idle":
            self.mode = "writing"

    def count_words(self, e=None):
        self.words = len(self.editor.get("1.0", "end").split())

    # ---------- state machine ----------
    def advance(self, now):
        if self.mode == "idle":
            self.remaining, self.danger = self.limit, 0.0
            self.accent = IDLE
            self.glow = 0.30 + 0.12 * math.sin(now * 2.0)
            self.dx = self.dy = 0.0
            if self.after_burn:
                self.msg, self.msg_color = "Everything is gone. Start again.", mix(MUTED, RED, 0.6)
            else:
                self.msg = f"Start typing. Stop for {int(self.limit)} seconds and it all disappears."
                self.msg_color = MUTED

        elif self.mode == "writing":
            elapsed = now - self.last_key
            self.remaining = max(0.0, self.limit - elapsed)
            self.danger = min(1.0, elapsed / self.limit)
            d = self.danger
            self.accent = danger_color(d)
            self.glow = 0.45 + 0.4 * d + 0.12 * d * math.sin(now * (8 + 16 * d))
            self.dx = self.dy = 0.0
            if d < 0.4:
                self.msg = "Keep going."
            elif d < 0.75:
                self.msg = "Don't stop."
            else:
                self.msg = "WRITE SOMETHING. NOW."
            self.msg_color = mix(MUTED, self.accent, 0.4 + d * 0.6)
            if self.remaining <= 0:
                self.start_burn(now)

        else:  # burning
            t = now - self.burn_start
            self.remaining, self.danger = 0.0, 1.0
            self.accent = RED
            self.glow = max(0.2, 1.0 - t / BURN_TIME)
            amp = max(0.0, 1 - t / 0.4) * 12
            self.dx = amp * math.sin(t * 95)
            self.dy = amp * 0.4 * math.cos(t * 70)
            self.msg, self.msg_color = "Everything is gone.", RED
            if t < FADE_TIME:
                self.editor.config(fg=hx(mix(TEXT, CARD, t / FADE_TIME)))
            elif not self.cleared:
                self.cleared = True
                self.editor.delete("1.0", "end")
                self.words = 0
                self.canvas.itemconfigure(self.win, state="hidden")
                self.spawn_embers(220)
            if t >= BURN_TIME:
                self.finish_burn()

    def start_burn(self, now):
        self.mode = "burning"
        self.burn_start = now
        self.cleared = False

    def finish_burn(self):
        self.canvas.itemconfigure(self.win, state="normal")
        self.editor.config(fg=hx(TEXT))
        self.editor.focus_set()
        self.mode = "idle"
        self.last_key = None
        self.after_burn = True
        self.dx = self.dy = 0.0

    def spawn_embers(self, n):
        x1, y1, x2, y2 = self.card_rect()
        for _ in range(n):
            self.embers.append(dict(
                x=random.uniform(x1 + 10, x2 - 10), y=random.uniform(y1 + 30, y2 - 10),
                vx=random.uniform(-30, 30), vy=-random.uniform(40, 230),
                life=random.uniform(0.7, 1.3), age=0.0, size=random.uniform(1.5, 4.5),
                hue=random.random(), ph=random.uniform(0, 6.28)))

    # ---------- drawing ----------
    def ring(self, cx, cy, r, width, color, frac):
        box = (cx - r, cy - r, cx + r, cy + r)
        if frac >= 0.999:
            self.canvas.create_oval(*box, outline=color, width=width, tags="dyn")
        elif frac > 0.001:
            self.canvas.create_arc(*box, start=90, extent=360 * frac, style="arc",
                                   outline=color, width=width, tags="dyn")

    def draw_pills(self):
        c = self.canvas
        unlocked = self.mode == "idle"
        for x1, y1, x2, y2, v in self.pill_rects():
            selected = int(self.limit) == v
            if selected:
                fill = mix(CARD, IDLE, 0.45 if unlocked else 0.2)
                edge = mix(CARD, IDLE, 0.9 if unlocked else 0.35)
                fg = mix(TEXT, CARD, 0.0 if unlocked else 0.4)
            else:
                fill = CARD
                edge = mix(CARD, MUTED, 0.45 if unlocked else 0.2)
                fg = mix(MUTED, CARD, 0.0 if unlocked else 0.5)
            rounded(c, x1, y1, x2, y2, 15, fill=hx(fill), outline=hx(edge), width=1.2, tags="dyn")
            c.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=f"{v}s", font=self.f_pill,
                          fill=hx(fg), tags="dyn")

    def draw(self, now, dt):
        c = self.canvas
        c.delete("dyn")
        W, H = self.W, self.H
        acc, glow = self.accent, self.glow

        # drifting dust
        for p in self.dust:
            p["y"] -= p["vy"] * dt
            if p["y"] < -5:
                p["y"], p["x"] = H + 5, random.uniform(0, W)
            tw = 0.5 + 0.5 * math.sin(now * 1.5 + p["ph"])
            col = hx(mix(BG_MID, acc, 0.10 + 0.18 * tw))
            c.create_oval(p["x"] - p["s"], p["y"] - p["s"], p["x"] + p["s"], p["y"] + p["s"],
                          fill=col, outline="", tags="dyn")

        # glowing card
        x1, y1, x2, y2 = self.card_rect()
        x1 += self.dx; x2 += self.dx; y1 += self.dy; y2 += self.dy
        for k in range(10, 0, -1):
            g = k * 2.2
            col = mix(BG_MID, acc, glow * (1 - k / 11) ** 2 * 0.9)
            rounded(c, x1 - g, y1 - g, x2 + g, y2 + g, 22 + g, fill=hx(col), outline="", tags="dyn")
        rounded(c, x1, y1, x2, y2, 22, fill=hx(CARD),
                outline=hx(mix(CARD, acc, 0.35 + 0.4 * glow)), width=1.5, tags="dyn")
        c.coords(self.win, x1 + 32, y1 + 26)

        # timer selector
        self.draw_pills()

        # timer ring
        cx, cy, r = W - 94, 62, 38
        frac = self.remaining / self.limit
        for k in range(1, 5):
            self.ring(cx, cy, r, 6 + k * 6, hx(mix(BG_TOP, acc, glow * 0.07 * (5 - k))), frac)
        c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=hx(mix(CARD, MUTED, 0.35)),
                      width=6, tags="dyn")
        self.ring(cx, cy, r, 6, hx(acc), frac)
        c.create_text(cx, cy, text=f"{self.remaining:.1f}", font=self.f_timer,
                      fill=hx(mix(TEXT, acc, 0.5)), tags="dyn")

        # status + word count
        c.create_text(42, 84, text=self.msg, anchor="w", font=self.f_small,
                      fill=hx(self.msg_color), tags="dyn")
        c.create_text(44, H - 38, anchor="w", font=self.f_small, fill=hx(MUTED), tags="dyn",
                      text=f"{self.words} word{'s' if self.words != 1 else ''}")

        # embers
        alive = []
        for p in self.embers:
            p["age"] += dt
            if p["age"] >= p["life"]:
                continue
            p["x"] += (p["vx"] + 25 * math.sin(p["age"] * 5 + p["ph"])) * dt
            p["y"] += p["vy"] * dt
            t = p["age"] / p["life"]
            col = hx(mix(mix(AMBER, RED, p["hue"]), BG_MID, t ** 1.4))
            s = p["size"] * (1 - 0.7 * t)
            c.create_oval(p["x"] - s, p["y"] - s, p["x"] + s, p["y"] + s,
                          fill=col, outline="", tags="dyn")
            alive.append(p)
        self.embers = alive

        # slow manual cursor blink
        phase = ((now - self.blink_origin) * 1000) % (CURSOR_ON_MS + CURSOR_OFF_MS)
        self.editor.config(insertbackground=hx(acc if phase < CURSOR_ON_MS else CARD))

    def frame(self):
        now = time.perf_counter()
        dt = min(0.05, now - self.prev)
        self.prev = now
        if self.W > 10:
            self.advance(now)
            self.draw(now, dt)
        self.after(16, self.frame)


if __name__ == "__main__":
    try:  # crisp text on high-DPI Windows screens
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    DangerousWriter().mainloop()