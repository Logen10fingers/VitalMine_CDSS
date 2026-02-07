from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import (
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user,
)
import joblib
import pandas as pd

# --- MVC IMPORTS ---
from models import db, User, Entry

# Added ask_medical_ai to imports
from utils import generate_pdf_report, generate_csv_report, ask_medical_ai

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///vitalmine.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "secret_key_vitalmine_2026"

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

try:
    model = joblib.load("sirs_model.pkl")
except:
    model = None


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# --- ROUTES ---


@app.route("/")
@login_required
def home():
    if current_user.role == "patient":
        return redirect(url_for("patient_dashboard"))

    all_entries = Entry.query.order_by(Entry.timestamp.desc()).all()
    stats = {
        "total": len(all_entries),
        "high": sum(1 for e in all_entries if e.status == "High"),
        "stable": sum(1 for e in all_entries if e.status != "High"),
    }

    history_data = []
    for e in all_entries:
        history_data.append(
            {
                "id": e.id,
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
    my_entries = (
        Entry.query.filter_by(user_id=current_user.id)
        .order_by(Entry.timestamp.desc())
        .all()
    )
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
    if current_user.role == "patient":
        return redirect(url_for("patient_dashboard"))
    patients = User.query.filter_by(role="patient").all()
    patient_list = []
    for p in patients:
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
            return redirect(
                url_for("patient_dashboard" if user.role == "patient" else "home")
            )
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
        return "Access Denied"

    try:
        temp = float(request.form.get("temperature"))
        hr = int(request.form.get("heart_rate"))
        rr = int(request.form.get("resp_rate"))
        wbc = float(request.form.get("wbc_count"))
    except ValueError:
        return "Invalid Data", 400

    if current_user.role == "patient":
        patient_name = current_user.username
        user_id_save = current_user.id
    else:
        patient_name = request.form.get("name") or current_user.username
        user_id_save = None

    ai_risk = "Stable"
    if model:
        df = pd.DataFrame([[temp, hr, rr, wbc]], columns=["temp", "hr", "rr", "wbc"])
        if model.predict(df)[0] == 1:
            ai_risk = "High"

    status = "Stable"
    advice_text = "Vitals are normal. Continue standard care."

    if ai_risk == "High":
        status = "High"
        advice_text = (
            "CRITICAL: Sepsis signs detected. Proceed to Emergency immediately."
        )
        print(f"\n[SERVER LOG] 📧 SMTP WORKER: Alert sent for {patient_name}")
        flash(f"🚨 EMERGENCY PROTOCOL: Alert sent for {patient_name}.", "danger")
    elif temp > 38.0:
        status = "Warning"
        advice_text = "High Fever detected. Take antipyretics."
        flash(f"⚠️ High Fever Warning for {patient_name}.", "warning")
    elif temp < 36.0:
        status = "Warning"
        advice_text = "Hypothermia Risk. Keep warm."
        flash(f"⚠️ Hypothermia Warning for {patient_name}.", "warning")
    elif hr > 100:
        status = "Warning"
        advice_text = "Tachycardia. Rest and re-check."
        flash(f"⚠️ Tachycardia Warning for {patient_name}.", "warning")
    elif rr > 22:
        status = "Warning"
        advice_text = "Hyperventilation. Monitor breathing."
        flash(f"⚠️ Respiratory Warning for {patient_name}.", "warning")
    else:
        flash(f"✅ Vitals logged for {patient_name}.", "success")

    new_entry = Entry(
        user_id=user_id_save,
        name=patient_name,
        temp=temp,
        hr=hr,
        rr=rr,
        wbc=wbc,
        status=status,
        advice=advice_text,
    )
    db.session.add(new_entry)
    db.session.commit()

    return redirect(
        url_for("patient_dashboard" if current_user.role == "patient" else "home")
    )


@app.route("/generate_pdf/<int:entry_id>")
@login_required
def generate_pdf(entry_id):
    entry = db.session.get(Entry, entry_id)
    if not entry:
        return "Not Found", 404
    return generate_pdf_report(entry)


@app.route("/export_data")
@login_required
def export_data():
    if current_user.role in ["nurse", "patient"]:
        return "Access Denied"
    return generate_csv_report(Entry.query.order_by(Entry.timestamp.desc()).all())


# --- PHASE 19: CHATBOT ROUTE ---
@app.route("/chat_with_ai", methods=["POST"])
@login_required
def chat_with_ai():
    user_question = request.json.get("question")

    # Get the latest patient data from DB
    last_entry = (
        Entry.query.filter_by(user_id=current_user.id)
        .order_by(Entry.timestamp.desc())
        .first()
    )

    if last_entry:
        context = {
            "name": current_user.username,
            "temp": last_entry.temp,
            "hr": last_entry.hr,
            "status": last_entry.status,
        }
    else:
        context = {"name": "Unknown", "temp": "N/A", "hr": "N/A", "status": "Unknown"}

    # Ask the Brain (in utils.py)
    ai_response = ask_medical_ai(user_question, context)

    return {"response": ai_response}


# --- PHASE 21: DIGITAL TWIN API ---
@app.route("/api/patient_history/<int:user_id>")
@login_required
def get_patient_history(user_id):
    """
    Fetches vitals for the Digital Twin & Live Graph.
    Includes Respiration Rate (RR) for lung visualization.
    """
    # 1. Get last 20 entries for this patient
    entries = (
        Entry.query.filter_by(user_id=user_id)
        .order_by(Entry.timestamp.desc())
        .limit(20)
        .all()
    )
    entries = entries[::-1]  # Reverse to Chronological order

    if not entries:
        return jsonify({"error": "No data"})

    latest = entries[-1]

    return jsonify(
        {
            "timestamps": [e.timestamp.strftime("%H:%M:%S") for e in entries],
            "heart_rates": [e.hr for e in entries],
            "temps": [e.temp for e in entries],
            "respiration_rates": [e.rr for e in entries],  # Added for Lungs
            "latest_vitals": {
                "hr": latest.hr,
                "temp": latest.temp,
                "rr": latest.rr,
                "status": latest.status,
            },
        }
    )


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username="admin").first():
            db.session.add(User(username="admin", password="password123", role="admin"))
            db.session.add(
                User(username="doctor", password="password123", role="doctor")
            )
            db.session.add(User(username="nurse", password="password123", role="nurse"))
            db.session.add(
                User(username="patient_om", password="password123", role="patient")
            )
            db.session.commit()

    app.run(debug=True)
