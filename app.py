from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///vitalmine.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# --- DATABASE MODELS ---
class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    temp = db.Column(db.Float, nullable=False)
    hr = db.Column(db.Integer, nullable=False)
    rr = db.Column(db.Integer, nullable=False)
    wbc = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# --- THE BRAIN (Logic) ---
def check_sirs_risk(temp, hr, rr, wbc):
    score = 0
    if temp > 38.0 or temp < 36.0:
        score += 1
    if hr > 90:
        score += 1
    if rr > 20:
        score += 1
    if wbc > 12000 or wbc < 4000:
        score += 1

    return "High" if score >= 2 else "Stable"


# --- ROUTES ---
@app.route("/")
def home():
    # Fetch all entries from database to show in the table
    all_entries = Entry.query.order_by(Entry.timestamp.desc()).all()

    # Format data for the HTML
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
    return render_template("home.html", history=history_data)


@app.route("/add_vitals", methods=["POST"])
def add_vitals():
    # 1. Get data from the HTML form
    name = request.form.get("name")
    temp = float(request.form.get("temperature"))
    hr = int(request.form.get("heart_rate"))
    rr = int(request.form.get("resp_rate"))
    wbc = float(request.form.get("wbc_count"))

    # 2. Use the BRAIN to calculate risk
    risk_status = check_sirs_risk(temp, hr, rr, wbc)

    # 3. Save to Database
    new_entry = Entry(name=name, temp=temp, hr=hr, rr=rr, wbc=wbc, status=risk_status)
    db.session.add(new_entry)
    db.session.commit()

    # 4. Refresh the page
    return redirect(url_for("home"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
