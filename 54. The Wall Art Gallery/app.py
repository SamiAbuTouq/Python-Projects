"""
The Wall - a gallery website powered by the Art Institute of Chicago public API.
API docs: https://api.artic.edu/docs/   (no API key needed)

Run:  pip install -r requirements.txt
      python app.py        ->  http://127.0.0.1:5000
"""
import html
import re
import time

import requests
from flask import Flask, Response, abort, render_template, request

app = Flask(__name__)

API = "https://api.artic.edu/api/v1"
IIIF = "https://www.artic.edu/iiif/2"          # image server (works for every image_id)
HEADERS = {"AIC-User-Agent": "the-wall-student-project (learning REST APIs)"}
PER_PAGE = 24
MAX_RESULTS = 1000                              # the API will not page past 1000 results

LIST_FIELDS = ["id", "title", "artist_display", "artist_title", "date_display", "image_id", "thumbnail"]
DETAIL_FIELDS = LIST_FIELDS + [
    "artist_id", "medium_display", "dimensions", "place_of_origin", "style_title",
    "classification_title", "department_title", "credit_line", "description",
    "short_description", "gallery_title", "is_on_view",
]

TOPICS = ["Impressionism", "Japanese prints", "Surrealism", "Ancient Egypt",
          "Cubism", "Portrait", "Still life", "Landscape", "Armor"]

# ---------- tiny in-memory cache so we are polite to the API ----------
_cache = {}


def cached_request(key, fn, ttl=600):
    now = time.time()
    hit = _cache.get(key)
    if hit and now - hit[0] < ttl:
        return hit[1]
    value = fn()
    _cache[key] = (now, value)
    return value


# ---------- helpers ----------
def img(image_id, width):
    """URL of OUR image proxy (the browser never talks to the museum directly)."""
    return f"/img/{image_id}?w={width}"


def clean_text(raw):
    """The API returns HTML in some fields - strip the tags."""
    if not raw:
        return ""
    return html.unescape(re.sub(r"<[^>]+>", "", raw)).strip()


def shape(item):
    """Turn an API record into what the templates need."""
    thumb = item.get("thumbnail") or {}
    w, h = thumb.get("width") or 4, thumb.get("height") or 5
    artist = (item.get("artist_display") or "Unknown artist").split("\n")[0]
    return {
        "id": item["id"],
        "title": item.get("title") or "Untitled",
        "artist": artist,
        "date": item.get("date_display") or "",
        "src": img(item["image_id"], 843),
        "ratio": f"{w} / {h}",
        "lqip": thumb.get("lqip"),
        "alt": thumb.get("alt_text") or item.get("title") or "Artwork",
    }


def search_artworks(q, page, artist_id=None, limit=PER_PAGE):
    """GET search: public domain only. Records without an image are skipped later."""
    params = {"fields": ",".join(LIST_FIELDS), "limit": limit, "page": page,
              "query[term][is_public_domain]": "true"}
    if q:
        params["q"] = q
    if artist_id:
        params["query[term][artist_id]"] = artist_id

    def go():
        r = requests.get(f"{API}/artworks/search", params=params, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return r.json()

    return cached_request(("search", q, page, artist_id, limit), go)


_img_cache = {}


@app.route("/img/<image_id>")
def image_proxy(image_id):
    """Fetch the picture server-side (with a proper User-Agent) and pass it on."""
    width = request.args.get("w", 843, type=int)
    if width not in (843, 1686) or not re.fullmatch(r"[0-9a-fA-F-]{20,40}", image_id):
        abort(400)
    key = (image_id, width)
    if key not in _img_cache:
        try:
            r = requests.get(f"{IIIF}/{image_id}/full/{width},/0/default.jpg",
                             headers={**HEADERS, "Accept": "image/jpeg,image/*"}, timeout=20)
        except requests.RequestException:
            abort(502)
        if r.status_code != 200 or not r.content:
            abort(502)
        if len(_img_cache) > 150:
            _img_cache.clear()
        _img_cache[key] = r.content
    return Response(_img_cache[key], mimetype="image/jpeg",
                    headers={"Cache-Control": "public, max-age=86400"})


# ---------- routes ----------
@app.route("/")
def index():
    q = request.args.get("q", "").strip() or "Impressionism"
    page = max(1, request.args.get("page", 1, type=int))
    error, works, total_pages, total = None, [], 1, 0
    try:
        data = search_artworks(q, page)
        works = [shape(i) for i in data["data"] if i.get("image_id")]
        total = data["pagination"]["total"]
        total_pages = min(data["pagination"]["total_pages"], MAX_RESULTS // PER_PAGE)
    except requests.RequestException:
        error = "The gallery could not be reached. Check your internet connection and try again."
    return render_template("index.html", q=q, works=works, page=page, total=total,
                           total_pages=total_pages, topics=TOPICS, error=error)


@app.route("/artwork/<int:art_id>")
def artwork(art_id):
    def go():
        r = requests.get(f"{API}/artworks/{art_id}", params={"fields": ",".join(DETAIL_FIELDS)},
                         headers=HEADERS, timeout=12)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()["data"]

    try:
        a = cached_request(("art", art_id), go, ttl=3600)
    except requests.RequestException:
        return render_template("artwork.html", art=None, error=True), 502
    if not a or not a.get("image_id"):
        abort(404)

    art = {
        "id": a["id"],
        "title": a.get("title") or "Untitled",
        "artist": (a.get("artist_display") or "Unknown artist").replace("\n", ", "),
        "date": a.get("date_display"),
        "large": img(a["image_id"], 843),
        "full": img(a["image_id"], 1686),
        "alt": (a.get("thumbnail") or {}).get("alt_text") or a.get("title"),
        "about": clean_text(a.get("description") or a.get("short_description")),
        "facts": [(k, v) for k, v in [
            ("Medium", a.get("medium_display")), ("Dimensions", a.get("dimensions")),
            ("Origin", a.get("place_of_origin")), ("Style", a.get("style_title")),
            ("Type", a.get("classification_title")), ("Department", a.get("department_title")),
            ("Credit", a.get("credit_line")),
            ("On view", f"Gallery {a['gallery_title']}" if a.get("is_on_view") and a.get("gallery_title")
             else ("Not currently on view" if a.get("is_on_view") is False else None)),
        ] if v],
    }

    more = []
    if a.get("artist_id"):
        try:
            data = search_artworks("", 1, artist_id=a["artist_id"], limit=7)
            more = [shape(i) for i in data["data"] if i.get("image_id") and i["id"] != a["id"]][:6]
        except requests.RequestException:
            pass
    return render_template("artwork.html", art=art, more=more, error=False)


@app.errorhandler(404)
def not_found(_):
    return render_template("artwork.html", art=None, error=False), 404


if __name__ == "__main__":
    app.run(debug=True)
