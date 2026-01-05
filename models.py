from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

# Initialize the database variable (we connect it to the app later)
db = SQLAlchemy()


# --- DATABASE TABLES ---
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
