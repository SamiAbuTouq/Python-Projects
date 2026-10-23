#!/usr/bin/env python3
"""
SPACE INVADERS  -  a neon-styled remake built with Python's Turtle module.

Controls
    Left / Right  (or A / D)   move your ship
    Space                      fire (hold to keep firing)
    P                          pause
    Enter                      start / play again
    Esc  (or Q)                quit

Run:  python space_invaders.py
"""

import math
import random
import time
import turtle
from turtle import Shape

# --------------------------------------------------------------------------
#  Constants
# --------------------------------------------------------------------------
WIDTH, HEIGHT = 640, 780
BG = "#05060f"
BG_RGB = (5, 6, 15)

PLAYER_Y = -300
GROUND_Y = -335
LEFT_BOUND, RIGHT_BOUND = -265, 265      # alien formation limits
PLAYER_LIMIT = 275

COLS = 9
ROWS = ["squid", "crab", "crab", "octo", "octo"]
ALIEN_SX, ALIEN_SY = 48, 46
ALIEN_COLORS = {"squid": "#ff4fd8", "crab": "#4ff0ff", "octo": "#7dff6a"}
ALIEN_POINTS = {"squid": 30, "crab": 20, "octo": 10}

# --------------------------------------------------------------------------
#  Pixel art
# --------------------------------------------------------------------------
SPRITES = {
    "squid": [
        ["...##...",
         "..####..",
         ".######.",
         "##.##.##",
         "########",
         "..#..#..",
         ".#.##.#.",
         "#.#..#.#"],
        ["...##...",
         "..####..",
         ".######.",
         "##.##.##",
         "########",
         ".#.##.#.",
         "#......#",
         ".#....#."],
    ],
    "crab": [
        ["..#.....#..",
         "...#...#...",
         "..#######..",
         ".##.###.##.",
         "###########",
         "#.#######.#",
         "#.#.....#.#",
         "...##.##..."],
        ["..#.....#..",
         "#..#...#..#",
         "#.#######.#",
         "###.###.###",
         "###########",
         ".#########.",
         "..#.....#..",
         ".#.......#."],
    ],
    "octo": [
        ["....####....",
         ".##########.",
         "############",
         "###..##..###",
         "############",
         "...##..##...",
         "..##.##.##..",
         "##........##"],
        ["....####....",
         ".##########.",
         "############",
         "###..##..###",
         "############",
         "..###..###..",
         ".##..##..##.",
         "..##....##.."],
    ],
}

PLAYER_SPRITE = [
    "......#......",
    ".....###.....",
    ".....###.....",
    ".###########.",
    "#############",
    "#############",
    "#############",
]

UFO_SPRITE = [
    ".....######.....",
    "...##########...",
    "..############..",
    ".##.##.##.##.##.",
    "################",
    "..###..##..###..",
    "...#........#...",
]

ALIEN_BULLET_SPRITES = [
    ["#.", ".#", "#.", ".#", "#."],
    [".#", "#.", ".#", "#.", ".#"],
]

BARRIER_LAYOUT = [
    "..#######..",
    ".#########.",
    "###########",
    "###########",
    "###########",
    "####...####",
    "###.....###",
]


def pixel_shape(name, rows, color, px=3):
    """Register a compound turtle shape built from a bitmap.
    Sprites are meant to be drawn with heading 90 (identity mapping)."""
    h, w = len(rows), len(rows[0])
    shape = Shape("compound")
    for r, row in enumerate(rows):
        c = 0
        while c < w:
            if row[c] == "#":
                start = c
                while c < w and row[c] == "#":
                    c += 1
                x0, x1 = (start - w / 2) * px, (c - w / 2) * px
                y1 = (h / 2 - r) * px
                y0 = y1 - px
                shape.addcomponent(((x0, y0), (x1, y0), (x1, y1), (x0, y1)), color, color)
            else:
                c += 1
    turtle.register_shape(name, shape)


# --------------------------------------------------------------------------
#  Helpers
# --------------------------------------------------------------------------
def hex_to_rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def rgb_to_hex(c):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(v))) for v in c)


def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(a + (b - a) * t for a, b in zip(c1, c2))


_pool = []


def make(shape="circle", color="white", size=1.0, x=0, y=0, show=True):
    """Get a (recycled) turtle. Turtles can't be deleted, so we pool them."""
    t = _pool.pop() if _pool else turtle.Turtle(visible=False)
    t.penup()
    t.speed(0)
    t.shape(shape)
    t.shapesize(size, size, 1)
    t.setheading(90)
    t.color(color)
    t.goto(x, y)
    if show:
        t.showturtle()
    else:
        t.hideturtle()
    return t


def free(t):
    t.clear()
    t.hideturtle()
    t.goto(2000, 2000)
    _pool.append(t)


def new_pen():
    p = turtle.Turtle(visible=False)
    p.penup()
    p.speed(0)
    return p


def glow_text(pen, x, y, text, color, glow, size, align="center"):
    font = ("Courier", size, "bold")
    pen.color(glow)
    pen.goto(x + 2, y - 2)
    pen.write(text, align=align, font=font)
    pen.color(color)
    pen.goto(x, y)
    pen.write(text, align=align, font=font)


# --------------------------------------------------------------------------
#  The game
# --------------------------------------------------------------------------
class Game:
    def __init__(self):
        self.screen = turtle.Screen()
        self.screen.setup(WIDTH, HEIGHT)
        self.screen.bgcolor(BG)
        self.screen.title("SPACE INVADERS")
        self.screen.tracer(0)
        self.running = True
        try:
            self.screen.getcanvas().winfo_toplevel().protocol("WM_DELETE_WINDOW", self.quit)
        except Exception:
            pass

        self.register_shapes()
        self.draw_background()

        # state
        self.state = "title"
        self.keys = {"left": False, "right": False, "fire": False}
        self.hi_score = 0
        self.score = 0
        self.lives = 3
        self.level = 1
        self.frame = 0
        self.last = time.perf_counter()

        self.aliens = []
        self.cells = []
        self.pbullet = None
        self.abullets = []
        self.particles = []
        self.popups = []
        self.ufo = None
        self.title_items = []
        self.life_icons = []
        self.player = None

        self.hud = new_pen()
        self.overlay = new_pen()
        self.prompt = new_pen()
        self.prompt_on = None
        self.hud_dirty = True

        self.bind_keys()
        self.show_title()

    # ---------------------------------------------------------------- setup
    def register_shapes(self):
        for kind, frames in SPRITES.items():
            for i, rows in enumerate(frames):
                pixel_shape(f"{kind}{i}", rows, ALIEN_COLORS[kind])
        pixel_shape("player", PLAYER_SPRITE, "#5dff8a")
        pixel_shape("player_icon", PLAYER_SPRITE, "#5dff8a", px=2)
        pixel_shape("ufo", UFO_SPRITE, "#ff3b4a")
        for i, rows in enumerate(ALIEN_BULLET_SPRITES):
            pixel_shape(f"abullet{i}", rows, "#ff7a3d", px=3)
        turtle.register_shape("pbullet", ((-1.5, -8), (1.5, -8), (1.5, 8), (-1.5, 8)))
        turtle.register_shape("cell", ((-3.9, -3.9), (3.9, -3.9), (3.9, 3.9), (-3.9, 3.9)))

    def draw_background(self):
        # soft nebulae made of layered translucent-looking dots
        neb = new_pen()
        for (x, y, base) in [(-150, 200, (30, 14, 60)), (170, -40, (10, 30, 62)), (-60, -230, (45, 12, 40))]:
            for r, k in [(420, 0.18), (330, 0.30), (240, 0.45), (150, 0.62), (80, 0.8)]:
                neb.goto(x, y)
                neb.dot(r, rgb_to_hex(lerp_color(BG_RGB, base, k)))

        # parallax stars
        self.stars = []
        for _ in range(80):
            col = hex_to_rgb(random.choice(["#9fb4ff", "#ffffff", "#ffd9a0", "#b8f1ff"]))
            t = make("circle", rgb_to_hex(col), random.choice([0.08, 0.12, 0.18]),
                     random.uniform(-310, 310), random.uniform(-390, 390))
            self.stars.append([t, random.uniform(8, 45), random.uniform(0, 6.28), col])

        # frame lines with a neon glow
        pen = new_pen()
        pen.hideturtle()
        for yy, col in [(GROUND_Y, "#5dff8a"), (322, "#4ff0ff")]:
            for w, k in [(7, 0.15), (4, 0.35), (2, 1.0)]:
                pen.pensize(w)
                pen.color(rgb_to_hex(lerp_color(BG_RGB, hex_to_rgb(col), k)))
                pen.goto(-WIDTH // 2, yy)
                pen.pendown()
                pen.goto(WIDTH // 2, yy)
                pen.penup()

    def bind_keys(self):
        s = self.screen

        def press(k):
            return lambda: self.keys.__setitem__(k, True)

        def release(k):
            return lambda: self.keys.__setitem__(k, False)

        for key, name in [("Left", "left"), ("a", "left"), ("Right", "right"),
                          ("d", "right"), ("space", "fire")]:
            s.onkeypress(press(name), key)
            s.onkeyrelease(release(name), key)
        s.onkeypress(self.on_enter, "Return")
        s.onkeypress(self.toggle_pause, "p")
        s.onkeypress(self.quit, "Escape")
        s.onkeypress(self.quit, "q")
        s.listen()

    def quit(self):
        self.running = False
        try:
            self.screen.bye()
        except Exception:
            pass

    # ---------------------------------------------------------------- screens
    def clear_title_items(self):
        for t in self.title_items:
            free(t)
        self.title_items = []

    def show_title(self):
        self.state = "title"
        self.overlay.clear()
        glow_text(self.overlay, 0, 175, "SPACE", "#4ff0ff", "#0b4a63", 44)
        glow_text(self.overlay, 0, 118, "INVADERS", "#ff4fd8", "#5a1650", 44)

        y = 40
        for label, shape, pts in [("UFO", "ufo", "= ??? PTS"),
                                  ("SQUID", "squid0", "= 30 PTS"),
                                  ("CRAB", "crab0", "= 20 PTS"),
                                  ("OCTOPUS", "octo0", "= 10 PTS")]:
            self.title_items.append(make(shape, "white", 1, -105, y))
            glow_text(self.overlay, -40, y - 9, pts, "#e8f0ff", "#202850", 16, "left")
            y -= 42

        self.overlay.color("#8893b8")
        self.overlay.goto(0, -160)
        self.overlay.write("\u2190 \u2192  or  A / D   move", align="center", font=("Courier", 13, "bold"))
        self.overlay.goto(0, -184)
        self.overlay.write("SPACE   fire        P   pause", align="center", font=("Courier", 13, "bold"))
        self.overlay.goto(0, -208)
        self.overlay.write("Hide behind the barriers!", align="center", font=("Courier", 13, "bold"))
        self.hud_dirty = True

    def show_game_over(self):
        self.state = "gameover"
        self.hi_score = max(self.hi_score, self.score)
        self.hud_dirty = True
        self.overlay.clear()
        glow_text(self.overlay, 0, 60, "GAME OVER", "#ff4a5a", "#5a1219", 46)
        glow_text(self.overlay, 0, 10, f"SCORE  {self.score:05d}", "#e8f0ff", "#202850", 20)
        if self.score >= self.hi_score and self.score > 0:
            glow_text(self.overlay, 0, -26, "NEW HIGH SCORE!", "#ffe14f", "#5a4a10", 16)

    def on_enter(self):
        if self.state in ("title", "gameover"):
            self.start_game()

    def toggle_pause(self):
        if self.state == "play":
            self.state = "paused"
            glow_text(self.overlay, 0, 0, "PAUSED", "#ffe14f", "#5a4a10", 40)
        elif self.state == "paused":
            self.state = "play"
            self.overlay.clear()
            self.last = time.perf_counter()

    # ---------------------------------------------------------------- game flow
    def start_game(self):
        self.overlay.clear()
        self.prompt.clear()
        self.prompt_on = None
        self.clear_title_items()
        self.cleanup_world()

        self.score = 0
        self.lives = 3
        self.level = 1
        self.invuln = 0.0
        self.hud_dirty = True

        if self.player is None:
            self.player = make("player", "white", 1, 0, PLAYER_Y)
        self.player.goto(0, PLAYER_Y)
        self.player.showturtle()

        self.spawn_wave()
        self.spawn_barriers()
        self.state = "play"
        self.last = time.perf_counter()

    def cleanup_world(self):
        for a in self.aliens:
            free(a["t"])
        self.aliens = []
        for c in self.cells:
            free(c["t"])
        self.cells = []
        self.clear_bullets()
        for p in self.particles:
            free(p["t"])
        self.particles = []
        for p in self.popups:
            free(p["t"])
        self.popups = []
        if self.ufo:
            free(self.ufo["t"])
            self.ufo = None

    def clear_bullets(self):
        if self.pbullet:
            free(self.pbullet)
            self.pbullet = None
        for b in self.abullets:
            free(b["t"])
        self.abullets = []

    def spawn_wave(self):
        top = 235 - min(self.level - 1, 5) * 18
        for r, kind in enumerate(ROWS):
            for c in range(COLS):
                x = (c - (COLS - 1) / 2) * ALIEN_SX
                y = top - r * ALIEN_SY
                t = make(f"{kind}0", "white", 1, x, y)
                self.aliens.append({"t": t, "kind": kind, "col": c})
        self.total = len(self.aliens)
        self.dir = 1
        self.anim = 0
        self.step_timer = 0.6
        self.shoot_timer = 1.5
        self.ufo_timer = random.uniform(12, 20)
        self.shoot_delay = 0.0
        self.pb_prev = 0.0
        self.popup(0, 40, f"WAVE {self.level}", "#ffe14f", 22, 1.4)

    def spawn_barriers(self):
        for c in self.cells:
            free(c["t"])
        self.cells = []
        for bx in (-210, -70, 70, 210):
            rows, cols = len(BARRIER_LAYOUT), len(BARRIER_LAYOUT[0])
            for r, row in enumerate(BARRIER_LAYOUT):
                for c, ch in enumerate(row):
                    if ch == "#":
                        x = bx + (c - cols / 2 + 0.5) * 8
                        y = -235 + (rows - r) * 8
                        t = make("cell", "#5dff5d", 1, x, y)
                        self.cells.append({"t": t, "x": x, "y": y, "hp": 3})

    # ---------------------------------------------------------------- effects
    def explode(self, x, y, color, n=18, speed=220):
        base = hex_to_rgb(color)
        for _ in range(n):
            ang = random.uniform(0, 6.283)
            sp = random.uniform(40, speed)
            life = random.uniform(0.35, 0.85)
            t = make("circle", color, random.uniform(0.15, 0.35), x, y)
            self.particles.append({"t": t, "x": x, "y": y, "vx": math.cos(ang) * sp,
                                   "vy": math.sin(ang) * sp, "life": life, "max": life,
                                   "col": base})

    def popup(self, x, y, text, color, size=12, life=0.7):
        t = make("circle", color, 1, x, y, show=False)
        t.write(text, align="center", font=("Courier", size, "bold"))
        self.popups.append({"t": t, "life": life, "y": y, "x": x, "text": text,
                            "size": size, "color": color})

    def update_effects(self, dt):
        for p in self.particles[:]:
            p["life"] -= dt
            if p["life"] <= 0:
                free(p["t"])
                self.particles.remove(p)
                continue
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vx"] *= 0.97
            p["vy"] *= 0.97
            k = p["life"] / p["max"]
            p["t"].goto(p["x"], p["y"])
            p["t"].color(rgb_to_hex(lerp_color(BG_RGB, p["col"], k)))
        for p in self.popups[:]:
            p["life"] -= dt
            if p["life"] <= 0:
                free(p["t"])
                self.popups.remove(p)

    def update_stars(self, dt):
        now = time.perf_counter()
        for i, s in enumerate(self.stars):
            t, sp, ph, col = s
            y = t.ycor() - sp * dt
            if y < -395:
                y = 395
                t.setx(random.uniform(-310, 310))
            t.sety(y)
            if (i + self.frame) % 4 == 0:
                b = 0.3 + 0.7 * (0.5 + 0.5 * math.sin(now * 2.2 + ph))
                t.color(rgb_to_hex(lerp_color(BG_RGB, col, b)))

    # ---------------------------------------------------------------- HUD
    def draw_hud(self):
        self.hud.clear()
        f = ("Courier", 15, "bold")
        self.hud.color("#4ff0ff")
        self.hud.goto(-300, 336)
        self.hud.write(f"SCORE {self.score:05d}", font=f)
        self.hud.color("#ffe14f")
        self.hud.goto(0, 336)
        self.hud.write(f"HI {max(self.hi_score, self.score):05d}", align="center", font=f)
        self.hud.color("#ff4fd8")
        self.hud.goto(300, 336)
        self.hud.write(f"WAVE {self.level}", align="right", font=f)
        self.hud.color("#5dff8a")
        self.hud.goto(-300, -372)
        self.hud.write("LIVES", font=("Courier", 13, "bold"))

        for t in self.life_icons:
            free(t)
        self.life_icons = []
        if self.state != "title":
            for i in range(max(0, self.lives)):
                self.life_icons.append(make("player_icon", "white", 1, -215 + i * 34, -362))
        self.hud_dirty = False

    # ---------------------------------------------------------------- update
    def tick(self):
        if not self.running:
            return
        try:
            now = time.perf_counter()
            dt = min(now - self.last, 0.05)
            self.last = now
            self.frame += 1

            self.update_stars(dt)
            self.update_effects(dt)

            if self.state == "play":
                self.update_play(dt)
            elif self.state == "clear":
                self.clear_timer -= dt
                if self.clear_timer <= 0:
                    self.level += 1
                    self.clear_bullets()
                    self.spawn_wave()
                    self.spawn_barriers()
                    self.hud_dirty = True
                    self.state = "play"
            elif self.state in ("title", "gameover"):
                self.update_prompt(now)

            if self.hud_dirty:
                self.draw_hud()
            self.screen.update()
            self.screen.ontimer(self.tick, 15)
        except (turtle.Terminator, Exception):
            self.running = False

    def update_prompt(self, now):
        on = int(now * 2) % 2 == 0
        if on != self.prompt_on:
            self.prompt_on = on
            self.prompt.clear()
            if on:
                y = -250 if self.state == "title" else -70
                msg = "PRESS ENTER TO START" if self.state == "title" else "PRESS ENTER TO PLAY AGAIN"
                glow_text(self.prompt, 0, y, msg, "#5dff8a", "#14401f", 18)

    def update_play(self, dt):
        # ---- player
        p = self.player
        vx = (self.keys["right"] - self.keys["left"]) * 330
        p.setx(max(-PLAYER_LIMIT, min(PLAYER_LIMIT, p.xcor() + vx * dt)))
        if self.invuln > 0:
            self.invuln -= dt
            if int(self.invuln * 12) % 2 == 0:
                p.hideturtle()
            else:
                p.showturtle()
            if self.invuln <= 0:
                p.showturtle()
        if self.keys["fire"] and self.pbullet is None and self.invuln < 1.4:
            self.pbullet = make("pbullet", "#ffffff", 1, p.xcor(), PLAYER_Y + 20)

        # ---- player bullet
        if self.pbullet:
            b = self.pbullet
            self.pb_prev = b.ycor()
            b.sety(b.ycor() + 680 * dt)
            if b.ycor() > 318:
                free(b)
                self.pbullet = None

        # ---- aliens: marching
        self.step_timer -= dt
        if self.step_timer <= 0 and self.aliens:
            self.step_aliens()
            n = len(self.aliens)
            base = 0.75 - (self.level - 1) * 0.07
            self.step_timer = max(0.035, base * (n / self.total) + 0.03)

        # ---- aliens: shooting
        self.shoot_timer -= dt
        max_b = min(2 + self.level, 6)
        if self.shoot_timer <= 0 and self.aliens and len(self.abullets) < max_b:
            self.alien_fire()
            self.shoot_timer = random.uniform(0.4, 1.3) / (1 + 0.12 * self.level)

        # ---- alien bullets
        shape_i = int(time.perf_counter() * 10) % 2
        for b in self.abullets[:]:
            t = b["t"]
            b["py"] = t.ycor()
            t.sety(t.ycor() - b["v"] * dt)
            t.shape(f"abullet{shape_i}")
            if t.ycor() < GROUND_Y + 6:
                self.explode(t.xcor(), GROUND_Y + 4, "#ff7a3d", 5, 80)
                free(t)
                self.abullets.remove(b)

        # ---- UFO
        self.update_ufo(dt)

        # ---- collisions
        self.collisions()

        if self.state == "play" and not self.aliens:
            self.state = "clear"
            self.clear_timer = 1.8
            self.clear_bullets()
            self.popup(0, 30, "WAVE CLEARED!", "#5dff8a", 24, 1.7)

    def step_aliens(self):
        xs = [a["t"].xcor() for a in self.aliens]
        dx = 12
        if (self.dir > 0 and max(xs) + dx > RIGHT_BOUND) or (self.dir < 0 and min(xs) - dx < LEFT_BOUND):
            self.dir *= -1
            for a in self.aliens:
                a["t"].sety(a["t"].ycor() - 18)
        else:
            for a in self.aliens:
                a["t"].setx(a["t"].xcor() + self.dir * dx)
        self.anim ^= 1
        for a in self.aliens:
            a["t"].shape(f"{a['kind']}{self.anim}")

        # aliens trample barriers; reaching the ship ends the game
        for a in self.aliens:
            ax, ay = a["t"].position()
            if ay < -215:
                for c in self.cells[:]:
                    if abs(c["x"] - ax) < 22 and abs(c["y"] - ay) < 18:
                        free(c["t"])
                        self.cells.remove(c)
            if ay - 12 < PLAYER_Y + 14:
                self.player_dies(final=True)
                return

    def alien_fire(self):
        bottoms = {}
        for a in self.aliens:
            c = a["col"]
            if c not in bottoms or a["t"].ycor() < bottoms[c]["t"].ycor():
                bottoms[c] = a
        # bias toward columns near the player
        cols = list(bottoms.values())
        px = self.player.xcor()
        weights = [1.0 / (1 + abs(a["t"].xcor() - px) / 120) for a in cols]
        a = random.choices(cols, weights)[0]
        t = make("abullet0", "white", 1, a["t"].xcor(), a["t"].ycor() - 16)
        self.abullets.append({"t": t, "v": 250 + self.level * 18, "py": t.ycor()})

    def update_ufo(self, dt):
        if self.ufo is None:
            self.ufo_timer -= dt
            if self.ufo_timer <= 0 and len(self.aliens) > 3:
                d = random.choice([-1, 1])
                t = make("ufo", "white", 1, -340 * d, 296)
                self.ufo = {"t": t, "d": d}
                self.ufo_timer = random.uniform(14, 24)
        else:
            t = self.ufo["t"]
            t.setx(t.xcor() + self.ufo["d"] * 150 * dt)
            if abs(t.xcor()) > 345:
                free(t)
                self.ufo = None

    # ---------------------------------------------------------------- collisions
    @staticmethod
    def sweep(y0, y1, step=3.0):
        """Sample points along a vertical path so fast bullets can't tunnel."""
        n = max(1, int(abs(y1 - y0) // step) + 1)
        return [y0 + (y1 - y0) * i / n for i in range(1, n + 1)]

    def collisions(self):
        # ---- player bullet (swept along the path it travelled this frame)
        b = self.pbullet
        if b:
            bx = b.xcor()
            hit = False
            for by in self.sweep(self.pb_prev + 6, b.ycor() + 6):
                for a in self.aliens:
                    ax, ay = a["t"].position()
                    if abs(bx - ax) < 19 and abs(by - ay) < 15:
                        pts = ALIEN_POINTS[a["kind"]]
                        self.add_score(pts)
                        self.explode(ax, ay, ALIEN_COLORS[a["kind"]])
                        self.popup(ax, ay + 8, str(pts), "#ffffff", 11, 0.6)
                        free(a["t"])
                        self.aliens.remove(a)
                        hit = True
                        break

                if not hit and self.ufo:
                    ux, uy = self.ufo["t"].position()
                    if abs(bx - ux) < 28 and abs(by - uy) < 13:
                        pts = random.choice([50, 100, 150, 300])
                        self.add_score(pts)
                        self.explode(ux, uy, "#ff3b4a", 30, 260)
                        self.popup(ux, uy + 10, str(pts), "#ffe14f", 14, 1.0)
                        free(self.ufo["t"])
                        self.ufo = None
                        hit = True

                if not hit:
                    for ab in self.abullets[:]:
                        t = ab["t"]
                        if abs(bx - t.xcor()) < 8 and abs(by - t.ycor()) < 14:
                            self.explode(bx, by, "#ffffff", 8, 120)
                            free(t)
                            self.abullets.remove(ab)
                            hit = True
                            break

                if not hit and self.hit_cell(bx, by):
                    hit = True

                if hit:
                    break

            if hit:
                free(b)
                self.pbullet = None

        # ---- alien bullets (also swept)
        for ab in self.abullets[:]:
            t = ab["t"]
            x = t.xcor()
            consumed = False
            for y in self.sweep(ab["py"] - 6, t.ycor() - 6):
                if self.hit_cell(x, y):
                    consumed = True
                    break
                if (self.invuln <= 0 and abs(x - self.player.xcor()) < 20
                        and abs(y + 6 - 8 - PLAYER_Y) < 14):
                    free(t)
                    self.abullets.remove(ab)
                    self.player_dies()
                    return
            if consumed:
                free(t)
                self.abullets.remove(ab)

    def hit_cell(self, x, y):
        for c in self.cells:
            if abs(c["x"] - x) < 6 and abs(c["y"] - y) < 6:
                c["hp"] -= 1
                self.explode(x, y, "#5dff5d", 4, 70)
                if c["hp"] <= 0:
                    free(c["t"])
                    self.cells.remove(c)
                else:
                    c["t"].color(["#ff9f43", "#c8ff4f", "#5dff5d"][c["hp"] - 1])
                return True
        return False

    def add_score(self, pts):
        old = self.score
        self.score += pts
        if self.score // 1500 > old // 1500 and self.lives < 5:
            self.lives += 1
            self.popup(0, 0, "EXTRA LIFE!", "#5dff8a", 20, 1.4)
        self.hud_dirty = True

    def player_dies(self, final=False):
        px = self.player.xcor()
        self.explode(px, PLAYER_Y, "#5dff8a", 40, 300)
        self.explode(px, PLAYER_Y, "#ffffff", 14, 180)
        self.lives = 0 if final else self.lives - 1
        self.hud_dirty = True
        for b in self.abullets:
            free(b["t"])
        self.abullets = []
        if self.pbullet:
            free(self.pbullet)
            self.pbullet = None
        if self.lives <= 0:
            self.player.hideturtle()
            self.show_game_over()
        else:
            self.invuln = 2.0
            self.player.goto(0, PLAYER_Y)


# --------------------------------------------------------------------------
def main():
    game = Game()
    game.tick()
    try:
        turtle.mainloop()
    except (turtle.Terminator, Exception):
        pass


if __name__ == "__main__":
    main()