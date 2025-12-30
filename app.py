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

# --- LOAD AI ---
try:
    model = joblib.load("sirs_model.pkl")
except:
    model = None


# --- DATABASE MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="nurse")  # NEW: Role Column


class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    temp = db.Column(db.Float, nullable=False)
    hr = db.Column(db.Integer, nullable=False)
    rr = db.Column(db.Integer, nullable=False)
    wbc = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --- ROUTES ---
@app.route("/")
@login_required
def home():
    all_entries = Entry.query.order_by(Entry.timestamp.desc()).all()

    # Calculate stats for Doctor/Admin
    total = len(all_entries)
    high = sum(1 for e in all_entries if e.status == "High")
    stable = total - high

    stats = {"total": total, "high": high, "stable": stable}

    # Pass 'history' and 'stats' to frontend
    # We create the history list manually to format dates nicely
    history_data = []
    for e in all_entries:
        history_data.append(
            {
                "time": e.timestamp.strftime("%H:%M:%S"),
                "name": e.name,
                "vitals": f"{e.temp} / {e.hr} / {e.rr} / {e.wbc}",
                "status": e.status,
            }
        )

    return render_template("home.html", history=history_data, stats=stats)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
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
    # SECURITY CHECK: Doctors cannot add vitals
    if current_user.role == "doctor":
        return "Access Denied: Doctors cannot perform data entry."

    temp = float(request.form.get("temperature"))
    hr = int(request.form.get("heart_rate"))
    rr = int(request.form.get("resp_rate"))
    wbc = float(request.form.get("wbc_count"))

    # AI PREDICTION
    if model:
        df = pd.DataFrame([[temp, hr, rr, wbc]], columns=["temp", "hr", "rr", "wbc"])
        risk = "High" if model.predict(df)[0] == 1 else "Stable"
    else:
        risk = "Stable"

    new_entry = Entry(
        name=request.form.get("name"), temp=temp, hr=hr, rr=rr, wbc=wbc, status=risk
    )
    db.session.add(new_entry)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/export_data")
@login_required
def export_data():
    # SECURITY CHECK: Nurses cannot export data
    if current_user.role == "nurse":
        return "Access Denied: Nurses cannot export confidential reports."

    all_entries = Entry.query.order_by(Entry.timestamp.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Timestamp", "Name", "Temp", "HR", "RR", "WBC", "Status"])
    for e in all_entries:
        writer.writerow(
            [e.id, e.timestamp, e.name, e.temp, e.hr, e.rr, e.wbc, e.status]
        )
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=ward_report.csv"},
    )


# --- SETUP: Create the 3 Roles ---
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        # 1. Admin
        if not User.query.filter_by(username="admin").first():
            db.session.add(User(username="admin", password="password123", role="admin"))
        # 2. Doctor (Analyst)
        if not User.query.filter_by(username="doctor").first():
            db.session.add(
                User(username="doctor", password="password123", role="doctor")
            )
        # 3. Nurse (Data Entry)
        if not User.query.filter_by(username="nurse").first():
            db.session.add(User(username="nurse", password="password123", role="nurse"))

        db.session.commit()
        print("System Ready: Admin, Doctor, and Nurse accounts active.")

    app.run(debug=True)
