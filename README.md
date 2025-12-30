# VitalMine - Clinical Decision Support System (CDSS)

**Semester 8 Major Project | IMCA**
**Student:** Om Tejaskumar Bhatt

## Project Overview

VitalMine is a web-based automated alert system designed to detect early signs of Sepsis using the SIRS criteria. It features real-time dashboards, risk stratification logic, and automated reporting.

## Tech Stack

- **Backend:** Python 3.10+, Flask
- **Database:** SQLite (SQLAlchemy ORM)
- **Frontend:** Bootstrap 5, Jinja2, Chart.js
- **Auth:** Flask-Login

## Installation & Setup

1.  **Activate Virtual Environment:**
    ```powershell
    .\venv\Scripts\Activate
    ```
2.  **Install Dependencies:**
    ```powershell
    pip install flask flask-sqlalchemy flask-login
    ```
3.  **Run the Server:**
    ```powershell
    python app.py
    ```
4.  **Access:**
    - URL: http://127.0.0.1:5000/
    - **Admin Login:** `admin`
    - **Password:** `password123`

## Features

- **SIRS Logic Engine:** Automatically calculates sepsis risk based on 4 vital parameters.
- **Real-Time Analytics:** Live doughnut chart showing Ward Status (Stable vs. Critical).
- **Reporting:** One-click CSV export for medical records (`ward_report.csv`).
- **Security:** Role-based access control with secure login.
