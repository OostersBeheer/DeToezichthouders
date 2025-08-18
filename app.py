import os from flask import Flask, render_template, request, redirect, url_for, session
app = Flask(__name__)

# Zorg dat de sessie werkt
app.secret_key = os.getenv("SECRET_KEY", "ZiggeZaggeNAC1912!")

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

# --- Admin login en nieuwe opdracht toevoegen ---
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if "login" in request.form:  # login formulier
            pw = request.form.get("password")
            if pw != os.getenv("ADMIN_PASSWORD"):
                session["admin_logged_in"] = True
                return redirect(url_for("admin"))
            else:
                return "Onjuist wachtwoord", 403

        elif "add_job" in request.form:  # nieuw job formulier
            if not session.get("admin_logged_in"):
                return "Toegang geweigerd", 403
            # Haal de velden uit het formulier
            title = request.form.get("title")
            company = request.form.get("company")
            location = request.form.get("location")
            hours = request.form.get("hours")
            rate = request.form.get("rate")
            description = request.form.get("description")
            categories = request.form.getlist("categories")

            c = get_db().cursor()
            c.execute(
                "INSERT INTO jobs (title, company, location, hours, rate, description, categories, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
                (title, company, location, hours, rate, description, ",".join(categories))
            )
            get_db().commit()
            return redirect(url_for("index"))

    if not session.get("admin_logged_in"):
        # Login formulier
        return render_template("admin.html", login=True)

    # Vacature toevoegen formulier
    return render_template("admin.html", login=False, categories=[
        ("finance", "Finance"),
        ("it", "IT"),
        ("construction", "Construction"),
        ("other", "Other")
    ])

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
