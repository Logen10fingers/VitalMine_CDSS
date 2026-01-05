# VitalMine - AI-Powered Clinical Decision Support System (CDSS)

**Semester 8 Major Project | IMCA (AI Specialization)**
**Student:** Om Tejaskumar Bhatt

---

## 🏥 Project Overview

**VitalMine** is an intelligent healthcare platform designed to bridge the gap between hospital monitoring and post-discharge patient care. Unlike traditional SIRS calculators, VitalMine uses a **Hybrid Logic Engine** combining **Machine Learning (Logistic Regression)** with clinical rule-based validation to detect early signs of **Sepsis** and other critical conditions.

The system features a **Role-Based Access Control (RBAC)** architecture, separating data views for Doctors, Nurses, and Patients to ensure security and privacy compliance.

---

## 🚀 Key Features

### 🧠 1. Artificial Intelligence Core

- **Predictive Analytics:** Uses a pre-trained **Logistic Regression Model** (`sirs_model.pkl`) to evaluate sepsis risk in real-time.
- **Hybrid Decision Logic:** Overrides AI predictions with specific clinical rules to detect granular issues (e.g., _Hypothermia Risk_, _Tachycardia_, _High Fever_).

### 🔒 2. Enterprise Security (RBAC)

- **Doctor Mode:** Full analytics access, Patient Directory, and PDF Report generation. (Cannot alter raw data).
- **Nurse Mode:** Rapid data entry interface for high-volume wards. (Restricted from sensitive analytics).
- **Patient Mode:** A private, secure silo where patients can only view their own history.

### 📱 3. Telemedicine Patient Portal

- **Remote Monitoring:** Patients can log vitals from home.
- **AI Triage Bot:** Provides immediate, actionable medical advice (e.g., _"Take antipyretics"_ vs _"Proceed to Emergency"_).
- **Visual History:** Color-coded recovery timeline.

### 📄 4. Professional Reporting

- **PDF Discharge Summaries:** One-click generation of formal medical case files using `ReportLab`.
- **Data Export:** CSV export capabilities for hospital administration.

---

## 🛠️ Tech Stack

- **Backend:** Python 3.10+, Flask
- **AI & Data:** Scikit-Learn, Pandas, Joblib, NumPy
- **Database:** SQLite (SQLAlchemy ORM)
- **Reporting:** ReportLab (PDF), CSV module
- **Frontend:** Bootstrap 5, Jinja2, Chart.js, FontAwesome

---

## ⚙️ Installation & Setup

1.  **Clone the Repository:**

    ```powershell
    git clone [https://github.com/Logen10fingers/VitalMine_CDSS.git](https://github.com/Logen10fingers/VitalMine_CDSS.git)
    cd VitalMine_CDSS
    ```

2.  **Activate Virtual Environment:**

    ```powershell
    .\venv\Scripts\Activate
    ```

3.  **Install Dependencies (Updated):**

    ```powershell
    pip install flask flask-sqlalchemy flask-login scikit-learn pandas joblib reportlab
    ```

4.  **Train the AI Model (First Run Only):**

    ```powershell
    python train_model.py
    ```

5.  **Run the Server:**

    ```powershell
    python app.py
    ```

6.  **Access the Dashboard:**
    - Open Browser: `http://127.0.0.1:5000/`

---

## 🔑 Login Credentials (Demo Accounts)

| Role        | Username     | Password      | Capabilities                                     |
| :---------- | :----------- | :------------ | :----------------------------------------------- |
| **Doctor**  | `doctor`     | `password123` | View Analytics, Patient Directory, Download PDFs |
| **Nurse**   | `nurse`      | `password123` | Add Patient Vitals, Basic View                   |
| **Patient** | `patient_om` | `password123` | Self-Monitor, View Personal Advice, AI Triage    |
| **Admin**   | `admin`      | `password123` | System Maintenance                               |

---

## 📸 Screenshots

_(Add your screenshots here for the final submission to show off the UI)_
