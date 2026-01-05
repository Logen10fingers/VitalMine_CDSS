from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import csv
from flask import Response, send_file
import google.generativeai as genai

# --- CONFIGURATION ---
GEMINI_API_KEY = "AIzaSyAJF3cVxJj_G6zTJ9G_YeZnlfFQJ7fz2fM"


def ask_medical_ai(user_question, patient_context):
    """
    Sends vitals to AI. Uses 'Dynamic Model Discovery' to find a working brain.
    """
    try:
        genai.configure(api_key=GEMINI_API_KEY)

        # --- SMART FIX: AUTO-DETECT MODEL ---
        # 1. List all models your key has access to
        available_models = []
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                available_models.append(m.name)

        # 2. Pick the best one (Flash > Pro > 1.0)
        target_model = None
        preferred_order = [
            "models/gemini-1.5-flash",
            "models/gemini-1.5-flash-001",
            "models/gemini-1.5-pro",
            "models/gemini-pro",
            "models/gemini-1.0-pro",
        ]

        # Check if any preferred model exists in your available list
        for pref in preferred_order:
            if pref in available_models:
                target_model = pref
                break

        # Fallback: If none match, just grab the first one available
        if not target_model and available_models:
            target_model = available_models[0]

        if not target_model:
            return "System Error: No AI models found for this API Key."

        # 3. Initialize the found model
        model = genai.GenerativeModel(target_model)

        # 4. The Prompt
        prompt = f"""
        You are VitalBot, a compassionate medical assistant.
        
        Context:
        - Patient: {patient_context['name']}
        - Temp: {patient_context['temp']} C
        - HR: {patient_context['hr']} bpm
        - Status: {patient_context['status']}
        
        Question: "{user_question}"
        
        Answer nicely in max 2 sentences. If Status is High, warn them urgently.
        """

        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        print(f"\n[AI ERROR LOG] {str(e)}\n")
        return "I am having trouble connecting. Please try again in a moment."


def generate_pdf_report(entry):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, 750, "VitalMine Hospital System")
    p.line(50, 725, 550, 725)

    p.setFont("Helvetica", 12)
    p.drawString(50, 680, f"Patient: {entry.name.upper()}")
    p.drawString(50, 660, f"Time: {entry.timestamp.strftime('%Y-%m-%d %H:%M')}")

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, 600, "Vitals:")
    p.setFont("Helvetica", 12)
    p.drawString(70, 580, f"• Temp: {entry.temp} C")
    p.drawString(70, 560, f"• HR: {entry.hr} bpm")
    p.drawString(70, 540, f"• RR: {entry.rr} /min")
    p.drawString(70, 520, f"• WBC: {entry.wbc}")

    p.rect(50, 430, 500, 70)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(60, 480, f"STATUS: {entry.status.upper()}")
    p.setFont("Helvetica-Oblique", 12)
    p.drawString(60, 450, f"Advice: {entry.advice}")

    p.showPage()
    p.save()

    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"Report_{entry.id}.pdf",
        mimetype="application/pdf",
    )


def generate_csv_report(all_entries):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Timestamp", "Name", "Temp", "HR", "Status", "Advice"])
    for e in all_entries:
        writer.writerow([e.id, e.timestamp, e.name, e.temp, e.hr, e.status, e.advice])
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=ward_report.csv"},
    )
