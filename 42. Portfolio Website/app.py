import json
import os
from datetime import datetime, timezone

from flask import Flask, flash, redirect, render_template, request, url_for

from data import CERTS, MORE_PROJECTS, PATH, PROFILE, PROJECTS, SKILLS, VOLUNTEERING

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")
MESSAGES_FILE = os.path.join(os.path.dirname(__file__), "messages.jsonl")


@app.route("/")
def home():
    return render_template(
        "index.html", profile=PROFILE, projects=PROJECTS, more=MORE_PROJECTS, skills=SKILLS,
        path=PATH, certs=CERTS, volunteering=VOLUNTEERING,
    )


@app.route("/contact", methods=["POST"])
def contact():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    message = request.form.get("message", "").strip()
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or "application/json" in request.headers.get("Accept", "")

    if request.form.get("website"):  # honeypot: real people leave this empty
        if is_ajax:
            return {"status": "ok", "message": "Message sent."}
        return redirect(url_for("home"))

    if not name or not message or "@" not in email:
        error_msg = "Add your name, a valid email and a message, then send again."
        if is_ajax:
            return {"status": "error", "message": error_msg}, 400
        flash(error_msg, "error")
    else:
        entry = {"time": datetime.now(timezone.utc).isoformat(), "name": name, "email": email, "message": message}
        with open(MESSAGES_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        ok_msg = "Message sent. I’ll reply by email."
        if is_ajax:
            return {"status": "ok", "message": ok_msg}
        flash(ok_msg, "ok")
    return redirect(url_for("home") + "#contact")


if __name__ == "__main__":
    app.run(debug=True)
