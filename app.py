import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "fallback-secret-key")

# Zet database pad altijd relatief aan dit bestand
DB_PATH = os.path.join(os.path.dirname(__file__), "jobs.db")

# Database initialisatie
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            hours TEXT,
            rate TEXT,
            description TEXT,
            duration TEXT,
            start_date TEXT,
            location TEXT,
            company TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            message TEXT,
            FOREIGN KEY(job_id) REFERENCES jobs(id)
        )
    """)
    conn.commit()
    conn.close()

# Init DB bij eerste start
init_db()

@app.route("/")
def index():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM jobs")
    jobs = c.fetchall()
    conn.close()
    return render_template("index.html", jobs=jobs)

@app.route("/job/<int:job_id>")
def job_detail(job_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    job = c.fetchone()
    conn.close()
    return render_template("job_detail.html", job=job)

@app.route("/apply/<int:job_id>", methods=["POST"])
def apply(job_id):
    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    message = request.form.get("message")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO applications (job_id, name, email, phone, message) VALUES (?, ?, ?, ?, ?)",
        (job_id, name, email, phone, message),
    )
    conn.commit()
    conn.close()
    flash("Je sollicitatie is verzonden!", "success")
    return redirect(url_for("index"))

@app.route("/admin", methods=["GET", "POST"])
def admin():
    admin_pw = os.environ.get("ADMIN_PASSWORD", "fallback-password")
    if request.args.get("pw") != admin_pw:
        return "Toegang geweigerd", 403

    if request.method == "POST":
        title = request.form.get("title")
        hours = request.form.get("hours")
        rate = request.form.get("rate")
        description = request.form.get("description")
        duration = request.form.get("duration")
        start_date = request.form.get("start_date")
        location = request.form.get("location")
        company = request.form.get("company")

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            INSERT INTO jobs (title, hours, rate, description, duration, start_date, location, company)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, hours, rate, description, duration, start_date, location, company))
        conn.commit()
        conn.close()
        flash("Vacature toegevoegd!", "success")
        return redirect(url_for("admin", pw=admin_pw))

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM jobs")
    jobs = c.fetchall()
    conn.close()
    return render_template("admin.html", jobs=jobs)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
