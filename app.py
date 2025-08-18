import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

# Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "fallback-secret-key")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

# Altijd een pad gebruiken relatief aan dit bestand
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "jobs.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # prettiger in templates: job['title']
    return conn

def init_db():
    """Maak tabellen als ze nog niet bestaan (idempotent)."""
    with get_conn() as conn:
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

        c.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT,
                message TEXT,
                date_applied TEXT,
                FOREIGN KEY(job_id) REFERENCES jobs(id)
            )
        """)
        conn.commit()

# >>> Kritiek: zorg dat tabellen er zijn zodra de app module geladen wordt (ook bij gunicorn)
init_db()

@app.route("/")
def index():
    # optioneel simpel zoekveld (q) over titel/bedrijf/locatie
    q = request.args.get("q", "").strip()
    with get_conn() as conn:
        c = conn.cursor()
        if q:
            like = f"%{q}%"
            c.execute("""
                SELECT * FROM jobs
                WHERE title LIKE ? OR company LIKE ? OR location LIKE ?
                ORDER BY id DESC
            """, (like, like, like))
        else:
            c.execute("SELECT * FROM jobs ORDER BY id DESC")
        jobs = c.fetchall()
    return render_template("index.html", jobs=jobs)

@app.route("/job/<int:job_id>", methods=["GET", "POST"])
def job_detail(job_id):
    with get_conn() as conn:
        c = conn.cursor()
        # Haal vacature op
        c.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        job = c.fetchone()
        if not job:
            flash("Vacature niet gevonden.", "error")
            return redirect(url_for("index"))

        # Verwerk reactie
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            phone = request.form.get("phone", "").strip()
            message = request.form.get("message", "").strip()
            if not name or not email:
                flash("Naam en e‑mail zijn verplicht.", "error")
            else:
                c.execute("""
                    INSERT INTO applications (job_id, name, email, phone, message, date_applied)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (job_id, name, email, phone, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                flash("Je reactie is verzonden!", "success")
        # (optioneel) je kunt hier reacties ophalen en meegeven aan de template

    return render_template("job_detail.html", job=job)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    # Queryparameter heet 'pw' (bijv. /admin?pw=JOUW_WACHTWOORD)
    if request.args.get("pw") != ADMIN_PASSWORD:
        return "Toegang geweigerd", 403

    with get_conn() as conn:
        c = conn.cursor()
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            hours = request.form.get("hours", "").strip()
            rate = request.form.get("rate", "").strip()
            description = request.form.get("description", "").strip()
            duration = request.form.get("duration", "").strip()
            start_date = request.form.get("start_date", "").strip()
            location = request.form.get("location", "").strip()
            company = request.form.get("company", "").strip()

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
    "",  # voorlopig geen categorieën
    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
))

            conn.commit()
            flash("Vacature toegevoegd!", "success")

        c.execute("SELECT * FROM jobs ORDER BY id DESC")
        jobs = c.fetchall()

    return render_template("admin.html", jobs=jobs)

if __name__ == "__main__":
    # Lokale run
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
