# VitalMine - AI-Powered Clinical Decision Support System (CDSS)

**Master of Computer Applications (MCA) Semester-IV Major Project** **Student:** Om Tejaskumar Bhatt

## 🏥 Project Overview

VitalMine is a next-generation Clinical Decision Support System (CDSS) designed to bridge the gap between IoT Real-Time Monitoring and Generative AI Medical Analysis.

Unlike traditional hospital management systems that only store data, VitalMine actively monitors patient vitals using a Simulated IoT Wearable Layer. It processes this data through a Hybrid Intelligence Engine—combining deterministic clinical rules for immediate sepsis alerts with Google Gemini 1.5 (GenAI) for complex, context-aware medical consultation.

The system features strict Role-Based Access Control (RBAC), ensuring that Doctors, Nurses, Patients, and Admins interact with the system securely and appropriately.

---

## 🚀 Key Features

### 🫀 1. Real-Time Digital Twin (Visual Diagnostics)

- **Medical SVG Body Map:** Replaces static charts with a dynamic visual interface.
- **Visual Alerts:** The heart animates faster and turns RED during tachycardia; the head glows ORANGE during fever.
- **Live Telemetry:** Updates every 10 seconds via AJAX API.

### 🧠 2. Generative AI Medical Assistant (Gemini 1.5)

- **Context-Aware Chatbot:** The AI doesn't just answer general questions; it securely reads the specific patient's live chart from the database.
- **Active Monitoring:** Proactively warns the user of "High Risk" statuses before answering queries.
- **Self-Repairing Connection:** Automatically switches between available AI models (`gemini-1.5-flash` vs `gemini-pro`) to prevent downtime.

### 📡 3. IoT Sepsis Simulator

- **Real-Time Data Streaming:** Includes a standalone script (`wearable_device.py`) acting as a physical patient monitor.
- **Simulation Modes:**
  - _Mode 1:_ Healthy/Recovery (Normal vitals).
  - _Mode 2:_ Sepsis Onset (Spiking fever >39°C, Tachycardia >100bpm).
  - _Mode 3:_ Hypothermia/Shock (Low temp, rapid/weak pulse).

### 🔒 4. Enterprise-Grade Security & Registration

- **Dynamic Registration:** Secure sign-up portal capturing extended patient demographics (Age, Gender, Blood Group) and Staff Credentials (Emp ID, Department).
- **Role-Based Access Control (RBAC):**
  - **Admin:** System management and oversight.
  - **Doctors:** Full clinical oversight, PDF generation, AI consultation.
  - **Nurses:** Rapid vitals entry, ward monitoring, patient registration.
  - **Patients:** Read-only access to personal history and AI advice.
- **Secure Authentication:** Password hashing (`werkzeug.security`) and visibility toggles.

### 📄 5. Clinical Documentation

- **Automated PDF Reports:** Generates professional discharge summaries and status reports using ReportLab.
- **CSV Data Export:** Allows administrators to export ward data for external auditing.

---

## 🛠️ Tech Stack

- **Core Framework:** Python 3.10+, Flask
- **Artificial Intelligence:** Google Generative AI (Gemini 1.5 Flash), Scikit-Learn
- **IoT Simulation:** Python Threading & HTTP Requests
- **Database:** SQLite (SQLAlchemy ORM)
- **Reporting:** ReportLab (PDF), Pandas (CSV)
- **Frontend:** HTML5, CSS3, JavaScript (Bootstrap 5), Custom SVG Animations

---

## ⚙️ Installation & Setup

**1. Clone the Repository**

```bash
git clone [https://github.com/Logen10fingers/VitalMine_CDSS.git](https://github.com/Logen10fingers/VitalMine_CDSS.git)
cd VitalMine_CDSS

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate

pip install flask flask-sqlalchemy flask-login google-genai python-dotenv reportlab pandas scikit-learn werkzeug

GEMINI_API_KEY=your_google_api_key_here

# Run the training script to set up the ML model
python train_model.py

python app.py

python wearable_device.py

## 🔑 Login Credentials (Demo Accounts)

| Role | Username | Password | Capabilities |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `password123` | User Management, Data Export, Patient Directory |
| **Doctor** | `doctor` | `password123` | View Analytics, Chat with AI, Download PDFs |
| **Nurse** | `nurse` | `password123` | Add Vitals, View Dashboard, Register Patients |
| **Patient** | `patient_om` | `password123` | View Personal Stats, Ask AI Advice |

🔮 Future Roadmap
Integration of NEWS2 (National Early Warning Score) algorithms.

Voice-activated commands for hands-free sterile operation.

Mobile App integration using React Native/Flutter.

© 2026 VitalMine Project.
```
