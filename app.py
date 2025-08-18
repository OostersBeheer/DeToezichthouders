import os
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

# Load .env bestand
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "defaultsecretkey")
DB_PATH = os.getenv("DB_PATH", "database.db")

# --- Database check / aanmaken ---
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

# --- Homepage: lijst van vacatures ---
@app.route("/")
def index():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM jobs ORDER BY created_at DESC")
    jobs = c.fetchall()
    conn.close()
    return render_template("index.html", jobs=jobs)

# --- Admin login en nieuwe vacature toevoegen ---
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST" and not session.get("admin_logged_in"):
        pw = request.form.get("password")
        if pw == os.getenv("ADMIN_PASSWORD"):
            session["admin_logged_in"] = True
            return redirect(url_for("admin"))
        else:
            return "Onjuist wachtwoord", 403

    if not session.get("admin_logged_in"):
        return '''
            <form method="post">
                <input type="password" name="password" placeholder="Admin wachtwoord">
                <input type="submit" value="Login">
            </form>
        '''

    # Vacature toevoegen
    if request.method == "POST" and session.get("admin_logged_in"):
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
        return redirect(url_for("admin"))

    return render_template("admin.html")

# --- Admin logout ---
@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
