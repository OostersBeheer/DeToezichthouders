import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime

app = Flask(__name__)
DB_PATH = "jobs.db"

# --- Database setup ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            hours TEXT,
            rate REAL,
            description TEXT,
            duration TEXT,
            start_date TEXT,
            location TEXT,
            company TEXT,
            categories TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()


# --- Homepage (lijst met opdrachten) ---
@app.route("/")
def index():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Filters op categorie (checkboxes)
    selected = request.args.getlist("cat")
    if selected:
        placeholders = " OR ".join(["categories LIKE ?"] * len(selected))
        query = f"SELECT * FROM jobs WHERE {placeholders} ORDER BY created_at DESC"
        params = [f"%{cat}%" for cat in selected]
        c.execute(query, params)
    else:
        c.execute("SELECT * FROM jobs ORDER BY created_at DESC")
    jobs = c.fetchall()
    conn.close()

    categories = [
        ("toezicht", "Toezicht"),
        ("handhaving", "Handhaving"),
        ("projectleiding", "Projectleiding"),
        ("advies", "Advies")
    ]

    return render_template("index.html", jobs=jobs, categories=categories, selected=selected)


# --- Detailpagina van een opdracht ---
@app.route("/job/<int:job_id>")
def job_detail(job_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    job = c.fetchone()
    conn.close()

    if not job:
        return "Opdracht niet gevonden", 404

    return render_template("job_detail.html", job=job)


# --- Admin: nieuwe opdracht toevoegen ---
@app.route("/admin", methods=["GET", "POST"])
def admin():
    pw = request.args.get("pw")
    if pw != os.getenv("ADMIN_PASSWORD", "ZiggeZaggeNAC1912"):
        return "Toegang geweigerd", 403

    if request.method == "POST":
        title = request.form["title"]
        hours = request.form.get("hours")
        rate = request.form.get("rate")
        description = request.form.get("description")
        duration = request.form.get("duration")
        start_date = request.form.get("start_date")
        location = request.form.get("location")
        company = request.form.get("company")
        categories = request.form.getlist("categories")
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            INSERT INTO jobs (title, hours, rate, description, duration, start_date, location, company, categories, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            title,
            hours,
            float(rate) if rate else None,
            description,
            duration,
            start_date,
            location,
            company,
            ",".join(categories),
            created_at
        ))
        conn.commit()
        conn.close()
        return redirect(url_for("index"))

    return render_template("admin.html")

# app.py

from flask import render_template

@app.route('/about')
def about():
    return render_template('about.html')

# --- Start de app ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
