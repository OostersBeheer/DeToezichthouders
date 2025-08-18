import os
import sqlite3
from datetime import datetime
from flask import Flask, request, session, redirect, url_for, render_template

app = Flask(__name__)

# Secret key en database path uit environment variables
app.secret_key = os.getenv("SECRET_KEY", "ZiggeZaggeNAC1912!")
DB_PATH = os.getenv("DB_PATH", "database.db")

# --- Database check & aanmaken ---
def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE jobs (
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

# --- Index route ---
@app.route("/")
def index():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM jobs ORDER BY created_at DESC")
    jobs = c.fetchall()
    conn.close()
    return render_template("index.html", jobs=jobs)

# --- Admin login en vacatures toevoegen ---
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        pw = request.form.get("password")
        if pw == os.getenv("ADMIN_PASSWORD", "ZiggeZaggeNAC1912!"):
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
    if request.args.get("action") == "add" and request.method == "POST":
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
@app.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
