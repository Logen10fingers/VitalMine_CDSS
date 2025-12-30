from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    Response,
    send_file,
)
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
import joblib
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///vitalmine.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "secret_key_vitalmine_2026"

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

try:
    model = joblib.load("sirs_model.pkl")
except:
    model = None


# --- DATABASE MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="patient")
    entries = db.relationship("Entry", backref="author", lazy=True)


class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    temp = db.Column(db.Float, nullable=False)
    hr = db.Column(db.Integer, nullable=False)
    rr = db.Column(db.Integer, nullable=False)
    wbc = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    advice = db.Column(db.String(200), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


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
        return "Access Denied"

    try:
        temp = float(request.form.get("temperature"))
        hr = int(request.form.get("heart_rate"))
        rr = int(request.form.get("resp_rate"))
        wbc = float(request.form.get("wbc_count"))
    except ValueError:
        return "Invalid Data", 400

    # --- ROBUST NAME LOGIC (FIX FOR CRASH) ---
    if current_user.role == "patient":
        patient_name = current_user.username
        user_id_save = current_user.id
    else:
        patient_name = request.form.get("name")
        user_id_save = None

    # Safety Fallback: If logic fails, force a name
    if not patient_name:
        patient_name = current_user.username

    # 1. AI PREDICTION
    ai_risk = "Stable"
    if model:
        df = pd.DataFrame([[temp, hr, rr, wbc]], columns=["temp", "hr", "rr", "wbc"])
        is_sick = model.predict(df)[0]
        if is_sick == 1:
            ai_risk = "High"

    # 2. DECISION LOGIC
    status = "Stable"
    advice_text = "Vitals are normal. Continue standard care."

    if ai_risk == "High":
        status = "High"
        advice_text = (
            "CRITICAL: Sepsis signs detected. Proceed to Emergency immediately."
        )
    elif temp > 38.0:
        status = "Warning"
        advice_text = "High Fever detected. Take antipyretics and hydrate."
    elif temp < 36.0:
        status = "Warning"
        advice_text = "Hypothermia Risk. Keep patient warm."
    elif hr > 100:
        status = "Warning"
        advice_text = "Tachycardia (High Heart Rate). Rest and re-check."
    elif rr > 22:
        status = "Warning"
        advice_text = "Hyperventilation detected. Monitor breathing."
    else:
        status = "Stable"

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

    if current_user.role == "patient":
        return redirect(url_for("patient_dashboard"))
    return redirect(url_for("home"))


@app.route("/generate_pdf/<int:entry_id>")
@login_required
def generate_pdf(entry_id):
    entry = Entry.query.get_or_404(entry_id)
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, 750, "VitalMine Hospital System")
    p.setFont("Helvetica", 12)
    p.drawString(50, 735, "Clinical Decision Support Report")
    p.line(50, 725, 550, 725)

    p.drawString(50, 680, f"Patient Name: {entry.name.upper()}")
    p.drawString(50, 660, f"Date/Time: {entry.timestamp.strftime('%Y-%m-%d %H:%M')}")
    p.drawString(50, 640, f"Report ID: #{entry.id}")

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, 600, "Clinical Vitals:")
    p.setFont("Helvetica", 12)
    p.drawString(70, 580, f"• Temperature: {entry.temp} °C")
    p.drawString(70, 560, f"• Heart Rate: {entry.hr} bpm")
    p.drawString(70, 540, f"• Respiratory Rate: {entry.rr} /min")
    p.drawString(70, 520, f"• WBC Count: {entry.wbc} /mcL")

    p.rect(50, 430, 500, 70)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(60, 480, "AI RISK ASSESSMENT:")

    if entry.status == "High":
        p.setFillColorRGB(1, 0, 0)
    elif entry.status == "Warning":
        p.setFillColorRGB(1, 0.5, 0)
    else:
        p.setFillColorRGB(0, 0.5, 0)

    p.drawString(230, 480, entry.status.upper())
    p.setFillColorRGB(0, 0, 0)

    p.setFont("Helvetica-Oblique", 12)
    p.drawString(60, 450, f"Recommendation: {entry.advice}")

    p.setFont("Helvetica", 10)
    p.drawString(
        50,
        100,
        "This report was generated by VitalMine AI. Please consult a physician.",
    )
    p.drawString(50, 50, "Signature: __________________________")

    p.showPage()
    p.save()

    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"Report_{entry.name}_{entry.id}.pdf",
        mimetype="application/pdf",
    )


@app.route("/export_data")
@login_required
def export_data():
    if current_user.role == "nurse" or current_user.role == "patient":
        return "Access Denied"
    all_entries = Entry.query.order_by(Entry.timestamp.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["ID", "Timestamp", "Name", "Temp", "HR", "RR", "WBC", "Status", "Advice"]
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


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        # Ensure all roles exist
        if not User.query.filter_by(username="admin").first():
            db.session.add(User(username="admin", password="password123", role="admin"))
        if not User.query.filter_by(username="doctor").first():
            db.session.add(
                User(username="doctor", password="password123", role="doctor")
            )
        if not User.query.filter_by(username="nurse").first():
            db.session.add(User(username="nurse", password="password123", role="nurse"))
        if not User.query.filter_by(username="patient_om").first():
            db.session.add(
                User(username="patient_om", password="password123", role="patient")
            )
        db.session.commit()

    app.run(debug=True)
