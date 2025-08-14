import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, abort
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, TextAreaField, IntegerField, DecimalField, FileField, HiddenField, DateField
from wtforms.validators import DataRequired, NumberRange, Email, Optional, Length
from werkzeug.utils import secure_filename
import sqlite3
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "data.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Configure categories here: (slug, label)
CATEGORIES = [
    ("bouw", "Bouw"),
    ("milieu", "Milieu"),
    ("handhaving", "Handhaving"),
    ("wonen", "Wonen & VvE"),
    ("sociaal", "Sociaal domein (Jeugd/Wmo)"),
    ("apv", "APV / Alcohol"),
    ("brandveiligheid", "Brandveiligheid"),
    ("ruimtelijk", "Ruimtelijke Ordening"),
    ("verkeer", "Verkeer & Openbare Ruimte"),
    ("kwaliteit", "Kwaliteit & Audit"),
]

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

csrf = CSRFProtect(app)

def slug_to_label(slug):
    for s, label in CATEGORIES:
        if s == slug:
            return label
    return slug

@contextmanager
def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
    finally:
        con.commit()
        con.close()

def init_db():
    with db() as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT,
            location TEXT,
            start_date TEXT,
            duration TEXT,
            hours INTEGER NOT NULL,
            rate REAL NOT NULL,
            description TEXT NOT NULL,
            categories TEXT,
            created_at TEXT NOT NULL
        );
        """)
        con.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            motivation TEXT,
            cv_filename TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
        );
        """)

class JobForm(FlaskForm):
    admin_password = HiddenField(validators=[DataRequired()])
    title = StringField("Titel van de opdracht", validators=[DataRequired(), Length(max=160)])
    company = StringField("Bedrijf/Organisatie", validators=[Optional(), Length(max=160)])
    location = StringField("Locatie", validators=[Optional(), Length(max=160)])
    start_date = DateField("Startdatum", validators=[Optional()], format="%Y-%m-%d")
    duration = StringField("Duur van de opdracht", validators=[Optional(), Length(max=120)])
    hours = IntegerField("Aantal uur", validators=[DataRequired(), NumberRange(min=1, max=10000)])
    rate = DecimalField("Tarief (€/uur)", validators=[DataRequired(), NumberRange(min=0)], places=2)
    description = TextAreaField("Omschrijving", validators=[DataRequired()])
    # categories via checkboxes (handmatig)

class ApplicationForm(FlaskForm):
    name = StringField("Naam", validators=[DataRequired(), Length(max=120)])
    email = StringField("E-mail", validators=[DataRequired(), Email()])
    phone = StringField("Telefoon (optioneel)", validators=[Optional(), Length(max=50)])
    motivation = TextAreaField("Korte toelichting (optioneel)", validators=[Optional()])
    cv = FileField("Upload je CV (PDF, max 5MB)", validators=[Optional()])

@app.route("/")
def index():
    selected = request.args.getlist("cat")
    with db() as con:
        jobs = con.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
    if selected:
        sel_set = set(selected)
        filtered = []
        for j in jobs:
            cats = set((j["categories"] or "").split(",")) if j["categories"] else set()
            if cats & sel_set:
                filtered.append(j)
        jobs = filtered
    return render_template("index.html", jobs=jobs, categories=CATEGORIES, selected=selected)

@app.route("/job/<int:job_id>")
def job_detail(job_id):
    with db() as con:
        job = con.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not job:
        abort(404)
    form = ApplicationForm()
    job_categories = [(c, slug_to_label(c)) for c in (job["categories"] or "").split(",") if c]
    return render_template("job_detail.html", job=job, form=form, job_categories=job_categories)

@app.route("/apply/<int:job_id>", methods=["POST"])
def apply(job_id):
    form = ApplicationForm()
    with db() as con:
        job = con.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not job:
            abort(404)
    if form.validate_on_submit():
        filename = None
        file = request.files.get("cv")
        if file and file.filename:
            fname = secure_filename(file.filename)
            if not fname.lower().endswith(".pdf"):
                flash("Alleen PDF-bestanden zijn toegestaan.", "error")
                return redirect(url_for("job_detail", job_id=job_id))
            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(0)
            if size > 5 * 1024 * 1024:
                flash("Bestand is te groot (max 5MB).", "error")
                return redirect(url_for("job_detail", job_id=job_id))
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            filename = f"{timestamp}_{fname}"
            file.save(os.path.join(UPLOAD_DIR, filename))

        with db() as con:
            con.execute(
                """
                INSERT INTO applications (job_id, name, email, phone, motivation, cv_filename, created_at)
                VALUES (?,?,?,?,?,?,?)
                """,
                (
                    job_id,
                    form.name.data.strip(),
                    form.email.data.strip(),
                    (form.phone.data or "").strip(),
                    (form.motivation.data or "").strip(),
                    filename,
                    datetime.utcnow().isoformat(),
                ),
            )
        flash("Bedankt! Je reactie is ontvangen.", "success")
        return redirect(url_for("job_detail", job_id=job_id))
    else:
        for field, errors in form.errors.items():
            for e in errors:
                flash(f"{field}: {e}", "error")
        return redirect(url_for("job_detail", job_id=job_id))

@app.route("/admin")
def admin():
    pw = request.args.get("pw", "")
    if pw != ADMIN_PASSWORD:
        return render_template("admin_login.html")
    with db() as con:
        jobs = con.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
        apps = con.execute(
            """
            SELECT a.*, j.title as job_title FROM applications a
            JOIN jobs j ON j.id = a.job_id
            ORDER BY a.created_at DESC
            """
        ).fetchall()
    return render_template("admin.html", jobs=jobs, apps=apps, pw=pw)

@app.route("/admin/new", methods=["GET", "POST"])
def admin_new():
    pw = request.args.get("pw", "")
    form = JobForm()
    if request.method == "GET":
        form.admin_password.data = pw
        return render_template("admin_new.html", form=form, pw=pw, categories=CATEGORIES)
    selected_categories = request.form.getlist("categories")
    categories_value = ",".join(selected_categories)
    if form.validate_on_submit() and form.admin_password.data == ADMIN_PASSWORD:
        with db() as con:
            con.execute(
                """
                INSERT INTO jobs (title, company, location, start_date, duration, hours, rate, description, categories, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)
                """
                ,
                (
                    form.title.data.strip(),
                    (form.company.data or "").strip(),
                    (form.location.data or "").strip(),
                    form.start_date.data.isoformat() if form.start_date.data else None,
                    (form.duration.data or "").strip(),
                    int(form.hours.data),
                    float(form.rate.data),
                    form.description.data.strip(),
                    categories_value,
                    datetime.utcnow().isoformat(),
                ),
            )
        flash("Opdracht geplaatst.", "success")
        return redirect(url_for("admin", pw=pw))
    else:
        if form.admin_password.data != ADMIN_PASSWORD:
            flash("Ongeldige admin inlog.", "error")
        return render_template("admin_new.html", form=form, pw=pw, categories=CATEGORIES)

@app.route("/admin/delete/<int:job_id>", methods=["POST"])
def admin_delete(job_id):
    pw = request.args.get("pw", "")
    if pw != ADMIN_PASSWORD:
        abort(403)
    with db() as con:
        con.execute("DELETE FROM jobs WHERE id=?", (job_id,))
    flash("Opdracht verwijderd.", "success")
    return redirect(url_for("admin", pw=pw))

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=True)

@app.route("/over-ons")
def over_ons():
    return render_template("over_ons.html")

@app.cli.command("init-db")
def initdb_command():
    init_db()
    print("Database initialized.")

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=True)
