"""Cafe & Wifi – a website built on top of the Day 66 cafes database."""
import random
import re
import sqlite3
from pathlib import Path

from flask import (Flask, abort, flash, g, jsonify, redirect,
                   render_template, request, url_for)

BASE = Path(__file__).parent
app = Flask(__name__)
app.config["SECRET_KEY"] = "change-me-in-production"
app.config["DATABASE"] = BASE / "cafes.db"

COFFEE_IMAGES = [
    "https://images.unsplash.com/photo-1445116572660-236099ec97a0",
    "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb",
    "https://images.unsplash.com/photo-1554118811-1e0d58224f24",
    "https://images.unsplash.com/photo-1559925393-8be0ec4767c8",
    "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085",
    "https://images.unsplash.com/photo-1509042239860-f550ce710b93",
    "https://images.unsplash.com/photo-1442512595331-e89e73853f31",
    "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4",
]


@app.template_global()
def fallback_img(cafe_id):
    """Same cafe always gets the same stock photo."""
    return COFFEE_IMAGES[cafe_id % len(COFFEE_IMAGES)] + "?auto=format&fit=crop&w=800&q=80"


AMENITIES = {  # column -> (label, icon)
    "has_wifi": ("Wi-Fi", "📶"),
    "has_sockets": ("Power sockets", "🔌"),
    "has_toilet": ("Toilet", "🚻"),
    "can_take_calls": ("Take calls", "📞"),
}


# ---------- database helpers ----------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def price_value(text):
    m = re.search(r"\d+(?:\.\d+)?", text or "")
    return float(m.group()) if m else None


def seats_value(text):
    nums = re.findall(r"\d+", text or "")
    return int(nums[-1]) if nums else 0


def all_cafes():
    rows = get_db().execute("SELECT * FROM cafe").fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["price_num"] = price_value(d["coffee_price"])
        d["seats_num"] = seats_value(d["seats"])
        out.append(d)
    return out


def compute_stats(cafes):
    prices = [c["price_num"] for c in cafes if c["price_num"]]
    return {
        "count": len(cafes),
        "areas": len({c["location"] for c in cafes}),
        "avg": f"£{sum(prices) / len(prices):.2f}" if prices else "–",
        "wifi": sum(1 for c in cafes if c["has_wifi"]),
    }


def is_ajax():
    return request.headers.get("X-Requested-With") == "fetch"


# ---------- pages ----------
@app.route("/")
def home():
    cafes = all_cafes()
    q = request.args.get("q", "").strip().lower()
    loc = request.args.get("loc", "")
    sort = request.args.get("sort", "name")
    wanted = [a for a in AMENITIES if request.args.get(a)]

    locations = sorted({c["location"] for c in cafes})
    stats = compute_stats(cafes)

    shown = [
        c for c in cafes
        if (not q or q in c["name"].lower() or q in c["location"].lower())
        and (not loc or c["location"] == loc)
        and all(c[a] for a in wanted)
    ]
    keys = {
        "name": lambda c: c["name"].lower(),
        "cheapest": lambda c: (c["price_num"] is None, c["price_num"] or 0),
        "biggest": lambda c: -c["seats_num"],
    }
    shown.sort(key=keys.get(sort, keys["name"]))

    if is_ajax():  # live filtering: only send the results block
        return render_template("_results.html", cafes=shown, amenities=AMENITIES,
                               total=len(cafes))
    return render_template("index.html", total=len(cafes), cafes=shown, locations=locations,
                           stats=stats, amenities=AMENITIES, q=request.args.get("q", ""),
                           loc=loc, sort=sort, wanted=wanted)


@app.route("/random")
def random_cafe():
    cafes = all_cafes()
    if not cafes:
        return redirect(url_for("home"))
    return redirect(url_for("cafe_detail", cafe_id=random.choice(cafes)["id"]))


@app.route("/cafe/<int:cafe_id>")
def cafe_detail(cafe_id):
    row = get_db().execute("SELECT * FROM cafe WHERE id = ?", (cafe_id,)).fetchone()
    if row is None:
        abort(404)
    return render_template("detail.html", c=dict(row), amenities=AMENITIES)


@app.route("/add", methods=["GET", "POST"])
def add_cafe():
    if request.method == "POST":
        f = request.form
        required = ["name", "map_url", "img_url", "location", "seats"]
        if any(not f.get(k, "").strip() for k in required):
            flash("Please fill in all the required fields.", "error")
            return render_template("add.html", amenities=AMENITIES, form=f), 400
        price = f.get("coffee_price", "").strip()
        if price and not price.startswith("£"):
            price = "£" + price
        try:
            db = get_db()
            cur = db.execute(
                """INSERT INTO cafe (name, map_url, img_url, location, has_sockets,
                   has_toilet, has_wifi, can_take_calls, seats, coffee_price)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (f["name"].strip(), f["map_url"].strip(), f["img_url"].strip(),
                 f["location"].strip(), int("has_sockets" in f), int("has_toilet" in f),
                 int("has_wifi" in f), int("can_take_calls" in f),
                 f["seats"].strip(), price or None))
            db.commit()
        except sqlite3.IntegrityError:
            flash("A cafe with that name already exists.", "error")
            return render_template("add.html", amenities=AMENITIES, form=f), 400
        flash(f"“{f['name'].strip()}” was added. Thanks for sharing!", "success")
        return redirect(url_for("cafe_detail", cafe_id=cur.lastrowid))
    return render_template("add.html", amenities=AMENITIES, form={})


@app.route("/cafe/<int:cafe_id>/edit", methods=["GET", "POST"])
def edit_cafe(cafe_id):
    db = get_db()
    row = db.execute("SELECT * FROM cafe WHERE id = ?", (cafe_id,)).fetchone()
    if row is None:
        abort(404)
    if request.method == "POST":
        f = request.form
        required = ["name", "map_url", "img_url", "location", "seats"]
        if any(not f.get(k, "").strip() for k in required):
            flash("Please fill in all the required fields.", "error")
            return render_template("add.html", amenities=AMENITIES, form=f, editing=row["id"]), 400
        price = f.get("coffee_price", "").strip()
        if price and not price.startswith("£"):
            price = "£" + price
        try:
            db.execute(
                """UPDATE cafe SET name=?, map_url=?, img_url=?, location=?, has_sockets=?,
                   has_toilet=?, has_wifi=?, can_take_calls=?, seats=?, coffee_price=? WHERE id=?""",
                (f["name"].strip(), f["map_url"].strip(), f["img_url"].strip(),
                 f["location"].strip(), int("has_sockets" in f), int("has_toilet" in f),
                 int("has_wifi" in f), int("can_take_calls" in f),
                 f["seats"].strip(), price or None, cafe_id))
            db.commit()
        except sqlite3.IntegrityError:
            flash("A cafe with that name already exists.", "error")
            return render_template("add.html", amenities=AMENITIES, form=f, editing=cafe_id), 400
        flash("Changes saved.", "success")
        return redirect(url_for("cafe_detail", cafe_id=cafe_id))
    form = {k: v for k, v in dict(row).items() if k not in AMENITIES or v}
    return render_template("add.html", amenities=AMENITIES, form=form, editing=cafe_id)


@app.route("/cafe/<int:cafe_id>/delete", methods=["POST"])
def delete_cafe(cafe_id):
    db = get_db()
    row = db.execute("SELECT name FROM cafe WHERE id = ?", (cafe_id,)).fetchone()
    if row is None:
        abort(404)
    db.execute("DELETE FROM cafe WHERE id = ?", (cafe_id,))
    db.commit()
    if is_ajax():
        return jsonify(ok=True, name=row["name"], stats=compute_stats(all_cafes()))
    flash(f"“{row['name']}” was removed (reported closed).", "success")
    return redirect(url_for("home"))


@app.errorhandler(404)
def not_found(_e):
    return render_template("404.html"), 404


# ---------- JSON API (the Day 66 API, still available) ----------
@app.route("/api/cafes")
def api_cafes():
    return jsonify(cafes=[{k: v for k, v in c.items() if not k.endswith("_num")}
                          for c in all_cafes()])


if __name__ == "__main__":
    app.run(debug=True)
