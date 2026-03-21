import io
import os
import pandas as pd
from flask import send_file
from dotenv import load_dotenv

# --- NEW GOOGLE GENAI SDK ---
from google import genai
from google.genai import types

# --- ADVANCED PDF IMPORTS ---
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def ask_medical_ai(user_question, patient_context):
    try:
        if not GEMINI_API_KEY:
            return "Configuration Error: API Key missing in .env file."

        # Initialize the NEW SDK client
        client = genai.Client(api_key=GEMINI_API_KEY)

        prompt = f"""
        You are VitalBot, a helpful medical assistant for a hospital dashboard.
        
        Current Patient Context:
        - Name: {patient_context.get('name', 'Unknown')}
        - Temp: {patient_context.get('temp', 'N/A')} C
        - Heart Rate: {patient_context.get('hr', 'N/A')} bpm
        - Resp Rate: {patient_context.get('rr', 'N/A')} breaths/min
        - Blood Pressure: {patient_context.get('sys_bp', 'N/A')}/{patient_context.get('dia_bp', 'N/A')} mmHg
        - Status: {patient_context.get('status', 'Unknown')}
        
        User Question: "{user_question}"
        
        Instructions:
        - Answer as a medical professional.
        - If the status is 'High' or 'Critical', warn the user immediately.
        - Keep the answer under 3 sentences.
        - You are an AI, so remind the user to consult a human doctor if they ask for a formal diagnosis.
        """

        # Turn off censorship using the NEW SDK formatting
        config = types.GenerateContentConfig(
            safety_settings=[
                types.SafetySetting(
                    category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"
                ),
            ]
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt, config=config
        )
        return response.text

    except Exception as e:
        print("\n" + "=" * 50)
        print("🚨 CRITICAL AI ERROR DETECTED BY GOOGLE:")
        print(str(e))
        print("=" * 50 + "\n")
        return "I am having trouble connecting to the AI server. Please check your internet or API Key."


def generate_pdf_report(entry):
    """
    Generates a highly structured, enterprise-grade Clinical EHR Report.
    """
    buffer = io.BytesIO()

    # Setup Document Layout
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=60,
        bottomMargin=40,
    )
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        textColor=colors.HexColor("#064e3b"),
        spaceAfter=10,
    )
    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=6,
        spaceBefore=15,
    )
    normal_style = styles["Normal"]

    status_color = colors.HexColor("#10b981")  # Default Green
    if entry.status in ["High", "Critical"]:
        status_color = colors.HexColor("#ef4444")  # Red
    elif entry.status == "Warning":
        status_color = colors.HexColor("#f59e0b")  # Yellow/Orange

    badge_style = ParagraphStyle(
        "Badge",
        fontName="Helvetica-Bold",
        fontSize=14,
        textColor=colors.white,
        alignment=1,
    )
    badge_p = Paragraph(f"{entry.status.upper()}", badge_style)

    header_data = [
        [Paragraph("<b>CLINICAL TELEMETRY REPORT</b>", title_style), badge_p]
    ]
    header_table = Table(header_data, colWidths=[400, 100])
    header_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (0, 0), "LEFT"),
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (1, 0), (1, 0), status_color),
                ("TOPPADDING", (1, 0), (1, 0), 8),
                ("BOTTOMPADDING", (1, 0), (1, 0), 8),
            ]
        )
    )
    elements.append(header_table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("PATIENT DEMOGRAPHICS & META", heading_style))
    meta_data = [
        [
            "Report ID:",
            f"VTM-{entry.id}-2026",
            "Inspection Date:",
            entry.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        ],
        ["Patient ID:", entry.name.upper(), "Inspected By:", "VitalMine CDSS Engine"],
    ]
    meta_table = Table(meta_data, colWidths=[90, 160, 100, 140])
    meta_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#334155")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elements.append(meta_table)
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("BIOMETRIC EVIDENCE", heading_style))
    vitals_data = [
        ["PARAMETER", "VALUE", "UNIT", "REFERENCE RANGE"],
        ["Core Temperature", str(entry.temp), "°C", "36.1 - 37.2 °C"],
        ["Heart Rate", str(entry.hr), "bpm", "60 - 100 bpm"],
        ["Respiratory Rate", str(entry.rr), "breaths/min", "12 - 20 breaths/min"],
        ["Blood Pressure", f"{entry.sys_bp}/{entry.dia_bp}", "mmHg", "120/80 mmHg"],
    ]
    vitals_table = Table(vitals_data, colWidths=[130, 100, 100, 160])
    vitals_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#064e3b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 1), (2, -1), "CENTER"),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#064e3b")),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elements.append(vitals_table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("AI CLASSIFICATION & ADVICE", heading_style))
    advice_data = [
        ["RISK LEVEL", "CLINICAL ADVICE"],
        [entry.status.upper(), Paragraph(entry.advice, normal_style)],
    ]
    advice_table = Table(advice_data, colWidths=[110, 380])
    advice_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3b82f6")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TEXTCOLOR", (0, 1), (0, 1), status_color),
                ("FONTNAME", (0, 1), (0, 1), "Helvetica-Bold"),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#3b82f6")),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elements.append(advice_table)

    def add_bg_and_footer(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor("#064e3b"))
        canvas.rect(0, letter[1] - 40, letter[0], 40, fill=True, stroke=False)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 14)
        canvas.drawCentredString(
            letter[0] / 2.0, letter[1] - 25, "VITALMINE CDSS - EHR TELEMETRY LOG"
        )

        canvas.setFillColor(colors.gray)
        canvas.setFont("Helvetica", 9)
        canvas.drawString(
            40,
            30,
            "© 2026 VitalMine Clinical Decision Support System. Secure EHR Export.",
        )

        canvas.setStrokeColor(colors.HexColor("#10b981"))
        canvas.setLineWidth(2.5)
        canvas.circle(letter[0] - 80, 60, 35)
        canvas.setFillColor(colors.HexColor("#10b981"))
        canvas.setFont("Helvetica-Bold", 11)
        canvas.translate(letter[0] - 80, 60)
        canvas.rotate(25)
        canvas.drawCentredString(0, -4, "VERIFIED")

        canvas.restoreState()

    doc.build(elements, onFirstPage=add_bg_and_footer, onLaterPages=add_bg_and_footer)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"EHR_{entry.name}_{entry.id}.pdf",
        mimetype="application/pdf",
    )


def generate_excel_report(all_entries):
    """
    Generates a color-coded, formatted Excel (.xlsx) file instead of a boring CSV.
    """
    output = io.BytesIO()

    data = []
    for e in all_entries:
        data.append(
            {
                "Log ID": e.id,
                "Timestamp": e.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "Patient ID": e.name,
                "Temp (°C)": e.temp,
                "Heart Rate (bpm)": e.hr,
                "Resp Rate (bpm)": e.rr,
                "Blood Pressure": f"{e.sys_bp}/{e.dia_bp}",
                "AI Risk Status": e.status,
                "Clinical Advice": e.advice,
            }
        )
    df = pd.DataFrame(data)

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Ward Telemetry")
        workbook = writer.book
        worksheet = writer.sheets["Ward Telemetry"]

        header_fmt = workbook.add_format(
            {"bold": True, "bg_color": "#064e3b", "font_color": "white", "border": 1}
        )
        critical_fmt = workbook.add_format(
            {"bg_color": "#fca5a5", "font_color": "#991b1b"}
        )
        warning_fmt = workbook.add_format(
            {"bg_color": "#fef08a", "font_color": "#9a3412"}
        )
        stable_fmt = workbook.add_format(
            {"bg_color": "#d1fae5", "font_color": "#065f46"}
        )

        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_fmt)
            worksheet.set_column(col_num, col_num, 20)

        for row_num in range(1, len(df) + 1):
            status = df.iloc[row_num - 1]["AI Risk Status"]
            if status in ["High", "Critical"]:
                worksheet.set_row(row_num, None, critical_fmt)
            elif status == "Warning":
                worksheet.set_row(row_num, None, warning_fmt)
            else:
                worksheet.set_row(row_num, None, stable_fmt)

    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name="vitalmine_ward_report.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
