from flask import Flask, render_template, request, redirect, url_for, Response, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from datetime import datetime
import csv
import io
import joblib
import pandas as pd

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///vitalmine.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "secret_key_vitalmine_2026"

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# --- LOAD AI MODEL ---
try:
    model = joblib.load("sirs_model.pkl")
except:
    model = None
    print("WARNING: sirs_model.pkl not found. AI features disabled.")


# --- DATABASE MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(
        db.String(20), nullable=False, default="patient"
    )  # Roles: admin, doctor, nurse, patient

    # Relationship: One User can have many Vitals Entries
    entries = db.relationship("Entry", backref="author", lazy=True)


class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=True
    )  # Link to User
    name = db.Column(db.String(100), nullable=False)
    temp = db.Column(db.Float, nullable=False)
    hr = db.Column(db.Integer, nullable=False)
    rr = db.Column(db.Integer, nullable=False)
    wbc = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    advice = db.Column(db.String(200), nullable=True)  # AI Advice Text
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --- ROUTES ---


@app.route("/")
@login_required
def home():
    # ROUTING LOGIC: If Patient, go to personal dashboard
    if current_user.role == "patient":
        return redirect(url_for("patient_dashboard"))

    # DOCTOR/ADMIN/NURSE DASHBOARD
    all_entries = Entry.query.order_by(Entry.timestamp.desc()).all()

    total = len(all_entries)
    high = sum(1 for e in all_entries if e.status == "High")
    stable = total - high
    stats = {"total": total, "high": high, "stable": stable}

    history_data = []
    for e in all_entries:
        history_data.append(
            {
                "time": e.timestamp.strftime("%H:%M:%S"),
                "name": e.name,
                "vitals": f"{e.temp} / {e.hr} / {e.rr} / {e.wbc}",
                "status": e.status,
                "advice": e.advice,
            }
        )

    return render_template("home.html", history=history_data, stats=stats)


@app.route("/patient_dashboard")
@login_required
def patient_dashboard():
    if current_user.role != "patient":
        return redirect(url_for("home"))

    # Fetch ONLY this patient's data
    my_entries = (
        Entry.query.filter_by(user_id=current_user.id)
        .order_by(Entry.timestamp.desc())
        .all()
    )

    # Most recent status for the "Current Status" card
    current_status = my_entries[0].status if my_entries else "Unknown"
    latest_advice = my_entries[0].advice if my_entries else "No data logged yet."

    return render_template(
        "patient_home.html",
        entries=my_entries,
        status=current_status,
        advice=latest_advice,
    )


@app.route("/patients")
@login_required
def patients_directory():
    # Security: Patients cannot see the directory
    if current_user.role == "patient":
        return redirect(url_for("patient_dashboard"))

    # 1. Get all users who are patients
    patients = User.query.filter_by(role="patient").all()

    # 2. For each patient, get their latest status
    patient_list = []
    for p in patients:
        # Get latest entry for this patient
        last_entry = (
            Entry.query.filter_by(user_id=p.id).order_by(Entry.timestamp.desc()).first()
        )
        status = last_entry.status if last_entry else "No Data"
        last_seen = last_entry.timestamp.strftime("%Y-%m-%d") if last_entry else "Never"

        patient_list.append(
            {
                "id": p.id,
                "username": p.username,
                "status": status,
                "last_seen": last_seen,
            }
        )

    return render_template("patients_list.html", patients=patient_list)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            # Redirect based on role
            if user.role == "patient":
                return redirect(url_for("patient_dashboard"))
            return redirect(url_for("home"))
        else:
            return render_template("login.html", error="Invalid Credentials")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/add_vitals", methods=["POST"])
@login_required
def add_vitals():
    if current_user.role == "doctor":
        return "Access Denied: Doctors cannot perform data entry."

    temp = float(request.form.get("temperature"))
    hr = int(request.form.get("heart_rate"))
    rr = int(request.form.get("resp_rate"))
    wbc = float(request.form.get("wbc_count"))

    # Auto-detect name: If patient, use their username. If nurse, use the form input.
    patient_name = (
        current_user.username
        if current_user.role == "patient"
        else request.form.get("name")
    )

    # AI PREDICTION
    if model:
        df = pd.DataFrame([[temp, hr, rr, wbc]], columns=["temp", "hr", "rr", "wbc"])
        is_sick = model.predict(df)[0]
        risk = "High" if is_sick == 1 else "Stable"
    else:
        # Fallback Logic
        score = 0
        if temp > 38.0 or temp < 36.0:
            score += 1
        if hr > 90:
            score += 1
        if rr > 20:
            score += 1
        if wbc > 12000 or wbc < 4000:
            score += 1
        risk = "High" if score >= 2 else "Stable"

    # THE ADVICE ENGINE (The "Smart" Part)
    if risk == "High":
        advice_text = (
            "CRITICAL ALERT: Sepsis signs detected. Proceed to Emergency immediately."
        )
    elif temp > 37.5:
        advice_text = (
            "Mild Fever detected. Stay hydrated and monitor temp every 4 hours."
        )
    else:
        advice_text = "Vitals are normal. Continue standard recovery protocol."

    # Save to DB
    new_entry = Entry(
        user_id=(
            current_user.id if current_user.role == "patient" else None
        ),  # Link to user
        name=patient_name,
        temp=temp,
        hr=hr,
        rr=rr,
        wbc=wbc,
        status=risk,
        advice=advice_text,
    )
    db.session.add(new_entry)
    db.session.commit()

    if current_user.role == "patient":
        return redirect(url_for("patient_dashboard"))
    return redirect(url_for("home"))


@app.route("/export_data")
@login_required
def export_data():
    if current_user.role == "nurse" or current_user.role == "patient":
        return "Access Denied"

    all_entries = Entry.query.order_by(Entry.timestamp.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "ID",
            "Timestamp",
            "Name",
            "Temp",
            "HR",
            "RR",
            "WBC",
            "Status",
            "Advice Issued",
        ]
    )
    for e in all_entries:
        writer.writerow(
            [e.id, e.timestamp, e.name, e.temp, e.hr, e.rr, e.wbc, e.status, e.advice]
        )
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=ward_report.csv"},
    )


# --- SETUP: Create Users ---
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        # Create standard roles
        if not User.query.filter_by(username="admin").first():
            db.session.add(User(username="admin", password="password123", role="admin"))
        if not User.query.filter_by(username="doctor").first():
            db.session.add(
                User(username="doctor", password="password123", role="doctor")
            )
        if not User.query.filter_by(username="nurse").first():
            db.session.add(User(username="nurse", password="password123", role="nurse"))

        # Create a Demo Patient
        if not User.query.filter_by(username="patient_om").first():
            db.session.add(
                User(username="patient_om", password="password123", role="patient")
            )

        db.session.commit()
        print("System Ready!")

    app.run(debug=True)
