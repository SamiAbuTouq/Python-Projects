"""
Watermark Studio - a desktop app to add text / logo watermarks to images.

Requirements:  pip install Pillow
Run:           python watermark_studio_soft_theme.py
"""

import tkinter as tk
from tkinter import ttk, filedialog, colorchooser, messagebox
from PIL import Image, ImageDraw, ImageFont, ImageTk, ImageOps

# ---------- Theme ----------
BG = "#0f1a1c"            # app background (deep teal-black)
PANEL = "#142226"         # sidebar
CARD = "#1b2e33"          # cards / inputs
BORDER = "#2a434a"        # subtle dividers
TEXT = "#dbe8e6"          # softened off-white with a hint of green
MUTED = "#86a09d"         # secondary text
ACCENT = "#27998b"        # calm teal (primary buttons, sliders)
ACCENT_HOVER = "#3bb3a4"  # lighter teal for hover
ACCENT2 = "#e3b866"       # soft gold for value labels

FONT_UI = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_TITLE = ("Segoe UI", 18, "bold")

FONT_CANDIDATES = {
    "Sans": ["arial.ttf", "Arial.ttf", "Helvetica.ttc", "DejaVuSans.ttf"],
    "Sans Bold": ["arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf"],
    "Serif": ["times.ttf", "Times New Roman.ttf", "DejaVuSerif.ttf"],
    "Mono": ["cour.ttf", "Courier New.ttf", "DejaVuSansMono.ttf"],
    "Impact": ["impact.ttf", "Impact.ttf", "DejaVuSans-Bold.ttf"],
}

POSITIONS = [
    ("tl", "↖"), ("tc", "↑"), ("tr", "↗"),
    ("ml", "←"), ("mc", "●"), ("mr", "→"),
    ("bl", "↙"), ("bc", "↓"), ("br", "↘"),
]

PREVIEW_MAX = 1400  # preview works on a downscaled copy so sliders stay smooth


def load_font(family, size):
    size = max(8, int(size))
    for name in FONT_CANDIDATES.get(family, []):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)  # Pillow >= 10.1
    except TypeError:
        return ImageFont.load_default()


class WatermarkApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Watermark Studio")
        self.geometry("1220x800")
        self.minsize(1050, 720)
        self.configure(bg=BG)

        # image state
        self.original = None       # full resolution RGBA
        self.preview_base = None   # downscaled RGBA for live preview
        self.logo = None           # RGBA logo
        self.photo = None          # ImageTk reference
        self.image_path = None
        self.custom_pos = None     # (fx, fy) fractions when user clicks the preview
        self._after_id = None
        self._img_box = (0, 0, 1, 1)  # x, y, w, h of the drawn preview

        # control variables
        self.mode = tk.StringVar(value="text")
        self.text = tk.StringVar(value="© Your Name")
        self.font_family = tk.StringVar(value="Sans Bold")
        self.size = tk.DoubleVar(value=7)
        self.logo_size = tk.DoubleVar(value=20)
        self.opacity = tk.DoubleVar(value=60)
        self.rotation = tk.DoubleVar(value=0)
        self.margin = tk.DoubleVar(value=3)
        self.color = "#ffffff"
        self.shadow = tk.BooleanVar(value=True)
        self.tile = tk.BooleanVar(value=False)
        self.position = tk.StringVar(value="br")

        self._setup_style()
        self._build_ui()

        for var in (self.mode, self.text, self.font_family, self.size, self.logo_size,
                    self.opacity, self.rotation, self.margin, self.shadow, self.tile):
            var.trace_add("write", lambda *_: self.schedule_refresh())
        self._on_mode_change()

    # ------------------------------------------------------------------ UI
    def _setup_style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", background=PANEL, foreground=TEXT, font=FONT_UI)
        s.configure("TFrame", background=PANEL)
        s.configure("Card.TFrame", background=CARD)
        s.configure("TLabel", background=PANEL, foreground=TEXT)
        s.configure("Card.TLabel", background=CARD, foreground=TEXT)
        s.configure("Muted.TLabel", background=CARD, foreground=MUTED, font=("Segoe UI", 9))
        s.configure("TEntry", fieldbackground=BG, foreground=TEXT, bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER, insertcolor=TEXT, padding=6)
        s.map("TEntry", bordercolor=[("focus", ACCENT)], lightcolor=[("focus", ACCENT)],
              darkcolor=[("focus", ACCENT)])
        s.configure("TCombobox", fieldbackground=BG, background=CARD, foreground=TEXT,
                    arrowcolor=TEXT, bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
                    padding=5)
        s.map("TCombobox", fieldbackground=[("readonly", BG)], foreground=[("readonly", TEXT)],
              bordercolor=[("focus", ACCENT)])
        self.option_add("*TCombobox*Listbox.background", BG)
        self.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
        self.option_add("*TCombobox*Listbox.selectForeground", "white")
        s.configure("Horizontal.TScale", background=CARD, troughcolor=BG,
                    bordercolor=CARD, lightcolor=ACCENT, darkcolor=ACCENT)
        s.map("Horizontal.TScale", background=[("active", ACCENT_HOVER)])
        s.configure("TCheckbutton", background=CARD, foreground=TEXT)
        s.map("TCheckbutton", background=[("active", CARD)], foreground=[("active", ACCENT2)],
              indicatorcolor=[("selected", ACCENT), ("!selected", BG)])
        s.configure("Vertical.TScrollbar", background=CARD, troughcolor=PANEL,
                    bordercolor=PANEL, arrowcolor=TEXT, lightcolor=CARD, darkcolor=CARD)
        s.map("Vertical.TScrollbar", background=[("active", ACCENT)])
        s.configure("TRadiobutton", background=CARD, foreground=TEXT)
        s.map("TRadiobutton", background=[("active", CARD)],
              indicatorcolor=[("selected", ACCENT), ("!selected", BG)])

    def _button(self, parent, text, command, primary=False, **kw):
        bg = ACCENT if primary else CARD
        hover = ACCENT_HOVER if primary else BORDER
        btn = tk.Button(parent, text=text, command=command, bg=bg, fg="white",
                        activebackground=hover, activeforeground="white", relief="flat",
                        bd=0, font=FONT_BOLD, cursor="hand2", padx=14, pady=9, **kw)
        btn.bind("<Enter>", lambda e: btn.config(bg=hover))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg))
        return btn

    def _card(self, parent, title):
        wrap = ttk.Frame(parent, style="Card.TFrame", padding=12)
        wrap.pack(fill="x", pady=(0, 10))
        ttk.Label(wrap, text=title.upper(), style="Muted.TLabel").pack(anchor="w", pady=(0, 6))
        return wrap

    def _slider(self, parent, label, var, lo, hi, unit=""):
        row = ttk.Frame(parent, style="Card.TFrame")
        row.pack(fill="x", pady=3)
        top = ttk.Frame(row, style="Card.TFrame")
        top.pack(fill="x")
        ttk.Label(top, text=label, style="Card.TLabel").pack(side="left")
        value = ttk.Label(top, text="", style="Card.TLabel", foreground=ACCENT2)
        value.pack(side="right")

        def update(*_):
            value.config(text=f"{var.get():.0f}{unit}")

        var.trace_add("write", update)
        update()
        ttk.Scale(row, from_=lo, to=hi, variable=var, orient="horizontal").pack(fill="x", pady=(2, 0))

    def _build_ui(self):
        # ---- Sidebar (scrollable; Save button stays pinned at the bottom)
        sidebar = ttk.Frame(self)
        sidebar.pack(side="left", fill="y")

        self._button(sidebar, "💾  Save image", self.save_image, primary=True).pack(
            fill="x", side="bottom", padx=16, pady=(8, 16))

        sb_canvas = tk.Canvas(sidebar, bg=PANEL, highlightthickness=0, width=340)
        sb_scroll = ttk.Scrollbar(sidebar, orient="vertical", command=sb_canvas.yview)
        sb_canvas.configure(yscrollcommand=sb_scroll.set)
        sb_scroll.pack(side="right", fill="y")
        sb_canvas.pack(side="left", fill="both", expand=True)

        side = ttk.Frame(sb_canvas, padding=16)
        win = sb_canvas.create_window((0, 0), window=side, anchor="nw")
        side.bind("<Configure>",
                  lambda e: sb_canvas.configure(scrollregion=sb_canvas.bbox("all")))
        sb_canvas.bind("<Configure>", lambda e: sb_canvas.itemconfigure(win, width=e.width))
        self._enable_wheel(sidebar, sb_canvas)

        ttk.Label(side, text="💧 Watermark Studio", font=FONT_TITLE,
                  foreground=TEXT).pack(anchor="w")
        ttk.Label(side, text="Brand your photos in seconds", foreground=MUTED).pack(
            anchor="w", pady=(0, 12))

        self._button(side, "📂  Open image", self.open_image, primary=True).pack(fill="x", pady=(0, 10))

        # Type
        card = self._card(side, "Watermark type")
        row = ttk.Frame(card, style="Card.TFrame")
        row.pack(fill="x")
        ttk.Radiobutton(row, text="Text", value="text", variable=self.mode,
                        command=self._on_mode_change).pack(side="left", padx=(0, 16))
        ttk.Radiobutton(row, text="Logo", value="logo", variable=self.mode,
                        command=self._on_mode_change).pack(side="left")

        # Holder keeps the text/logo cards in the right slot when switching
        self.holder = ttk.Frame(side)
        self.holder.pack(fill="x")

        # Text options
        self.text_card = self._card(self.holder, "Text")
        ttk.Entry(self.text_card, textvariable=self.text).pack(fill="x", pady=(0, 6))
        r = ttk.Frame(self.text_card, style="Card.TFrame")
        r.pack(fill="x", pady=(0, 4))
        ttk.Combobox(r, textvariable=self.font_family, values=list(FONT_CANDIDATES),
                     state="readonly", width=12).pack(side="left")
        self.color_btn = tk.Button(r, text="  Color  ", bg=self.color, fg="black", relief="flat",
                                   bd=0, font=FONT_BOLD, cursor="hand2", command=self.pick_color)
        self.color_btn.pack(side="right")
        self._slider(self.text_card, "Size", self.size, 1, 30, "%")
        ttk.Checkbutton(self.text_card, text="Drop shadow", variable=self.shadow).pack(anchor="w")

        # Logo options
        self.logo_card = self._card(self.holder, "Logo")
        self._button(self.logo_card, "🖼  Choose logo (PNG)", self.open_logo).pack(fill="x", pady=(0, 6))
        self.logo_label = ttk.Label(self.logo_card, text="No logo selected", style="Muted.TLabel")
        self.logo_label.pack(anchor="w")
        self._slider(self.logo_card, "Logo size", self.logo_size, 3, 80, "%")

        # Style
        style_card = self._card(side, "Style")
        self._slider(style_card, "Opacity", self.opacity, 5, 100, "%")
        self._slider(style_card, "Rotation", self.rotation, -90, 90, "°")
        self._slider(style_card, "Margin", self.margin, 0, 20, "%")

        # Position
        pos_card = self._card(side, "Position")
        wrap = ttk.Frame(pos_card, style="Card.TFrame")
        wrap.pack(side="left")
        self.pos_buttons = {}
        for i, (key, sym) in enumerate(POSITIONS):
            b = tk.Button(wrap, text=sym, width=3, relief="flat", bd=0, font=FONT_BOLD,
                          bg=BG, fg=TEXT, cursor="hand2",
                          command=lambda k=key: self.set_position(k))
            b.grid(row=i // 3, column=i % 3, padx=2, pady=2)
            self.pos_buttons[key] = b
        info = ttk.Frame(pos_card, style="Card.TFrame")
        info.pack(side="left", padx=14, anchor="n")
        ttk.Checkbutton(info, text="Tile pattern", variable=self.tile).pack(anchor="w")
        ttk.Label(info, text="Tip: click the preview\nto place it anywhere", style="Muted.TLabel").pack(
            anchor="w", pady=(6, 0))
        self.set_position("br")

        # ---- Preview area
        right = tk.Frame(self, bg=BG)
        right.pack(side="left", fill="both", expand=True)
        self.canvas = tk.Canvas(right, bg=BG, highlightthickness=0, cursor="crosshair")
        self.canvas.pack(fill="both", expand=True, padx=20, pady=(20, 8))
        self.status = tk.Label(right, text="Open an image to get started", bg=BG, fg=MUTED,
                               font=("Segoe UI", 9), anchor="w")
        self.status.pack(fill="x", padx=22, pady=(0, 12))

        self.canvas.bind("<Configure>", lambda e: self.schedule_refresh())
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_click)
        self._draw_placeholder()

    def _enable_wheel(self, area, canvas):
        """Mouse-wheel scrolling for the sidebar (Windows/macOS/Linux)."""
        def on_wheel(event):
            w = self.winfo_containing(event.x_root, event.y_root)
            if w is None or not str(w).startswith(str(area)):
                return
            box = canvas.bbox("all")
            if not box or box[3] <= canvas.winfo_height():
                return  # everything already fits
            if getattr(event, "num", None) == 4:
                step = -1
            elif getattr(event, "num", None) == 5:
                step = 1
            else:
                step = -1 if event.delta > 0 else 1
            canvas.yview_scroll(step, "units")

        self.bind_all("<MouseWheel>", on_wheel)
        self.bind_all("<Button-4>", on_wheel)
        self.bind_all("<Button-5>", on_wheel)

    def _draw_placeholder(self):
        self.canvas.delete("all")
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        self.canvas.create_rectangle(30, 30, max(w - 30, 31), max(h - 30, 31),
                                     outline=BORDER, dash=(6, 6), width=2)
        self.canvas.create_text(w / 2, h / 2 - 12, text="🖼", fill=MUTED, font=("Segoe UI", 40))
        self.canvas.create_text(w / 2, h / 2 + 34, text="Click “Open image” to start",
                                fill=MUTED, font=("Segoe UI", 12))

    # ------------------------------------------------------------ Actions
    def _on_mode_change(self):
        if self.mode.get() == "text":
            self.logo_card.pack_forget()
            self.text_card.pack(fill="x", pady=(0, 10))
        else:
            self.text_card.pack_forget()
            self.logo_card.pack(fill="x", pady=(0, 10))
        self.schedule_refresh()

    def open_image(self):
        path = filedialog.askopenfilename(
            title="Choose an image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.webp *.tiff"), ("All files", "*.*")])
        if not path:
            return
        try:
            img = ImageOps.exif_transpose(Image.open(path)).convert("RGBA")
        except Exception as exc:
            messagebox.showerror("Error", f"Could not open image:\n{exc}")
            return
        self.original = img
        self.image_path = path
        prev = img.copy()
        prev.thumbnail((PREVIEW_MAX, PREVIEW_MAX), Image.LANCZOS)
        self.preview_base = prev
        self.custom_pos = None
        self.status.config(text=f"{path.split('/')[-1].split(chr(92))[-1]}  •  {img.width}×{img.height}px")
        self.refresh()

    def open_logo(self):
        path = filedialog.askopenfilename(
            title="Choose a logo",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp"), ("All files", "*.*")])
        if not path:
            return
        try:
            self.logo = Image.open(path).convert("RGBA")
        except Exception as exc:
            messagebox.showerror("Error", f"Could not open logo:\n{exc}")
            return
        self.logo_label.config(text=path.split("/")[-1].split(chr(92))[-1])
        self.schedule_refresh()

    def pick_color(self):
        _, hex_color = colorchooser.askcolor(color=self.color, title="Watermark color")
        if hex_color:
            self.color = hex_color
            self.color_btn.config(bg=hex_color, fg="black" if self._is_light(hex_color) else "white")
            self.schedule_refresh()

    @staticmethod
    def _is_light(hex_color):
        r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
        return (r * 299 + g * 587 + b * 114) / 1000 > 140

    def set_position(self, key):
        self.position.set(key)
        self.custom_pos = None
        for k, b in self.pos_buttons.items():
            b.config(bg=ACCENT if k == key else BG)
        self.schedule_refresh()

    def on_canvas_click(self, event):
        if self.original is None or self.tile.get():
            return
        x0, y0, w, h = self._img_box
        fx = min(max((event.x - x0) / w, 0), 1)
        fy = min(max((event.y - y0) / h, 0), 1)
        self.custom_pos = (fx, fy)
        for b in self.pos_buttons.values():
            b.config(bg=BG)
        self.schedule_refresh()

    # ---------------------------------------------------------- Rendering
    def build_watermark(self, base_width):
        """Return an RGBA watermark sized relative to the base image width."""
        opacity = self.opacity.get() / 100

        if self.mode.get() == "logo":
            if self.logo is None:
                return None
            target_w = max(8, int(base_width * self.logo_size.get() / 100))
            ratio = target_w / self.logo.width
            wm = self.logo.resize((target_w, max(1, int(self.logo.height * ratio))), Image.LANCZOS)
        else:
            text = self.text.get().strip()
            if not text:
                return None
            font = load_font(self.font_family.get(), base_width * self.size.get() / 100)
            pad = int(font.size * 0.4) if hasattr(font, "size") else 12
            probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
            l, t, r, b = probe.textbbox((0, 0), text, font=font)
            wm = Image.new("RGBA", (r - l + pad * 2, b - t + pad * 2), (0, 0, 0, 0))
            d = ImageDraw.Draw(wm)
            if self.shadow.get():
                off = max(1, int(font.size * 0.06)) if hasattr(font, "size") else 2
                d.text((pad - l + off, pad - t + off), text, font=font, fill=(0, 0, 0, 170))
            d.text((pad - l, pad - t), text, font=font, fill=self.color)

        # opacity
        alpha = wm.getchannel("A").point(lambda v: int(v * opacity))
        wm.putalpha(alpha)

        # rotation
        angle = self.rotation.get()
        if abs(angle) > 0.5:
            wm = wm.rotate(angle, expand=True, resample=Image.BICUBIC)
        return wm

    def compose(self, base):
        wm = self.build_watermark(base.width)
        out = base.copy()
        if wm is None:
            return out
        W, H = out.size
        w, h = wm.size
        m = int(W * self.margin.get() / 100)

        if self.tile.get():
            step_x, step_y = int(w * 1.5), int(h * 2.0)
            row = 0
            y = -h // 2
            while y < H:
                x = -w // 2 + (step_x // 2 if row % 2 else 0)
                while x < W:
                    out.paste(wm, (x, y), wm)
                    x += step_x
                y += step_y
                row += 1
            return out

        if self.custom_pos is not None:
            x = int(self.custom_pos[0] * W - w / 2)
            y = int(self.custom_pos[1] * H - h / 2)
        else:
            key = self.position.get()
            x = {"l": m, "c": (W - w) // 2, "r": W - w - m}[self._col(key)]
            y = {"t": m, "m": (H - h) // 2, "b": H - h - m}[key[0]]
        out.paste(wm, (x, y), wm)
        return out

    @staticmethod
    def _col(key):
        return {"tl": "l", "ml": "l", "bl": "l", "tc": "c", "mc": "c", "bc": "c",
                "tr": "r", "mr": "r", "br": "r"}[key]

    def schedule_refresh(self):
        if self._after_id:
            self.after_cancel(self._after_id)
        self._after_id = self.after(25, self.refresh)

    def refresh(self):
        self._after_id = None
        if self.preview_base is None:
            self._draw_placeholder()
            return
        cw, ch = max(self.canvas.winfo_width(), 50), max(self.canvas.winfo_height(), 50)
        composed = self.compose(self.preview_base)
        scale = min(cw / composed.width, ch / composed.height)
        size = (max(1, int(composed.width * scale)), max(1, int(composed.height * scale)))
        shown = composed.resize(size, Image.LANCZOS)

        self.photo = ImageTk.PhotoImage(shown)
        x, y = (cw - size[0]) // 2, (ch - size[1]) // 2
        self._img_box = (x, y, size[0], size[1])
        self.canvas.delete("all")
        self.canvas.create_rectangle(x - 1, y - 1, x + size[0] + 1, y + size[1] + 1,
                                     outline=BORDER, width=1)
        self.canvas.create_image(x, y, image=self.photo, anchor="nw")

    # --------------------------------------------------------------- Save
    def save_image(self):
        if self.original is None:
            messagebox.showinfo("Nothing to save", "Open an image first.")
            return
        path = filedialog.asksaveasfilename(
            title="Save watermarked image", defaultextension=".png",
            initialfile="watermarked.png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg *.jpeg"), ("WebP", "*.webp")])
        if not path:
            return
        result = self.compose(self.original)
        try:
            if path.lower().endswith((".jpg", ".jpeg")):
                result = result.convert("RGB")
                result.save(path, quality=95)
            else:
                result.save(path)
        except Exception as exc:
            messagebox.showerror("Error", f"Could not save:\n{exc}")
            return
        self.status.config(text=f"Saved → {path}")
        messagebox.showinfo("Done", "Your watermarked image has been saved! 🎉")


if __name__ == "__main__":
    WatermarkApp().mainloop()