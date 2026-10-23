"""TaskFlow - a Kanban-style task manager built with Flask + SQLite."""
import sqlite3
from pathlib import Path

from flask import Flask, g, jsonify, render_template, request

BASE = Path(__file__).parent
DB_PATH = BASE / "tasks.db"

STATUSES = ("todo", "doing", "done")
PRIORITIES = ("low", "medium", "high")

app = Flask(__name__)


# ---------------------------------------------------------------- database
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                status      TEXT NOT NULL DEFAULT 'todo',
                priority    TEXT NOT NULL DEFAULT 'medium',
                due_date    TEXT,
                position    INTEGER NOT NULL DEFAULT 0,
                created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        if con.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 0:
            samples = [
                ("Welcome to TaskFlow", "Drag cards between columns. Click a card to edit it.", "todo", "high"),
                ("Design the landing page", "Pick a colour palette and sketch the layout.", "todo", "medium"),
                ("Build the REST API", "CRUD endpoints with Flask and SQLite.", "doing", "high"),
                ("Set up the project", "Create the repo and install Flask.", "done", "low"),
            ]
            for pos, (t, d, s, p) in enumerate(samples):
                con.execute(
                    "INSERT INTO tasks (title, description, status, priority, position) VALUES (?,?,?,?,?)",
                    (t, d, s, p, pos),
                )


def row_to_dict(row):
    return dict(row)


def clean(data, partial=False):
    """Validate and normalise incoming task data. Returns (values, error)."""
    out = {}
    if "title" in data or not partial:
        title = str(data.get("title", "")).strip()
        if not title:
            return None, "Title is required."
        out["title"] = title[:120]
    if "description" in data:
        out["description"] = str(data["description"]).strip()[:500]
    if "status" in data:
        if data["status"] not in STATUSES:
            return None, "Invalid status."
        out["status"] = data["status"]
    if "priority" in data:
        if data["priority"] not in PRIORITIES:
            return None, "Invalid priority."
        out["priority"] = data["priority"]
    if "due_date" in data:
        out["due_date"] = (data["due_date"] or None)
    return out, None


# ------------------------------------------------------------------ routes
@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/tasks")
def list_tasks():
    rows = get_db().execute("SELECT * FROM tasks ORDER BY position, id").fetchall()
    return jsonify([row_to_dict(r) for r in rows])


@app.post("/api/tasks")
def create_task():
    values, err = clean(request.get_json(silent=True) or {})
    if err:
        return jsonify(error=err), 400
    db = get_db()
    status = values.get("status", "todo")
    pos = db.execute(
        "SELECT COALESCE(MAX(position), -1) + 1 FROM tasks WHERE status = ?", (status,)
    ).fetchone()[0]
    cur = db.execute(
        "INSERT INTO tasks (title, description, status, priority, due_date, position) VALUES (?,?,?,?,?,?)",
        (
            values["title"],
            values.get("description", ""),
            status,
            values.get("priority", "medium"),
            values.get("due_date"),
            pos,
        ),
    )
    db.commit()
    row = db.execute("SELECT * FROM tasks WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(row_to_dict(row)), 201


@app.patch("/api/tasks/<int:task_id>")
def update_task(task_id):
    values, err = clean(request.get_json(silent=True) or {}, partial=True)
    if err:
        return jsonify(error=err), 400
    if not values:
        return jsonify(error="Nothing to update."), 400
    db = get_db()
    if not db.execute("SELECT 1 FROM tasks WHERE id = ?", (task_id,)).fetchone():
        return jsonify(error="Task not found."), 404
    sets = ", ".join(f"{k} = ?" for k in values)
    db.execute(f"UPDATE tasks SET {sets} WHERE id = ?", (*values.values(), task_id))
    db.commit()
    row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return jsonify(row_to_dict(row))


@app.delete("/api/tasks/<int:task_id>")
def delete_task(task_id):
    db = get_db()
    cur = db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    db.commit()
    if cur.rowcount == 0:
        return jsonify(error="Task not found."), 404
    return "", 204


@app.put("/api/reorder")
def reorder():
    """Body: {"status": "doing", "ids": [3, 1, 7]} -> sets column + order."""
    data = request.get_json(silent=True) or {}
    status, ids = data.get("status"), data.get("ids")
    if status not in STATUSES or not isinstance(ids, list):
        return jsonify(error="Invalid payload."), 400
    db = get_db()
    for pos, task_id in enumerate(ids):
        db.execute(
            "UPDATE tasks SET status = ?, position = ? WHERE id = ?",
            (status, pos, int(task_id)),
        )
    db.commit()
    return jsonify(ok=True)


init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
