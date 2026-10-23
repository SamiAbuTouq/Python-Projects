"""
TYPEFLOW - a typing speed test / trainer built with Tkinter.

Features
  * Random passages from a built-in library (several are stitched together per round)
  * Live WPM, accuracy and countdown with a progress bar
  * Per-word colouring (correct / wrong) and per-letter feedback on the current word
  * Selectable round length (30 / 60 / 120 seconds)
  * Persistent high-score table saved next to the script (typing_scores.json)
  * Keyboard friendly: just start typing, SPACE commits a word, ESC / TAB restarts

Run:  python typing_speed_test.py      (Python 3.8+, no extra packages needed)
"""

import json
import random
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import font as tkfont

# --------------------------------------------------------------------------- #
#  Data
# --------------------------------------------------------------------------- #
PASSAGES = [
    "The morning train slid out of the station while the city was still half asleep. "
    "Steam curled from paper cups, and strangers stared at their reflections in the dark windows, "
    "each lost in thoughts they would never share with anyone else on board.",
    "Programming is mostly the art of breaking a large problem into smaller ones until each piece "
    "is simple enough to solve. The trick is patience: write a little, run it, read the error, "
    "and try again until the screen finally agrees with your plan.",
    "Far beyond the last village the road turned to gravel, then to dust, then to nothing at all. "
    "The travelers pressed on anyway, guided by a map that was older than their grandparents "
    "and a stubborn belief that the sea was waiting just over the ridge.",
    "A good cup of coffee needs three things: fresh beans, clean water, and a little attention. "
    "Rush any of them and the result tastes flat, but give each step a moment and the whole "
    "kitchen fills with a warm smell that makes the day feel possible.",
    "Every keyboard tells a quiet story. The worn letters show which words you reach for most, "
    "and the shiny keys reveal the ones you avoid. Practice is simply the habit of letting your "
    "fingers learn what your mind already knows.",
    "The old lighthouse keeper climbed the spiral stairs each evening, counting the steps out loud "
    "as he had done for forty years. At the top he lit the great lamp, and its beam swept "
    "across the water like a slow and patient heartbeat.",
    "Space is not empty; it is full of light that has been traveling for longer than our species "
    "has existed. When you look up at night, you are reading letters written in a language of "
    "fire, posted long ago and only now arriving at your window.",
    "Good design hides in plain sight. A door handle that tells you to pull, a button that "
    "feels satisfying to press, a menu that is exactly where you expected it to be. You only "
    "notice the craft when it is missing and everything suddenly feels hard.",
    "The market woke up before the sun did. Crates of oranges were stacked into bright pyramids, "
    "fishermen shouted their prices over the noise, and a small boy darted between the stalls "
    "clutching a coin as if it were the key to the entire world.",
    "Learning a new skill feels clumsy at first, and that is perfectly normal. Progress arrives "
    "in tiny steps that are easy to miss, but if you stay consistent for a few weeks, you will "
    "look back and barely recognize the beginner you used to be.",
    "Rain tapped softly on the roof while the whole house settled into a comfortable silence. "
    "A cat curled up on the windowsill, a book lay open on the table, and for a few precious "
    "hours nothing in the world needed to be done in a hurry.",
    "Software is never truly finished. There is always another feature to add, another edge case "
    "to handle, another line that could be simpler. The best developers learn to ship, listen, "
    "and improve, rather than waiting for a perfection that never comes.",
]

DURATIONS = (30, 60, 120)
SCORE_FILE = Path(__file__).with_name("typing_scores.json")

# Colour palette
BG = "#0b0e17"
CARD = "#141a2b"
CARD_2 = "#1b2238"
BORDER = "#2a3150"
TEXT = "#e8ebf5"
DIM = "#5d6685"
ACCENT = "#7c5cff"
ACCENT_HOVER = "#947bff"
TEAL = "#00e5c3"
RED = "#ff5c7a"
AMBER = "#ffb84d"


def pick_font(candidates, fallback="TkFixedFont"):
    available = set(tkfont.families())
    for name in candidates:
        if name in available:
            return name
    return fallback


def rating_for(wpm):
    if wpm < 20:
        return "Just getting started"
    if wpm < 40:
        return "Warming up"
    if wpm < 60:
        return "Solid typist (above average!)"
    if wpm < 80:
        return "Fast fingers"
    if wpm < 100:
        return "Speed demon"
    return "Keyboard legend"


# --------------------------------------------------------------------------- #
#  Small UI helpers
# --------------------------------------------------------------------------- #
class FlatButton(tk.Label):
    """A label-based button so colours render the same on Windows, macOS and Linux."""

    def __init__(self, parent, text, command, bg=ACCENT, hover=ACCENT_HOVER,
                 fg="white", font=None, padx=20, pady=9):
        super().__init__(parent, text=text, bg=bg, fg=fg, font=font,
                         padx=padx, pady=pady, cursor="hand2")
        self.base_bg, self.hover_bg, self.command = bg, hover, command
        self.bind("<Enter>", lambda _e: self.configure(bg=self.hover_bg))
        self.bind("<Leave>", lambda _e: self.configure(bg=self.base_bg))
        self.bind("<Button-1>", lambda _e: self.command())

    def set_colors(self, bg, hover, fg="white"):
        self.base_bg, self.hover_bg = bg, hover
        self.configure(bg=bg, fg=fg)


class ScoreBoard:
    """Loads / saves the high-score table."""

    def __init__(self, path):
        self.path = path
        self.scores = self._load()

    def _load(self):
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []
        if not isinstance(data, list):
            return []
        clean = []
        for s in data:  # keep only well-formed entries, ignore anything else
            if isinstance(s, dict) and isinstance(s.get("wpm"), (int, float)):
                clean.append({
                    "wpm": s["wpm"],
                    "acc": s.get("acc", 0),
                    "duration": s.get("duration", 60),
                    "date": s.get("date", ""),
                })
        return clean

    def add(self, wpm, accuracy, duration):
        entry = {
            "wpm": round(wpm, 1),
            "acc": round(accuracy, 1),
            "duration": duration,
            "date": datetime.now().strftime("%d %b %Y"),
        }
        previous_best = self.best()
        self.scores.append(entry)
        self.scores.sort(key=lambda s: s["wpm"], reverse=True)
        self.scores = self.scores[:10]
        try:
            self.path.write_text(json.dumps(self.scores, indent=2), encoding="utf-8")
        except OSError:
            pass  # not fatal: scores just won't persist
        return entry["wpm"] > previous_best

    def best(self):
        return max((s["wpm"] for s in self.scores), default=0)


# --------------------------------------------------------------------------- #
#  Main application
# --------------------------------------------------------------------------- #
class TypeFlow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TYPEFLOW - Typing Speed Test")
        self.configure(bg=BG)
        self.geometry("960x700")
        self.minsize(820, 620)

        mono = pick_font(["JetBrains Mono", "Cascadia Code", "Consolas", "Menlo",
                          "DejaVu Sans Mono", "Courier New"])
        sans = pick_font(["Segoe UI", "Helvetica Neue", "Inter", "Arial", "DejaVu Sans"],
                         fallback="TkDefaultFont")
        self.f_logo = (sans, 26, "bold")
        self.f_small = (sans, 10)
        self.f_label = (sans, 9, "bold")
        self.f_stat = (mono, 28, "bold")
        self.f_text = (mono, 20)
        self.f_input = (mono, 18)
        self.f_btn = (sans, 11, "bold")
        self.f_big = (mono, 64, "bold")
        self.f_h2 = (sans, 16, "bold")

        self.scoreboard = ScoreBoard(SCORE_FILE)
        self.duration = 60
        self.overlay = None
        self.after_id = None

        self._build_ui()
        self.bind("<Escape>", lambda _e: self.new_round())
        self.new_round()

    # ------------------------------------------------------------------ UI --
    def _build_ui(self):
        root = tk.Frame(self, bg=BG)
        root.pack(fill="both", expand=True, padx=34, pady=26)
        self.root_frame = root

        # Header
        header = tk.Frame(root, bg=BG)
        header.pack(fill="x")
        logo = tk.Frame(header, bg=BG)
        logo.pack(side="left")
        tk.Label(logo, text="TYPE", font=self.f_logo, fg=TEXT, bg=BG).pack(side="left")
        tk.Label(logo, text="FLOW", font=self.f_logo, fg=ACCENT, bg=BG).pack(side="left")
        tk.Label(header, text="  how fast can you really type?", font=self.f_small,
                 fg=DIM, bg=BG).pack(side="left", pady=(10, 0))
        FlatButton(header, "High Scores", self.show_scores, bg=CARD_2, hover=BORDER,
                   fg=TEXT, font=self.f_btn).pack(side="right")

        # Stat cards
        stats = tk.Frame(root, bg=BG)
        stats.pack(fill="x", pady=(22, 12))
        self.time_val = self._stat_card(stats, "TIME", TEXT)
        self.wpm_val = self._stat_card(stats, "WPM", TEAL)
        self.acc_val = self._stat_card(stats, "ACCURACY", AMBER)
        self.best_val = self._stat_card(stats, "BEST", ACCENT_HOVER)

        # Progress bar
        self.bar = tk.Canvas(root, height=6, bg=CARD, highlightthickness=0)
        self.bar.pack(fill="x", pady=(0, 16))

        # Passage display
        text_card = tk.Frame(root, bg=CARD, highlightthickness=1,
                             highlightbackground=BORDER)
        text_card.pack(fill="both", expand=True)
        self.text = tk.Text(text_card, wrap="word", font=self.f_text, bg=CARD, fg=DIM,
                            relief="flat", bd=0, padx=28, pady=22, height=7,
                            spacing1=4, spacing2=6, cursor="arrow",
                            highlightthickness=0, insertwidth=0)
        self.text.pack(fill="both", expand=True)
        self.text.tag_configure("ok", foreground=TEAL)
        self.text.tag_configure("bad", foreground=RED, underline=True)
        self.text.tag_configure("current", background=CARD_2, foreground=TEXT)
        self.text.tag_configure("typed_ok", foreground=TEAL)
        self.text.tag_configure("typed_bad", foreground="white", background="#7a2038")
        self.text.bind("<Button-1>", lambda _e: (self.entry.focus_set(), "break")[1])

        # Input
        self.var = tk.StringVar()
        self.entry = tk.Entry(root, textvariable=self.var, font=self.f_input, bg="#0f1322",
                              fg=TEXT, insertbackground=ACCENT, relief="flat",
                              highlightthickness=2, highlightbackground=BORDER,
                              highlightcolor=ACCENT, justify="center")
        self.entry.pack(fill="x", pady=(16, 0), ipady=10)
        self.entry.bind("<<Paste>>", lambda _e: "break")      # no cheating :)
        self.entry.bind("<Control-v>", lambda _e: "break")
        self.entry.bind("<Tab>", lambda _e: (self.new_round(), "break")[1])
        self.var.trace_add("write", self._on_type)

        # Footer
        footer = tk.Frame(root, bg=BG)
        footer.pack(fill="x", pady=(16, 0))
        tk.Label(footer, text="ROUND", font=self.f_label, fg=DIM, bg=BG).pack(side="left")
        self.dur_buttons = {}
        for d in DURATIONS:
            b = FlatButton(footer, f"{d}s", lambda d=d: self.set_duration(d),
                           bg=CARD_2, hover=BORDER, fg=TEXT, font=self.f_btn,
                           padx=14, pady=6)
            b.pack(side="left", padx=(8, 0))
            self.dur_buttons[d] = b
        tk.Label(footer, text="SPACE = next word   |   ESC / TAB = restart",
                 font=self.f_small, fg=DIM, bg=BG).pack(side="left", padx=24)
        FlatButton(footer, "Restart", self.new_round, font=self.f_btn).pack(side="right")

        self.bar.bind("<Configure>", lambda _e: self._draw_bar(self._bar_frac))
        self._bar_frac = 1.0
        self._refresh_duration_buttons()

    def _stat_card(self, parent, title, color):
        card = tk.Frame(parent, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        card.pack(side="left", expand=True, fill="x", padx=5)
        tk.Label(card, text=title, font=self.f_label, fg=DIM, bg=CARD).pack(pady=(12, 0))
        value = tk.Label(card, text="0", font=self.f_stat, fg=color, bg=CARD)
        value.pack(pady=(0, 10))
        return value

    def _draw_bar(self, frac):
        self._bar_frac = frac
        w = self.bar.winfo_width()
        self.bar.delete("all")
        color = RED if frac < 0.2 else (AMBER if frac < 0.45 else ACCENT)
        self.bar.create_rectangle(0, 0, max(0, w * frac), 6, fill=color, width=0)

    def _refresh_duration_buttons(self):
        for d, b in self.dur_buttons.items():
            if d == self.duration:
                b.set_colors(ACCENT, ACCENT_HOVER)
            else:
                b.set_colors(CARD_2, BORDER, fg=TEXT)

    # ---------------------------------------------------------- Round logic --
    def set_duration(self, seconds):
        self.duration = seconds
        self._refresh_duration_buttons()
        self.new_round()

    def new_round(self):
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None
        self._close_overlay()

        passages = random.sample(PASSAGES, 3)
        self.words = " ".join(passages).split()
        # start offset of every word inside the Text widget
        self.offsets, pos = [], 0
        for w in self.words:
            self.offsets.append(pos)
            pos += len(w) + 1

        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", " ".join(self.words))
        self.text.configure(state="disabled")
        for tag in ("ok", "bad", "current", "typed_ok", "typed_bad"):
            self.text.tag_remove(tag, "1.0", "end")
        self.text.yview_moveto(0)

        self.idx = 0
        self.started = False
        self.finished = False
        self.start_time = 0.0
        self.correct_chars = 0
        self.correct_words = 0
        self.typed_chars = 0
        self.matched_chars = 0

        self.entry.configure(state="normal")
        self.var.set("")
        self.entry.focus_set()

        self.time_val.configure(text=str(self.duration), fg=TEXT)
        self.wpm_val.configure(text="0")
        self.acc_val.configure(text="100%")
        self.best_val.configure(text=str(int(self.scoreboard.best())))
        self._draw_bar(1.0)
        self._mark_current()

    def _range(self, i):
        start = f"1.0+{self.offsets[i]}c"
        end = f"1.0+{self.offsets[i] + len(self.words[i])}c"
        return start, end

    def _mark_current(self):
        s, e = self._range(self.idx)
        self.text.tag_add("current", s, e)
        self.text.see(s)

    def _start(self):
        self.started = True
        self.start_time = time.time()
        self._tick()

    def _on_type(self, *_):
        if self.finished:
            return
        value = self.var.get()
        if not self.started and value.strip():
            self._start()
        if value.endswith(" "):
            typed = value.strip()
            self.var.set("")
            if typed:
                self._commit(typed)
            return
        self._show_progress_in_word(value)

    def _show_progress_in_word(self, typed):
        """Colour each letter of the current word as the user types it."""
        if self.idx >= len(self.words):
            return
        word = self.words[self.idx]
        start, end = self._range(self.idx)
        self.text.tag_remove("typed_ok", start, end)
        self.text.tag_remove("typed_bad", start, end)
        for i, ch in enumerate(typed[:len(word)]):
            a, b = f"{start}+{i}c", f"{start}+{i + 1}c"
            self.text.tag_add("typed_ok" if ch == word[i] else "typed_bad", a, b)
        if len(typed) > len(word):  # overshoot -> flag the last letter
            self.text.tag_add("typed_bad", f"{end}-1c", end)

    def _commit(self, typed):
        word = self.words[self.idx]
        start, end = self._range(self.idx)
        for tag in ("current", "typed_ok", "typed_bad"):
            self.text.tag_remove(tag, start, end)

        self.typed_chars += max(len(typed), len(word))
        self.matched_chars += sum(a == b for a, b in zip(typed, word))
        if typed == word:
            self.correct_words += 1
            self.correct_chars += len(word) + 1       # +1 for the space
            self.text.tag_add("ok", start, end)
        else:
            self.text.tag_add("bad", start, end)

        self.idx += 1
        if self.idx >= len(self.words):
            self._finish()
            return
        self._mark_current()
        self._update_stats()

    # ------------------------------------------------------------- Stats ----
    def _elapsed(self):
        return time.time() - self.start_time if self.started else 0.0

    def _wpm(self, elapsed):
        if elapsed < 1:
            return 0.0
        return (self.correct_chars / 5) / (elapsed / 60)       # standard: 5 chars = 1 word

    def _accuracy(self):
        if self.typed_chars == 0:
            return 100.0
        return 100.0 * self.matched_chars / self.typed_chars

    def _update_stats(self):
        self.wpm_val.configure(text=str(int(self._wpm(self._elapsed()))))
        self.acc_val.configure(text=f"{int(self._accuracy())}%")

    def _tick(self):
        if self.finished:
            return
        remaining = self.duration - self._elapsed()
        if remaining <= 0:
            self._finish()
            return
        self.time_val.configure(text=str(int(remaining) + 1),
                                fg=RED if remaining < 10 else TEXT)
        self._draw_bar(remaining / self.duration)
        self._update_stats()
        self.after_id = self.after(100, self._tick)

    def _finish(self):
        if self.finished:
            return
        self.finished = True
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None
        elapsed = min(self._elapsed(), self.duration)
        wpm = (self.correct_chars / 5) / (max(elapsed, 1) / 60)
        acc = self._accuracy()
        self.time_val.configure(text="0", fg=RED)
        self._draw_bar(0)
        self.wpm_val.configure(text=str(int(wpm)))
        self.acc_val.configure(text=f"{int(acc)}%")
        self.entry.configure(state="disabled")
        new_best = self.scoreboard.add(wpm, acc, self.duration)
        self.best_val.configure(text=str(int(self.scoreboard.best())))
        self._show_overlay(result=(wpm, acc, new_best))

    # ------------------------------------------------------------ Overlay ---
    def _close_overlay(self):
        if self.overlay is not None:
            self.overlay.destroy()
            self.overlay = None
        self.unbind("<Return>")

    def show_scores(self):
        if self.started and not self.finished:
            return  # don't interrupt a round
        self._close_overlay()
        self._show_overlay(result=None)

    def _show_overlay(self, result):
        self._close_overlay()
        box = tk.Frame(self.root_frame, bg=CARD, highlightthickness=2,
                       highlightbackground=ACCENT)
        box.place(relx=0.5, rely=0.5, anchor="center", width=560)
        self.overlay = box

        if result:
            wpm, acc, new_best = result
            tk.Label(box, text="TIME'S UP", font=self.f_label, fg=DIM, bg=CARD).pack(pady=(24, 0))
            tk.Label(box, text=f"{int(wpm)}", font=self.f_big, fg=TEAL, bg=CARD).pack()
            tk.Label(box, text="WORDS PER MINUTE", font=self.f_label, fg=DIM, bg=CARD).pack()
            tk.Label(box, text=rating_for(wpm), font=self.f_h2, fg=TEXT, bg=CARD).pack(pady=(12, 0))
            detail = f"Accuracy {acc:.0f}%   |   {self.correct_words} correct words"
            tk.Label(box, text=detail, font=self.f_small, fg=DIM, bg=CARD).pack(pady=(4, 0))
            if new_best:
                tk.Label(box, text="NEW PERSONAL BEST!", font=self.f_btn, fg=AMBER,
                         bg=CARD).pack(pady=(8, 0))
        else:
            tk.Label(box, text="HIGH SCORES", font=self.f_h2, fg=TEXT, bg=CARD).pack(pady=(24, 0))

        # Leaderboard
        board = tk.Frame(box, bg=CARD_2)
        board.pack(fill="x", padx=28, pady=18)
        if not self.scoreboard.scores:
            tk.Label(board, text="No scores yet - go set one!", font=self.f_small,
                     fg=DIM, bg=CARD_2).pack(pady=14)
        for rank, s in enumerate(self.scoreboard.scores[:5], start=1):
            row = tk.Frame(board, bg=CARD_2)
            row.pack(fill="x", padx=14, pady=3)
            color = AMBER if rank == 1 else TEXT
            tk.Label(row, text=f"#{rank}", font=self.f_btn, fg=color, bg=CARD_2,
                     width=3, anchor="w").pack(side="left")
            tk.Label(row, text=f"{s['wpm']:.0f} WPM", font=self.f_btn, fg=color,
                     bg=CARD_2, width=9, anchor="w").pack(side="left")
            tk.Label(row, text=f"{s['acc']:.0f}% acc", font=self.f_small, fg=DIM,
                     bg=CARD_2, width=9, anchor="w").pack(side="left")
            tk.Label(row, text=f"{s['duration']}s", font=self.f_small, fg=DIM,
                     bg=CARD_2, width=5, anchor="w").pack(side="left")
            tk.Label(row, text=s["date"], font=self.f_small, fg=DIM,
                     bg=CARD_2).pack(side="right")

        buttons = tk.Frame(box, bg=CARD)
        buttons.pack(pady=(0, 24))
        if result:
            FlatButton(buttons, "Try Again  (Enter)", self.new_round,
                       font=self.f_btn).pack(side="left", padx=6)
            self.bind("<Return>", lambda _e: self.new_round())
        else:
            FlatButton(buttons, "Close", self._close_overlay, bg=CARD_2, hover=BORDER,
                       fg=TEXT, font=self.f_btn).pack(side="left", padx=6)
        box.lift()


if __name__ == "__main__":
    TypeFlow().mainloop()