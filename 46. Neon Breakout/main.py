"""
NEON BREAKOUT  -  built with Python's turtle module
---------------------------------------------------
Controls:
    Left / Right arrows  or  A / D   move the paddle
    Mouse                            also moves the paddle
    SPACE                            launch the ball / restart after game over
    ESC  or  P                       pause / resume
    R                                restart (while paused or after game over)
    Q                                quit

Some bricks (white frame, blinking) hide a power-up.
Break one and a capsule falls - catch it with the paddle! Plain bricks drop nothing.
Every power-up has its own colour, icon and label:
    x2    (two dots)       MULTI-BALL  every ball splits in two
    x3    (three dots)     MULTI-BALL  every ball splits in three
    WIDE  (double arrow)   paddle grows for a while
    FIRE  (flame)          balls burn straight through bricks for a while
    SLOW  (clock)          balls slow down for a while
    +1    (heart)          extra life
"""
import math
import os
import random
import time
import tkinter
import turtle

# ----------------------------------------------------------------- settings
WIDTH, HEIGHT = 800, 700
LEFT, RIGHT, TOP, BOTTOM = -390, 390, 290, -350      # play-area walls

PADDLE_Y = -300
PADDLE_W, PADDLE_H = 120, 14
PADDLE_SPEED = 650                                    # px / second (keyboard)

BALL_R = 8
MAX_BALLS = 12
TRAIL_LEN = 7
BASE_SPEED = 340                                      # px / second, level 1
SPEED_PER_LEVEL = 40
MAX_SPEED = 640

COLS, ROWS = 10, 6
BRICK_W, BRICK_H = 68, 24
PITCH_Y = 30
PITCH_X = 76
FIRST_BRICK_Y = 235

POWERUP_BRICKS = 8                                    # special bricks per level (marked with a badge)
CAPSULE_W, CAPSULE_H = 76, 26
CAPSULE_SPEED = 160

WIDE_TIME, FIRE_TIME, SLOW_TIME = 12, 7, 9            # seconds

BG = "#07070f"
ROW_COLORS = ["#ff2e63", "#ff6b35", "#ffd23f", "#3bff9d", "#1fd1ff", "#a35cff"]
CYAN = "#1fd1ff"

# kind -> (label, colour, drop weight)
POWERUPS = {
    "x2":   ("x2",   "#1fd1ff", 30),
    "x3":   ("x3",   "#3bff9d", 14),
    "WIDE": ("WIDE", "#a35cff", 20),
    "FIRE": ("FIRE", "#ff6b35", 16),
    "SLOW": ("SLOW", "#ffd23f", 12),
    "+1":   ("+1",   "#ff2e63", 8),
}

HIGHSCORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "highscore.txt")


# ------------------------------------------------------------------ helpers
def _rgb(hex_color):
    return int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)


def shade(hex_color, factor):
    """Multiply a colour's brightness (factor < 1 darkens, > 1 lightens)."""
    r, g, b = (max(0, min(255, int(c * factor))) for c in _rgb(hex_color))
    return f"#{r:02x}{g:02x}{b:02x}"


def mix(c1, c2, t):
    """Blend colour c1 into c2 (t=0 -> c1, t=1 -> c2)."""
    t = max(0.0, min(1.0, t))
    a, b = _rgb(c1), _rgb(c2)
    r, g, bl = (int(a[i] + (b[i] - a[i]) * t) for i in range(3))
    return f"#{r:02x}{g:02x}{bl:02x}"


def make_shape(shape, width, height, color, outline=None):
    """Create a ready-to-use turtle with a given size (in pixels)."""
    t = turtle.Turtle()
    t.hideturtle()
    t.penup()
    t.speed(0)
    t.shape(shape)
    t.shapesize(stretch_wid=height / 20, stretch_len=width / 20, outline=1)
    t.color(outline or color, color)
    t.showturtle()
    return t


# ------------------------------------------------------------------- bricks
class Brick:
    def __init__(self, x, y, color, points):
        self.x, self.y = x, y
        self.color = color
        self.points = points
        self.alive = True
        self.powerup = None                    # kind of capsule it drops (or None)
        self.fill = shade(color, 0.85)
        self.t = make_shape("square", BRICK_W, BRICK_H, self.fill,
                            outline=shade(color, 1.6))
        self.t.goto(x, y)

    def set_powerup(self, kind):
        self.powerup = kind
        # special bricks get a bright white frame so they stand out
        self.t.color("#ffffff" if kind else shade(self.color, 1.6), self.fill)

    def reset(self):
        self.alive = True
        self.t.showturtle()

    def destroy(self):
        self.alive = False
        self.t.hideturtle()


# -------------------------------------------------------------------- balls
class Ball:
    """One ball from a reusable pool (so multi-ball never creates new turtles)."""

    def __init__(self):
        self.active = False
        self.x = self.y = self.vx = self.vy = 0.0
        self.trail_pos = []
        self.trail = [make_shape("circle", 4 + i * 1.5, 4 + i * 1.5, "#ffffff")
                      for i in range(TRAIL_LEN)]
        self.glow = make_shape("circle", BALL_R * 3.2, BALL_R * 3.2, "#17304d")
        self.body = make_shape("circle", BALL_R * 2, BALL_R * 2, "#ffffff")
        self.hide()

    def hide(self):
        for t in self.trail:
            t.hideturtle()
        self.glow.hideturtle()
        self.body.hideturtle()

    def spawn(self, x, y, vx, vy):
        self.active = True
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.trail_pos = []
        self.glow.showturtle()
        self.body.showturtle()

    def remove(self):
        self.active = False
        self.hide()


# -------------------------------------------------------------------- game
class Game:
    def __init__(self):
        self.screen = turtle.Screen()
        self.screen.setup(WIDTH, HEIGHT)
        self.screen.bgcolor(BG)
        self.screen.title("NEON BREAKOUT")
        self.screen.tracer(0)

        self.draw_background()

        # --- game objects (created back-to-front so glows sit underneath)
        self.bricks = []
        for row in range(ROWS):
            for col in range(COLS):
                x = (col - (COLS - 1) / 2) * PITCH_X
                y = FIRST_BRICK_Y - row * PITCH_Y
                self.bricks.append(Brick(x, y, ROW_COLORS[row], (ROWS - row) * 10))
        self.bricks_left = len(self.bricks)

        self.particles = []
        for _ in range(90):
            p = make_shape("circle", 6, 6, "#ffffff")
            p.hideturtle()
            self.particles.append({"t": p, "vx": 0, "vy": 0, "life": 0, "max": 1, "color": "#fff"})

        self.capsules = []
        for _ in range(6):
            t = make_shape("square", CAPSULE_W, CAPSULE_H, "#222222", outline="#ffffff")
            t.hideturtle()
            self.capsules.append({"t": t, "active": False, "kind": "x2", "x": 0.0, "y": 0.0})

        self.balls = [Ball() for _ in range(MAX_BALLS)]

        self.paddle_w = PADDLE_W
        self.paddle_glow = make_shape("square", PADDLE_W + 18, PADDLE_H + 12, shade(CYAN, 0.22))
        self.paddle = make_shape("square", PADDLE_W, PADDLE_H, shade(CYAN, 0.9), outline="#ffffff")

        # --- text writers (created last so they draw on top)
        self.hud = self.make_writer()
        self.msg = self.make_writer()
        self.icons = self.make_writer()       # little pictures on the falling capsules
        self.labels = self.make_writer()      # text on the falling capsules
        self.toast = self.make_writer()       # "MULTI-BALL x3!" pop-ups
        self.status = self.make_writer()      # active power-up timers

        # --- state
        self.high_score = self.load_high_score()
        self.keys = {"left": False, "right": False}
        self.paddle_x = 0.0
        self.last_time = time.perf_counter()
        self.toast_text, self.toast_color, self.toast_timer = "", "#fff", 0.0
        self.status_text = None
        self.labels_dirty = False
        self.new_game()
        self.bind_controls()

    # ------------------------------------------------------------- set-up
    def draw_background(self):
        stars = turtle.Turtle()
        stars.hideturtle()
        stars.penup()
        stars.speed(0)
        for _ in range(110):
            x = random.randint(-WIDTH // 2, WIDTH // 2)
            y = random.randint(-HEIGHT // 2, HEIGHT // 2)
            stars.goto(x, y)
            stars.dot(random.choice([1, 1, 2, 2, 3]), random.choice(["#1a1a33", "#23234a", "#2e2e5e"]))

        frame = turtle.Turtle()
        frame.hideturtle()
        frame.penup()
        frame.speed(0)
        for width, color in ((9, "#0a2a38"), (5, "#0f6a88"), (2, CYAN)):
            frame.pensize(width)
            frame.color(color)
            frame.goto(LEFT - 6, BOTTOM)
            frame.pendown()
            frame.goto(LEFT - 6, TOP + 6)
            frame.goto(RIGHT + 6, TOP + 6)
            frame.goto(RIGHT + 6, BOTTOM)
            frame.penup()

    @staticmethod
    def make_writer():
        w = turtle.Turtle()
        w.hideturtle()
        w.penup()
        w.speed(0)
        return w

    def bind_controls(self):
        s = self.screen
        s.listen()
        for key, name, pressed in (("Left", "left", True), ("a", "left", True),
                                   ("Right", "right", True), ("d", "right", True)):
            s.onkeypress(lambda n=name: self.set_key(n, True), key)
        for key, name in (("Left", "left"), ("a", "left"), ("Right", "right"), ("d", "right")):
            s.onkeyrelease(lambda n=name: self.set_key(n, False), key)
        s.onkeypress(self.space, "space")
        s.onkeypress(self.toggle_pause, "p")
        s.onkeypress(self.toggle_pause, "Escape")
        s.onkeypress(self.restart, "r")
        s.onkeypress(self.quit, "q")
        s.getcanvas().bind("<Motion>", self.on_mouse)

    def set_key(self, name, pressed):
        self.keys[name] = pressed

    def on_mouse(self, event):
        canvas = self.screen.getcanvas()
        self.paddle_x = event.x - canvas.winfo_width() / 2
        self.clamp_paddle()

    # --------------------------------------------------------- game flow
    def new_game(self):
        self.score = 0
        self.lives = 3
        self.level = 1
        self.reset_bricks()
        self.start_round("NEON BREAKOUT", "press SPACE to launch")

    def reset_bricks(self):
        for b in self.bricks:
            b.reset()
            b.set_powerup(None)
        self.bricks_left = len(self.bricks)
        # pick which bricks hide a power-up this level
        kinds = list(POWERUPS)
        weights = [POWERUPS[k][2] for k in kinds]
        for b in random.sample(self.bricks, POWERUP_BRICKS):
            b.set_powerup(random.choices(kinds, weights=weights)[0])

    def reset_effects(self):
        """Clear all power-ups, capsules and extra balls."""
        self.wide_timer = self.fire_timer = self.slow_timer = 0.0
        self.set_paddle_width(PADDLE_W)
        for c in self.capsules:
            c["active"] = False
            c["t"].hideturtle()
        for b in self.balls:
            b.remove()
        self.labels.clear()
        self.icons.clear()
        self.labels_dirty = False

    def start_round(self, title, subtitle):
        self.state = "ready"
        self.reset_effects()
        self.speed = min(BASE_SPEED + (self.level - 1) * SPEED_PER_LEVEL, MAX_SPEED)
        first = self.balls[0]
        first.spawn(self.paddle_x, PADDLE_Y + PADDLE_H / 2 + BALL_R, 0, 0)
        self.style_ball(first)
        self.show_message(title, subtitle)
        self.draw_hud()

    def space(self):
        if self.state == "ready":
            angle = math.radians(random.uniform(-35, 35))
            ball = self.balls[0]
            ball.vx = self.eff_speed() * math.sin(angle)
            ball.vy = self.eff_speed() * math.cos(angle)
            self.state = "playing"
            self.msg.clear()
        elif self.state == "over":
            self.new_game()

    def toggle_pause(self):
        if self.state == "playing":
            self.state = "paused"
            self.show_message("PAUSED", "ESC resume   -   R restart")
        elif self.state == "paused":
            self.state = "playing"
            self.msg.clear()

    def restart(self):
        """Start a fresh game (only from the pause menu or the game-over screen)."""
        if self.state in ("paused", "over"):
            self.msg.clear()
            self.new_game()

    def quit(self):
        try:
            self.screen.bye()
        except Exception:
            pass

    def next_level(self):
        self.level += 1
        self.score += 100
        self.reset_bricks()
        self.start_round(f"LEVEL {self.level}", "press SPACE to launch")

    def lose_life(self):
        self.lives -= 1
        if self.lives > 0:
            self.start_round("OOPS!", "press SPACE to launch")
        else:
            self.state = "over"
            self.reset_effects()
            if self.score > self.high_score:
                self.high_score = self.score
                self.save_high_score()
            self.show_message("GAME OVER", f"score {self.score}  -  SPACE to play again")
            self.draw_hud()

    # ---------------------------------------------------------- drawing
    def show_message(self, title, subtitle=""):
        self.msg.clear()
        self.msg.color(shade(CYAN, 0.35))          # fake glow: dim copy offset by 2px
        self.msg.goto(2, -62)
        self.msg.write(title, align="center", font=("Courier", 38, "bold"))
        self.msg.color("#ffffff")
        self.msg.goto(0, -60)
        self.msg.write(title, align="center", font=("Courier", 38, "bold"))
        self.msg.color("#9fb4d6")
        self.msg.goto(0, -95)
        self.msg.write(subtitle, align="center", font=("Courier", 14, "normal"))

    def draw_hud(self):
        self.hud.clear()
        self.hud.color(CYAN)
        self.hud.goto(LEFT, 305)
        self.hud.write(f"SCORE {self.score:05d}", align="left", font=("Courier", 18, "bold"))
        self.hud.color("#ffd23f")
        self.hud.goto(0, 305)
        self.hud.write(f"LVL {self.level}   BEST {self.high_score:05d}", align="center",
                       font=("Courier", 16, "bold"))
        self.hud.color("#ff2e63")
        self.hud.goto(RIGHT, 305)
        self.hud.write("♥ " * max(self.lives, 0), align="right", font=("Courier", 18, "bold"))

    def show_toast(self, text, color):
        self.toast_text, self.toast_color, self.toast_timer = text, color, 1.4

    def update_toast(self, dt):
        if self.toast_timer <= 0:
            return
        self.toast_timer -= dt
        self.toast.clear()
        if self.toast_timer > 0:
            fade = mix(self.toast_color, BG, 1 - self.toast_timer / 0.5)   # fade out in last 0.5s
            self.toast.color(fade)
            self.toast.goto(0, -170)
            self.toast.write(self.toast_text, align="center", font=("Courier", 26, "bold"))

    def update_status(self):
        parts = []
        if self.wide_timer > 0:
            parts.append(f"WIDE {math.ceil(self.wide_timer)}s")
        if self.fire_timer > 0:
            parts.append(f"FIRE {math.ceil(self.fire_timer)}s")
        if self.slow_timer > 0:
            parts.append(f"SLOW {math.ceil(self.slow_timer)}s")
        text = "   ".join(parts)
        if text != self.status_text:
            self.status_text = text
            self.status.clear()
            self.status.color("#9fb4d6")
            self.status.goto(LEFT, -343)
            self.status.write(text, align="left", font=("Courier", 12, "bold"))

    def style_ball(self, b):
        fire = self.fire_timer > 0
        b.body.color("#fff1d0" if fire else "#ffffff")
        b.glow.color("#5a2a0c" if fire else "#17304d")

    def draw_objects(self):
        self.paddle.goto(self.paddle_x, PADDLE_Y)
        self.paddle_glow.goto(self.paddle_x, PADDLE_Y)

        fire = self.fire_timer > 0
        trail_color = "#8a3a10" if fire else "#1a3a66"
        for b in self.balls:
            if not b.active:
                continue
            b.body.goto(b.x, b.y)
            b.glow.goto(b.x, b.y)
            if self.state == "playing":
                b.trail_pos.append((b.x, b.y))
                b.trail_pos = b.trail_pos[-TRAIL_LEN:]
            elif self.state == "ready":
                b.trail_pos = []
            n = len(b.trail_pos)
            for i, t in enumerate(b.trail):
                idx = i - (TRAIL_LEN - n)
                if idx >= 0:
                    t.goto(*b.trail_pos[idx])
                    t.color(mix(trail_color, BG, 1 - (i + 1) / TRAIL_LEN))
                    t.showturtle()
                else:
                    t.hideturtle()

    def draw_icon(self, p, kind, cx, cy, color, s=1.0):
        """Draw a small picture (about 24x20 px * s) for a power-up, centred on (cx, cy)."""
        p.color(color)
        p.pensize(2)
        p.setheading(0)

        def poly(points, fill=False):
            p.goto(cx + points[0][0] * s, cy + points[0][1] * s)
            p.pendown()
            if fill:
                p.begin_fill()
            for dx, dy in points[1:] + [points[0]]:
                p.goto(cx + dx * s, cy + dy * s)
            if fill:
                p.end_fill()
            p.penup()

        def dot(dx, dy, size):
            p.goto(cx + dx * s, cy + dy * s)
            p.dot(max(2, round(size * s)))

        if kind == "x2":                                  # two balls
            dot(-6, 0, 10)
            dot(6, 0, 10)
        elif kind == "x3":                                # three balls
            dot(-7, -4, 9)
            dot(7, -4, 9)
            dot(0, 6, 9)
        elif kind == "WIDE":                              # double-headed arrow
            p.goto(cx - 11 * s, cy)
            p.pendown()
            p.goto(cx + 11 * s, cy)
            p.penup()
            poly([(-5, 5), (-11, 0), (-5, -5)])
            poly([(5, 5), (11, 0), (5, -5)])
        elif kind == "FIRE":                              # flame
            poly([(0, 10), (4, 4), (7, -2), (5, -7), (0, -9),
                  (-5, -7), (-7, -2), (-4, 3), (-2, 5)], fill=True)
        elif kind == "SLOW":                              # clock
            p.goto(cx, cy - 8 * s)
            p.pendown()
            p.circle(8 * s)
            p.penup()
            p.goto(cx, cy + 5 * s)
            p.pendown()
            p.goto(cx, cy)
            p.goto(cx + 4 * s, cy)
            p.penup()
        elif kind == "+1":                                # heart
            dot(-3.5, 3, 9)
            dot(3.5, 3, 9)
            poly([(-7.5, 1), (7.5, 1), (0, -9)], fill=True)

    def update_blink(self):
        """Special bricks pulse between their normal colour and white."""
        phase = (math.sin(time.perf_counter() * 3) + 1) / 2     # lower number = slower blink
        for br in self.bricks:
            if br.alive and br.powerup:
                br.t.color("#ffffff", mix(br.fill, "#ffffff", 0.75 * phase))

    def draw_capsule_labels(self):
        active = [c for c in self.capsules if c["active"]]
        if not active and not self.labels_dirty:
            return
        self.labels.clear()
        self.icons.clear()
        self.labels.color(BG)
        for c in active:
            self.draw_icon(self.icons, c["kind"], c["x"] - 22, c["y"], BG)
            self.labels.goto(c["x"] + 14, c["y"] - 8)
            self.labels.write(POWERUPS[c["kind"]][0], align="center", font=("Courier", 11, "bold"))
        self.labels_dirty = bool(active)

    # -------------------------------------------------------- particles
    def burst(self, x, y, color, count=9):
        free = [p for p in self.particles if p["life"] <= 0]
        for p in free[:count]:
            angle = random.uniform(0, math.tau)
            speed = random.uniform(70, 280)
            p.update(vx=math.cos(angle) * speed, vy=math.sin(angle) * speed,
                     life=random.uniform(0.35, 0.8), color=color)
            p["max"] = p["life"]
            p["t"].goto(x, y)
            p["t"].color(color)
            p["t"].showturtle()

    def update_particles(self, dt):
        for p in self.particles:
            if p["life"] <= 0:
                continue
            p["life"] -= dt
            if p["life"] <= 0:
                p["t"].hideturtle()
                continue
            p["vy"] -= 420 * dt                        # gravity
            t = p["t"]
            t.goto(t.xcor() + p["vx"] * dt, t.ycor() + p["vy"] * dt)
            t.color(mix(p["color"], BG, 1 - p["life"] / p["max"]))

    # ---------------------------------------------------------- power-ups
    def eff_speed(self):
        return self.speed * (0.7 if self.slow_timer > 0 else 1.0)

    def normalize(self, b):
        """Give a ball the current speed, and keep it from going nearly horizontal."""
        s = self.eff_speed()
        mag = math.hypot(b.vx, b.vy) or 1.0
        vx, vy = b.vx / mag * s, b.vy / mag * s
        min_vy = 0.25 * s
        if abs(vy) < min_vy:
            vy = math.copysign(min_vy, vy if vy else 1)
            vx = math.copysign(math.sqrt(s * s - vy * vy), vx if vx else 1)
        b.vx, b.vy = vx, vy

    def normalize_all(self):
        for b in self.balls:
            if b.active:
                self.normalize(b)

    def set_paddle_width(self, w):
        self.paddle_w = w
        self.paddle.shapesize(stretch_wid=PADDLE_H / 20, stretch_len=w / 20, outline=1)
        self.paddle_glow.shapesize(stretch_wid=(PADDLE_H + 12) / 20, stretch_len=(w + 18) / 20, outline=1)
        self.clamp_paddle()

    def multiply(self, extra):
        """Split every ball into (1 + extra) balls."""
        for src in [b for b in self.balls if b.active]:
            for k in range(extra):
                nb = next((b for b in self.balls if not b.active), None)
                if nb is None:
                    return
                ang = (0.38 + 0.12 * (k // 2)) * (1 if k % 2 == 0 else -1)
                c, s = math.cos(ang), math.sin(ang)
                nb.spawn(src.x, src.y, src.vx * c - src.vy * s, src.vx * s + src.vy * c)
                self.normalize(nb)
                self.style_ball(nb)

    def drop_powerup(self, kind, x, y):
        slot = next((c for c in self.capsules if not c["active"]), None)
        if slot is None:
            return
        colour = POWERUPS[kind][1]
        slot.update(active=True, kind=kind, x=x, y=y)
        slot["t"].color("#ffffff", colour)
        slot["t"].goto(x, y)
        slot["t"].showturtle()

    def apply_powerup(self, kind, x, y):
        colour = POWERUPS[kind][1]
        if kind in ("x2", "x3"):
            self.multiply(1 if kind == "x2" else 2)
            self.show_toast("DOUBLE BALL!" if kind == "x2" else "TRIPLE BALL!", colour)
        elif kind == "WIDE":
            self.wide_timer = WIDE_TIME
            self.set_paddle_width(PADDLE_W * 1.6)
            self.show_toast("WIDE PADDLE!", colour)
        elif kind == "FIRE":
            self.fire_timer = FIRE_TIME
            for b in self.balls:
                if b.active:
                    self.style_ball(b)
            self.show_toast("FIREBALL!", colour)
        elif kind == "SLOW":
            self.slow_timer = SLOW_TIME
            self.normalize_all()
            self.show_toast("SLOW MOTION", colour)
        elif kind == "+1":
            self.lives = min(self.lives + 1, 6)
            self.draw_hud()
            self.show_toast("EXTRA LIFE!", colour)
        self.burst(x, y, colour, count=18)

    def update_capsules(self, dt):
        for c in self.capsules:
            if not c["active"]:
                continue
            c["y"] -= CAPSULE_SPEED * dt
            c["t"].goto(c["x"], c["y"])
            caught = (c["y"] - CAPSULE_H / 2 <= PADDLE_Y + PADDLE_H / 2
                      and c["y"] > PADDLE_Y - PADDLE_H
                      and abs(c["x"] - self.paddle_x) <= self.paddle_w / 2 + CAPSULE_W / 2)
            if caught:
                c["active"] = False
                c["t"].hideturtle()
                self.apply_powerup(c["kind"], c["x"], c["y"])
            elif c["y"] < BOTTOM:
                c["active"] = False
                c["t"].hideturtle()

    def update_timers(self, dt):
        if self.wide_timer > 0:
            self.wide_timer -= dt
            if self.wide_timer <= 0:
                self.set_paddle_width(PADDLE_W)
        if self.fire_timer > 0:
            self.fire_timer -= dt
            if self.fire_timer <= 0:
                for b in self.balls:
                    if b.active:
                        self.style_ball(b)
        if self.slow_timer > 0:
            self.slow_timer -= dt
            if self.slow_timer <= 0:
                self.normalize_all()

    # ----------------------------------------------------------- physics
    def clamp_paddle(self):
        half = self.paddle_w / 2
        self.paddle_x = max(LEFT + half, min(RIGHT - half, self.paddle_x))

    def update(self, dt):
        direction = self.keys["right"] - self.keys["left"]
        if direction:
            self.paddle_x += direction * PADDLE_SPEED * dt
            self.clamp_paddle()

        if self.state == "ready":
            ball = self.balls[0]
            ball.x, ball.y = self.paddle_x, PADDLE_Y + PADDLE_H / 2 + BALL_R
            return
        if self.state != "playing":
            return

        self.update_timers(dt)
        self.update_capsules(dt)

        # two sub-steps per frame so fast balls never skip through bricks
        for _ in range(2):
            for b in [b for b in self.balls if b.active]:
                b.x += b.vx * dt / 2
                b.y += b.vy * dt / 2
                self.collide_walls(b)
                self.collide_paddle(b)
                self.collide_bricks(b)
                if b.y < BOTTOM:
                    b.remove()
            if self.bricks_left == 0:
                self.next_level()
                return
            if not any(b.active for b in self.balls):
                self.lose_life()
                return

    def collide_walls(self, b):
        if b.x < LEFT + BALL_R:
            b.x = LEFT + BALL_R
            b.vx = abs(b.vx)
            self.normalize(b)
        elif b.x > RIGHT - BALL_R:
            b.x = RIGHT - BALL_R
            b.vx = -abs(b.vx)
            self.normalize(b)
        if b.y > TOP - BALL_R:
            b.y = TOP - BALL_R
            b.vy = -abs(b.vy)

    def collide_paddle(self, b):
        top = PADDLE_Y + PADDLE_H / 2
        if (b.vy < 0 and b.y - BALL_R <= top and b.y > PADDLE_Y - PADDLE_H
                and abs(b.x - self.paddle_x) <= self.paddle_w / 2 + BALL_R):
            # where it lands on the paddle decides the bounce angle
            offset = max(-1, min(1, (b.x - self.paddle_x) / (self.paddle_w / 2)))
            angle = offset * math.radians(62)
            s = self.eff_speed()
            b.vx = s * math.sin(angle)
            b.vy = s * math.cos(angle)
            b.y = top + BALL_R

    def collide_bricks(self, b):
        fire = self.fire_timer > 0
        hit_any = False
        for br in self.bricks:
            if not br.alive:
                continue
            dx, dy = b.x - br.x, b.y - br.y
            ox = BRICK_W / 2 + BALL_R - abs(dx)
            oy = BRICK_H / 2 + BALL_R - abs(dy)
            if ox <= 0 or oy <= 0:
                continue
            if not fire:
                # bounce on whichever axis we overlapped the least
                if ox < oy:
                    b.vx = abs(b.vx) * (1 if dx > 0 else -1)
                else:
                    b.vy = abs(b.vy) * (1 if dy > 0 else -1)
            br.destroy()
            self.bricks_left -= 1
            self.score += br.points
            self.burst(br.x, br.y, br.color)
            if br.powerup:
                self.drop_powerup(br.powerup, br.x, br.y)
            hit_any = True
            if not fire:
                break                      # normal ball: one brick per step
        if hit_any:
            self.speed = min(self.speed + 3, MAX_SPEED)    # slowly ramps up
            self.normalize_all()
            self.draw_hud()

    # ------------------------------------------------------- persistence
    def load_high_score(self):
        try:
            with open(HIGHSCORE_FILE) as f:
                return int(f.read().strip())
        except (OSError, ValueError):
            return 0

    def save_high_score(self):
        try:
            with open(HIGHSCORE_FILE, "w") as f:
                f.write(str(self.high_score))
        except OSError:
            pass

    # --------------------------------------------------------- main loop
    def tick(self):
        try:
            now = time.perf_counter()
            dt = min(now - self.last_time, 0.033)
            self.last_time = now
            self.update(dt)
            self.update_particles(dt)
            self.update_toast(dt)
            self.update_status()
            self.draw_objects()
            self.update_blink()
            self.draw_capsule_labels()
            self.screen.update()
            self.screen.ontimer(self.tick, 10)
        except (turtle.Terminator, tkinter.TclError):
            pass                                  # window was closed

    def run(self):
        self.tick()
        self.screen.mainloop()


if __name__ == "__main__":
    Game().run()