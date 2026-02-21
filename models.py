from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

# Initialize the database variable (we connect it to the app later)
db = SQLAlchemy()


# --- DATABASE TABLES ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    # NEW: Added email field for the Notification Service
    email = db.Column(db.String(120), unique=True, nullable=True)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="patient")

    # NEW (Phase 23): Extended Patient Demographics
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(20), nullable=True)

    # NEW (Phase 23): Realistic Hospital Fields
    blood_group = db.Column(db.String(10), nullable=True)
    contact = db.Column(db.String(20), nullable=True)
    emp_id = db.Column(db.String(50), nullable=True)
    department = db.Column(db.String(50), nullable=True)

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
