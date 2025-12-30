from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize the Flask application
app = Flask(__name__)

# --- CONFIGURATION ---
# This tells Flask to create a file named 'vitalmine.db' in your folder to store data
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///vitalmine.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the Database
db = SQLAlchemy(app)

# --- DATABASE MODELS (The Structure) ---


class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    admission_date = db.Column(db.DateTime, default=datetime.utcnow)


class Vitals(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    heart_rate = db.Column(db.Integer, nullable=False)
    resp_rate = db.Column(db.Integer, nullable=False)
    wbc_count = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# --- ROUTES ---
@app.route("/")
def home():
    return "VitalMine System Running - Phase 3 (Database Connected)"


# --- APP STARTUP ---
if __name__ == "__main__":
    # This creates the database file if it doesn't exist
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")

    app.run(debug=True)
