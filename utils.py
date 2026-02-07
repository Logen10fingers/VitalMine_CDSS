from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import csv
from flask import Response, send_file
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load the secret .env file
load_dotenv()

# --- CONFIGURATION ---
# Read the key securely from the environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def ask_medical_ai(user_question, patient_context):
    """
    REAL AI MODE (Option B - Self-Repairing):
    Connects to Google Gemini. Automatically finds a working model
    (Flash or Pro) to prevent 404 Model Not Found errors.
    """
    try:
        # Safety Check: If key is missing, warn the user
        if not GEMINI_API_KEY:
            return "Configuration Error: API Key missing in .env file."

        genai.configure(api_key=GEMINI_API_KEY)

        # --- DYNAMIC MODEL DISCOVERY (The Fix) ---
        # Instead of guessing 'gemini-1.5-flash', we ask Google what is available.
        target_model = None
        available_models = []

        try:
            for m in genai.list_models():
                if "generateContent" in m.supported_generation_methods:
                    available_models.append(m.name)
                    # Priority 1: Flash (Fast & Free)
                    if "flash" in m.name:
                        target_model = m.name
                        break
                    # Priority 2: Standard Pro
                    elif "gemini-pro" in m.name and not target_model:
                        target_model = m.name
        except Exception:
            pass  # If listing fails, we fall back to default below

        # Fallback if discovery didn't pick one
        if not target_model:
            target_model = "models/gemini-pro"

        # Initialize the found model
        model = genai.GenerativeModel(target_model)

        # The Prompt (The Brain)
        prompt = f"""
        You are VitalBot, a helpful medical assistant for a hospital dashboard.
        
        Current Patient Context:
        - Name: {patient_context.get('name', 'Unknown')}
        - Temp: {patient_context.get('temp', 'N/A')} C
        - Heart Rate: {patient_context.get('hr', 'N/A')} bpm
        - Status: {patient_context.get('status', 'Unknown')}
        
        User Question: "{user_question}"
        
        Instructions:
        - Answer as a medical professional.
        - If the status is 'High' or 'Critical', warn the user immediately.
        - Keep the answer under 3 sentences.
        """

        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        # If internet fails or key is bad, return a fallback instead of crashing
        print(f"\n[AI ERROR LOG] {str(e)}\n")
        return "I am having trouble connecting to the AI server. Please check your internet or API Key."


def generate_pdf_report(entry):
    """
    Generates a PDF Clinical Report.
    """
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, 750, "VitalMine Hospital System")
    p.line(50, 725, 550, 725)

    p.setFont("Helvetica", 12)
    p.drawString(50, 680, f"Patient: {entry.name.upper()}")
    p.drawString(50, 660, f"Time: {entry.timestamp.strftime('%Y-%m-%d %H:%M')}")

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, 600, "Vitals Logged:")
    p.setFont("Helvetica", 12)
    p.drawString(70, 580, f"• Temperature: {entry.temp} C")
    p.drawString(70, 560, f"• Heart Rate: {entry.hr} bpm")
    p.drawString(70, 540, f"• Resp Rate: {entry.rr} /min")
    p.drawString(70, 520, f"• WBC Count: {entry.wbc}")

    p.rect(50, 430, 500, 80)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(60, 480, f"CURRENT STATUS: {entry.status.upper()}")

    # Handle advice text
    advice_text = entry.advice if entry.advice else "No specific advice logged."
    p.setFont("Helvetica-Oblique", 11)
    p.drawString(
        60, 450, f"AI Advice: {advice_text[:80]}..."
    )  # Truncate for PDF safety

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
    """
    Generates a CSV dump.
    """
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
