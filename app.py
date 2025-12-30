from flask import Flask, render_template, request, redirect, url_for, Response
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

# --- LOAD THE AI BRAIN ---
try:
    model = joblib.load("sirs_model.pkl")
    print("AI Model Loaded Successfully!")
except:
    print("WARNING: Model not found. Run train_model.py first.")
    model = None


# --- DATABASE MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)


class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    temp = db.Column(db.Float, nullable=False)
    hr = db.Column(db.Integer, nullable=False)
    rr = db.Column(db.Integer, nullable=False)
    wbc = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# --- LOGIN LOADER ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --- ROUTES ---


@app.route("/")
@login_required
def home():
    all_entries = Entry.query.order_by(Entry.timestamp.desc()).all()

    total_patients = len(all_entries)
    high_risk_count = 0
    stable_count = 0

    history_data = []
    for e in all_entries:
        if e.status == "High":
            high_risk_count += 1
        else:
            stable_count += 1

        history_data.append(
            {
                "time": e.timestamp.strftime("%H:%M:%S"),
                "name": e.name,
                "vitals": f"{e.temp} / {e.hr} / {e.rr} / {e.wbc}",
                "status": e.status,
            }
        )

    stats = {"total": total_patients, "high": high_risk_count, "stable": stable_count}

    return render_template(
        "home.html", history=history_data, stats=stats, user=current_user
    )


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
    # 1. Get data
    temp = float(request.form.get("temperature"))
    hr = int(request.form.get("heart_rate"))
    rr = int(request.form.get("resp_rate"))
    wbc = float(request.form.get("wbc_count"))

    # 2. AI PREDICTION LOGIC
    if model:
        # Create a dataframe for the AI (it expects named columns)
        input_data = pd.DataFrame(
            [[temp, hr, rr, wbc]], columns=["temp", "hr", "rr", "wbc"]
        )

        # Ask the model: 1 = Sick, 0 = Healthy
        prediction = model.predict(input_data)[0]

        risk_status = "High" if prediction == 1 else "Stable"
    else:
        # Fallback if model fails
        risk_status = "Stable"

    # 3. Save result
    new_entry = Entry(
        name=request.form.get("name"),
        temp=temp,
        hr=hr,
        rr=rr,
        wbc=wbc,
        status=risk_status,
    )
    db.session.add(new_entry)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/export_data")
@login_required
def export_data():
    all_entries = Entry.query.order_by(Entry.timestamp.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "ID",
            "Timestamp",
            "Patient Name",
            "Temperature",
            "Heart Rate",
            "Resp Rate",
            "WBC Count",
            "Risk Status",
        ]
    )
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


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username="admin").first():
            admin = User(username="admin", password="password123")
            db.session.add(admin)
            db.session.commit()

    app.run(debug=True)
