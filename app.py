from flask import Flask, render_template, request, redirect, url_for
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

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///vitalmine.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "secret_key_vitalmine_2026"  # Needed for security

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # Where to send unauthorized users


# --- DATABASE MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)  # In real life, hash this!


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
@login_required  # <--- This protects the dashboard!
def home():
    all_entries = Entry.query.order_by(Entry.timestamp.desc()).all()
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
    return render_template("home.html", history=history_data, user=current_user)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Check against database
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
    # LOGIC (The Brain)
    temp = float(request.form.get("temperature"))
    hr = int(request.form.get("heart_rate"))
    rr = int(request.form.get("resp_rate"))
    wbc = float(request.form.get("wbc_count"))

    score = 0
    if temp > 38.0 or temp < 36.0:
        score += 1
    if hr > 90:
        score += 1
    if rr > 20:
        score += 1
    if wbc > 12000 or wbc < 4000:
        score += 1
    risk_status = "High" if score >= 2 else "Stable"

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


# --- SETUP (Create Admin User) ---
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        # Create a default admin user if one doesn't exist
        if not User.query.filter_by(username="admin").first():
            admin = User(username="admin", password="password123")
            db.session.add(admin)
            db.session.commit()
            print("Admin User Created: admin / password123")

    app.run(debug=True)
