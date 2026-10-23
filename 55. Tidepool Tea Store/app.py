"""Tidepool Tea: a small Flask eCommerce store with Stripe Checkout."""
import json
import os
from datetime import datetime
from urllib.parse import urljoin, urlparse

import stripe
from dotenv import load_dotenv
from flask import (Flask, abort, flash, jsonify, redirect, render_template,
                   request, session, url_for)
from flask_login import (LoginManager, UserMixin, current_user, login_required,
                         login_user, logout_user)
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
    SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "sqlite:///tidepool.db"),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

CURRENCY = "usd"
FREE_SHIPPING_FROM = 4000   # cents
FLAT_SHIPPING = 500         # cents
MAX_QTY = 20
SHIP_TO = ["US", "CA", "GB", "AU", "DE", "FR", "NL", "JO", "AE"]

db = SQLAlchemy(app)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Log in to continue."


# --------------------------------------------------------------------------- #
# Models
# --------------------------------------------------------------------------- #
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    orders = db.relationship("Order", backref="user", lazy=True,
                             order_by="Order.created_at.desc()")


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    mark = db.Column(db.String(20), nullable=False)       # short label on the artwork
    tagline = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(20), nullable=False)   # tea | gear
    price_cents = db.Column(db.Integer, nullable=False)
    color = db.Column(db.String(9), nullable=False)
    accent = db.Column(db.String(9), nullable=False)
    shape = db.Column(db.String(10), default="tin")       # tin | cup | pot
    origin = db.Column(db.String(80))
    steep = db.Column(db.String(80))
    tasting = db.Column(db.String(160))


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    stripe_session_id = db.Column(db.String(255), unique=True, nullable=False)
    total_cents = db.Column(db.Integer, nullable=False)
    shipping_cents = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default="paid")
    ship_to = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship("OrderItem", backref="order", lazy=True,
                            cascade="all, delete-orphan")


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    name = db.Column(db.String(160), nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    total_cents = db.Column(db.Integer, nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
@app.template_filter("money")
def money(cents):
    return "${:,.2f}".format((cents or 0) / 100)


def is_safe_url(target):
    if not target:
        return False
    host = urlparse(request.host_url)
    test = urlparse(urljoin(request.host_url, target))
    return test.scheme in ("http", "https") and host.netloc == test.netloc


def get_cart():
    return session.get("cart", {})


def cart_lines():
    cart = get_cart()
    ids = [int(i) for i in cart]
    products = {p.id: p for p in Product.query.filter(Product.id.in_(ids))} if ids else {}
    lines = []
    for pid, qty in cart.items():
        product = products.get(int(pid))
        if product:
            lines.append({"product": product, "qty": qty,
                          "total": product.price_cents * qty})
    return lines


def cart_totals(lines):
    subtotal = sum(l["total"] for l in lines)
    shipping = 0 if (not lines or subtotal >= FREE_SHIPPING_FROM) else FLAT_SHIPPING
    return {
        "subtotal": subtotal,
        "shipping": shipping,
        "total": subtotal + shipping,
        "to_free": max(FREE_SHIPPING_FROM - subtotal, 0),
        "progress": min(int(subtotal / FREE_SHIPPING_FROM * 100), 100) if lines else 0,
    }


@app.context_processor
def inject_globals():
    return {
        "cart_count": sum(get_cart().values()),
        "free_from": FREE_SHIPPING_FROM,
        "year": datetime.utcnow().year,
    }


def back_or(endpoint):
    ref = request.referrer
    return redirect(ref if ref and is_safe_url(ref) else url_for(endpoint))


# --------------------------------------------------------------------------- #
# Storefront
# --------------------------------------------------------------------------- #
@app.route("/")
def index():
    category = request.args.get("category", "")
    q = request.args.get("q", "").strip()
    query = Product.query
    if category in ("tea", "gear"):
        query = query.filter_by(category=category)
    if q:
        like = f"%{q}%"
        query = query.filter(Product.name.ilike(like) | Product.tagline.ilike(like))
    products = query.order_by(Product.id).all()
    return render_template("index.html", products=products, category=category, q=q)


@app.route("/product/<slug>")
def product(slug):
    item = Product.query.filter_by(slug=slug).first_or_404()
    related = (Product.query.filter(Product.id != item.id,
                                    Product.category == item.category)
               .limit(3).all())
    return render_template("product.html", p=item, related=related)


# --------------------------------------------------------------------------- #
# Cart
# --------------------------------------------------------------------------- #
@app.route("/cart")
def cart():
    lines = cart_lines()
    return render_template("cart.html", lines=lines, t=cart_totals(lines))


@app.post("/cart/add/<int:product_id>")
def cart_add(product_id):
    item = db.get_or_404(Product, product_id)
    try:
        qty = max(1, int(request.form.get("qty", 1)))
    except ValueError:
        qty = 1
    cart_data = get_cart()
    key = str(item.id)
    cart_data[key] = min(cart_data.get(key, 0) + qty, MAX_QTY)
    session["cart"] = cart_data
    message = f"{item.name} added to your cart."
    if request.headers.get("X-Requested-With") == "fetch":   # no page reload
        return jsonify(ok=True, count=sum(cart_data.values()), message=message)
    flash(message, "ok")
    return back_or("cart")


def is_fetch():
    return request.headers.get("X-Requested-With") == "fetch"


def cart_payload(removed=None):
    """Everything the cart page needs to redraw itself without a reload."""
    lines = cart_lines()
    t = cart_totals(lines)
    return jsonify(
        ok=True,
        removed=removed,
        empty=not lines,
        count=sum(get_cart().values()),
        lines={str(l["product"].id): {"qty": l["qty"], "total": money(l["total"])}
               for l in lines},
        subtotal=money(t["subtotal"]),
        shipping="Free" if t["shipping"] == 0 else money(t["shipping"]),
        total=money(t["total"]),
        to_free=t["to_free"],
        to_free_fmt=money(t["to_free"]),
        progress=t["progress"],
    )


@app.post("/cart/update/<int:product_id>")
def cart_update(product_id):
    cart_data = get_cart()
    key = str(product_id)
    removed = None
    if key in cart_data:
        try:
            qty = int(request.form.get("qty", 1))
        except ValueError:
            qty = cart_data[key]
        if qty <= 0:
            cart_data.pop(key)
            removed = product_id
        else:
            cart_data[key] = min(qty, MAX_QTY)
        session["cart"] = cart_data
    if is_fetch():
        return cart_payload(removed)
    return redirect(url_for("cart"))


@app.post("/cart/remove/<int:product_id>")
def cart_remove(product_id):
    cart_data = get_cart()
    cart_data.pop(str(product_id), None)
    session["cart"] = cart_data
    if is_fetch():
        return cart_payload(product_id)
    flash("Item removed.", "ok")
    return redirect(url_for("cart"))


# --------------------------------------------------------------------------- #
# Auth
# --------------------------------------------------------------------------- #
@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        error = None
        if not name:
            error = "Enter your name."
        elif "@" not in email or "." not in email.split("@")[-1]:
            error = "Enter a valid email address."
        elif len(password) < 8:
            error = "Use a password with at least 8 characters."
        elif password != confirm:
            error = "The two passwords don't match."
        elif User.query.filter_by(email=email).first():
            error = "An account with that email already exists. Try logging in."
        if error:
            flash(error, "error")
            return render_template("register.html", name=name, email=email), 400
        user = User(name=name, email=email,
                    password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash(f"Welcome, {user.name.split()[0]}. Your account is ready.", "ok")
        nxt = request.args.get("next")
        return redirect(nxt if is_safe_url(nxt) else url_for("index"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash,
                                        request.form.get("password", "")):
            login_user(user, remember=bool(request.form.get("remember")))
            nxt = request.args.get("next")
            return redirect(nxt if is_safe_url(nxt) else url_for("index"))
        flash("That email and password don't match.", "error")
        return render_template("login.html", email=email), 401
    return render_template("login.html")


@app.post("/logout")
def logout():
    logout_user()
    flash("You're logged out.", "ok")
    return redirect(url_for("index"))


# --------------------------------------------------------------------------- #
# Checkout (Stripe)
# --------------------------------------------------------------------------- #
@app.post("/checkout")
@login_required
def checkout():
    lines = cart_lines()
    if not lines:
        flash("Your cart is empty.", "error")
        return redirect(url_for("index"))
    if not stripe.api_key:
        flash("Stripe isn't configured yet. Add STRIPE_SECRET_KEY to your .env file.", "error")
        return redirect(url_for("cart"))

    totals = cart_totals(lines)
    # Prices always come from the database, never from the browser.
    line_items = [{
        "quantity": l["qty"],
        "price_data": {
            "currency": CURRENCY,
            "unit_amount": l["product"].price_cents,
            "product_data": {"name": l["product"].name,
                             "description": l["product"].tagline},
        },
    } for l in lines]

    try:
        checkout_session = stripe.checkout.Session.create(
            mode="payment",
            line_items=line_items,
            customer_email=current_user.email,
            client_reference_id=str(current_user.id),
            shipping_address_collection={"allowed_countries": SHIP_TO},
            shipping_options=[{
                "shipping_rate_data": {
                    "type": "fixed_amount",
                    "fixed_amount": {"amount": totals["shipping"], "currency": CURRENCY},
                    "display_name": "Free shipping" if totals["shipping"] == 0
                    else "Standard shipping",
                },
            }],
            success_url=url_for("success", _external=True)
            + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=url_for("cart", _external=True),
        )
    except stripe.StripeError as exc:
        app.logger.exception("Stripe error")
        flash(f"Payment couldn't start: {getattr(exc, 'user_message', None) or 'please try again.'}", "error")
        return redirect(url_for("cart"))
    return redirect(checkout_session.url, code=303)


def fulfill_order(cs):
    """Create the Order once per paid Checkout Session (safe to call repeatedly)."""
    existing = Order.query.filter_by(stripe_session_id=cs["id"]).first()
    if existing:
        return existing
    if cs.get("payment_status") != "paid":
        return None
    user_id = cs.get("client_reference_id")
    if not user_id:
        return None

    shipping_info = (cs.get("shipping_details")
                     or (cs.get("collected_information") or {}).get("shipping_details")
                     or {})
    addr = shipping_info.get("address") or {}
    ship_to = ", ".join(filter(None, [
        shipping_info.get("name"), addr.get("line1"), addr.get("line2"),
        addr.get("city"), addr.get("state"), addr.get("postal_code"),
        addr.get("country")]))

    order = Order(
        user_id=int(user_id),
        stripe_session_id=cs["id"],
        total_cents=cs.get("amount_total") or 0,
        shipping_cents=(cs.get("total_details") or {}).get("amount_shipping") or 0,
        ship_to=ship_to,
    )
    for li in (cs.get("line_items") or {}).get("data", []):
        order.items.append(OrderItem(name=li["description"], qty=li["quantity"],
                                     total_cents=li["amount_total"]))
    db.session.add(order)
    db.session.commit()
    return order


@app.route("/checkout/success")
@login_required
def success():
    session_id = request.args.get("session_id", "")
    if not session_id:
        return redirect(url_for("index"))
    try:
        # Newer stripe-python objects are not dicts, so convert to a plain dict.
        cs = stripe.checkout.Session.retrieve(session_id, expand=["line_items"]).to_dict()
    except stripe.StripeError:
        abort(404)
    if cs.get("client_reference_id") != str(current_user.id):
        abort(403)
    order = fulfill_order(cs)
    if order:
        session.pop("cart", None)
    return render_template("success.html", order=order)


@app.post("/stripe/webhook")
@csrf.exempt
def stripe_webhook():
    """Optional safety net: creates the order even if the shopper closes the tab."""
    if not WEBHOOK_SECRET:
        abort(404)
    try:
        event = stripe.Webhook.construct_event(
            request.data, request.headers.get("Stripe-Signature", ""), WEBHOOK_SECRET)
    except (ValueError, stripe.SignatureVerificationError):
        abort(400)
    if event["type"] in ("checkout.session.completed",
                         "checkout.session.async_payment_succeeded"):
        cs = stripe.checkout.Session.retrieve(event["data"]["object"]["id"],
                                              expand=["line_items"]).to_dict()
        fulfill_order(cs)
    return "", 200


@app.route("/orders")
@login_required
def orders():
    return render_template("orders.html", orders=current_user.orders)


# --------------------------------------------------------------------------- #
# Seed data
# --------------------------------------------------------------------------- #
SEED = [
    dict(slug="jasmine-pearl", name="Jasmine Pearl", mark="Jasmine", category="tea",
         tagline="Hand-rolled green tea scented over fresh jasmine blossoms.",
         description="Each pearl unfurls into a whole leaf and bud as it steeps. Scented in small batches over several nights, so the floral note stays soft and never perfumey. 80 g tin, about 40 cups.",
         price_cents=1800, color="#2F6B4F", accent="#F3E7B0", origin="Fujian, China",
         steep="80 °C · 2 min", tasting="Orchard blossom, sweet grass, clean finish"),
    dict(slug="smoked-lapsang", name="Smoked Lapsang", mark="Lapsang", category="tea",
         tagline="Black tea dried over pinewood fires. Deep, resinous, campfire-warm.",
         description="A bold black tea for people who want their cup to taste like a cabin in winter. Pairs well with salty cheese and rainy afternoons. 80 g tin, about 35 cups.",
         price_cents=1600, color="#43302A", accent="#F26B5B", origin="Wuyi Mountains, China",
         steep="95 °C · 3 min", tasting="Pine smoke, dried longan, dark honey"),
    dict(slug="roasted-barley", name="Roasted Barley", mark="Barley", category="tea",
         tagline="Caffeine-free mugicha, toasty and nutty. Good hot or iced.",
         description="Whole barley roasted until it smells like fresh bread. Naturally caffeine free, so it works at midnight. Cold-brew a jug in the fridge for summer. 150 g tin, about 50 cups.",
         price_cents=1400, color="#9A6A33", accent="#FFE8AE", origin="Saga, Japan",
         steep="100 °C · 5 min", tasting="Toasted grain, cocoa nib, mellow sweetness"),
    dict(slug="sencha-morning", name="Sencha Morning", mark="Sencha", category="tea",
         tagline="Bright, grassy Japanese green tea for the first cup of the day.",
         description="Steamed within hours of picking to lock in colour and freshness. Brew it cooler and shorter than you think for a sweet, savoury cup. 80 g tin, about 40 cups.",
         price_cents=2000, color="#5E9B48", accent="#F3F6F1", origin="Shizuoka, Japan",
         steep="70 °C · 1 min", tasting="Fresh peas, sea air, lemon zest"),
    dict(slug="hibiscus-ember", name="Hibiscus Ember", mark="Hibiscus", category="tea",
         tagline="Tart, ruby-red herbal blend with orange peel and cinnamon.",
         description="A caffeine-free blend that looks as good as it tastes. Delicious hot, spectacular over ice with a squeeze of lime. 100 g tin, about 40 cups.",
         price_cents=1500, color="#A3203A", accent="#FFBE3D", origin="Blend of Egypt and Sri Lanka",
         steep="100 °C · 6 min", tasting="Cranberry, orange peel, warm spice"),
    dict(slug="earl-grey-reserve", name="Earl Grey Reserve", mark="Earl Grey", category="tea",
         tagline="Ceylon black tea with real bergamot oil and cornflower petals.",
         description="Our everyday black tea. Brisk enough for milk, fragrant enough to drink plain. 100 g tin, about 45 cups.",
         price_cents=1700, color="#2D4A7A", accent="#CFE6DA", origin="Uva, Sri Lanka",
         steep="95 °C · 4 min", tasting="Bergamot, malt, a little citrus peel"),
    dict(slug="stoneware-cup", name="Stoneware Cup", mark="Cup", category="gear",
         tagline="Hand-glazed 200 ml cup that keeps your tea hot a little longer.",
         description="Thrown and glazed in small runs, so no two are identical. Dishwasher and microwave safe. Sold individually.",
         price_cents=2400, color="#FFBE3D", accent="#10302E", shape="cup",
         origin="Made in Portugal", steep="200 ml", tasting="Speckled glaze, thick walls"),
    dict(slug="glass-teapot", name="Glass Teapot", mark="Pot", category="gear",
         tagline="Heat-proof borosilicate pot with a stainless steel infuser.",
         description="Watch the leaves open. The wide basket gives tea room to expand, and the spout pours without dripping. 600 ml, about 3 cups.",
         price_cents=4200, color="#F26B5B", accent="#10302E", shape="pot",
         origin="Designed in Berlin", steep="600 ml", tasting="Borosilicate glass, steel infuser"),
]


def seed():
    if Product.query.count() == 0:
        db.session.add_all(Product(**row) for row in SEED)
        db.session.commit()


with app.app_context():
    db.create_all()
    seed()

if __name__ == "__main__":
    app.run(debug=True)
