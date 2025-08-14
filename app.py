from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "geheime_sleutel")  # Zet in Render als SECRET_KEY

DATABASE = "jobs.db"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")  # Zet in Render als ADMIN_PASSWORD


def init_db():
    """Maakt database en tabel als die nog niet bestaat."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    hours TEXT,
                    rate TEXT,
                    description TEXT,
                    duration TEXT,
                    start_date TEXT,
                    location TEXT,
                    company TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER,
                    name TEXT,
                    email TEXT,
                    message TEXT,
                    date_applied TEXT
                )''')
    conn.commit()
    conn.close()


@app.route("/")
def index():
    """Toont vacatures met optionele filter."""
    category = request.args.get("category")
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    if category:
        c.execute("SELECT * FROM jobs WHERE location LIKE ?", (f"%{category}%",))
    else:
        c.execute("SELECT * FROM jobs")
    jobs = c.fetchall()
    conn.close()
    return render_template("index.html", jobs=jobs)


@app.route("/job/<int:job_id>", methods=["GET", "POST"])
def job_detail(job_id):
    """Detailpagina van vacature + reactieformulier."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Vacature ophalen
    c.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    job = c.fetchone()

    if not job:
        conn.close()
        flash("Vacature niet gevonden.", "error")
        return redirect(url_for("index"))

    # Reactieformulier verwerken
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        message = request.form["message"]

        if not name or not email:
            flash("Naam en e-mail zijn verplicht.", "error")
        else:
            c.execute('''INSERT INTO applications (job_id, name, email, message, date_applied)
                         VALUES (?, ?, ?, ?, ?)''',
                      (job_id, name, email, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            flash("Je reactie is verzonden!", "success")

    # Reacties ophalen
    c.execute("SELECT name, message, date_applied FROM applications WHERE job_id = ?", (job_id,))
    applications = c.fetchall()

    conn.close()
    return render_template("job_detail.html", job=job, applications=applications)


@app.route("/admin", methods=["GET", "POST"])
def admin():
    """Adminpagina voor vacatures toevoegen."""
    password = request.args.get("password")
    if password != ADMIN_PASSWORD:
        return "Toegang geweigerd", 403

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    if request.method == "POST":
        title = request.form["title"]
        hours = request.form["hours"]
        rate = request.form["rate"]
        description = request.form["description"]
        duration = request.form["duration"]
        start_date = request.form["start_date"]
        location = request.form["location"]
        company = request.form["company"]

        c.execute('''INSERT INTO jobs (title, hours, rate, description, duration, start_date, location, company)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                  (title, hours, rate, description, duration, start_date, location, company))
        conn.commit()
        flash("Vacature toegevoegd!", "success")

    c.execute("SELECT * FROM jobs")
    jobs = c.fetchall()
    conn.close()

    return render_template("admin.html", jobs=jobs)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
