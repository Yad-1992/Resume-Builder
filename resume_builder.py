import os
import streamlit as st
import requests
import base64
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch

# -------------------
# API Key Handling
# -------------------
API_KEY = None
if "GROQ_API_KEY" in st.secrets:
    API_KEY = st.secrets["GROQ_API_KEY"]
elif "GROQ_API_KEY" in os.environ:
    API_KEY = os.environ["GROQ_API_KEY"]

if not API_KEY:
    st.error("❌ GROQ_API_KEY not found. Please set it in Streamlit Secrets or as an environment variable.")
    st.stop()

# -------------------
# PDF Generator
# -------------------
def generate_stylish_pdf(name, email, phone, summary, skills, exp_title, exp_period, exp_points, education):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=50, bottomMargin=40)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleCenter", fontSize=18, leading=22, alignment=TA_CENTER,
                              spaceAfter=10, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="Header", fontSize=12, leading=14, alignment=TA_LEFT,
                              textColor=colors.HexColor("#0d47a1"), fontName="Helvetica-Bold",
                              spaceBefore=12, spaceAfter=6))
    styles.add(ParagraphStyle(name="Body", fontSize=10, leading=14, alignment=TA_LEFT, fontName="Helvetica"))
    styles.add(ParagraphStyle(name="BulletCustom", fontSize=10, leading=14, leftIndent=12, fontName="Helvetica"))

    content = []
    # Header
    content.append(Paragraph(name, styles["TitleCenter"]))
    content.append(Paragraph(f"{email} | {phone}", styles["Body"]))
    content.append(Spacer(1, 0.15 * inch))

    # Summary
    content.append(Paragraph("Professional Summary", styles["Header"]))
    content.append(Paragraph(summary, styles["Body"]))

    # Skills
    content.append(Paragraph("Core Skills", styles["Header"]))
    for s in skills.split(","):
        if s.strip():
            content.append(Paragraph(f"• {s.strip()}", styles["BulletCustom"]))

    # Experience
    content.append(Paragraph("Professional Experience", styles["Header"]))
    content.append(Paragraph(f"{exp_title} ({exp_period})", styles["Body"]))
    for p in exp_points.split("\n"):
        if p.strip():
            content.append(Paragraph(f"• {p.strip()}", styles["BulletCustom"]))

    # Education
    content.append(Paragraph("Education", styles["Header"]))
    content.append(Paragraph(education, styles["Body"]))

    doc.build(content)
    buffer.seek(0)
    return buffer

# -------------------
# Streamlit UI
# -------------------
st.set_page_config(page_title="AI Resume Builder", page_icon="📄", layout="centered")
st.markdown("## 📄 AI Resume Builder")
st.caption("Fill out your details → AI polishes it → Stylish PDF output")

with st.form("resume_form"):
    name = st.text_input("Full Name")
    email = st.text_input("Email")
    phone = st.text_input("Phone")
    summary = st.text_area("Professional Summary", height=80)
    skills = st.text_area("Core Skills (comma separated)", height=60)
    exp_title = st.text_input("Experience Title")
    exp_period = st.text_input("Experience Period")
    exp_points = st.text_area("Experience Bullets (one per line)", height=100)
    education = st.text_input("Education")
    submitted = st.form_submit_button("✨ Generate Resume")

# -------------------
# Resume Generation Logic
# -------------------
if submitted:
    if not name or not email:
        st.warning("⚠️ Please enter at least your name and email.")
    else:
        with st.spinner("Generating AI-enhanced resume..."):
            prompt = f"""
            Rewrite and polish this resume content in a professional, ATS-friendly style:
            Name: {name}
            Email: {email}
            Phone: {phone}
            Summary: {summary}
            Skills: {skills}
            Experience Title: {exp_title}
            Experience Period: {exp_period}
            Experience Points: {exp_points}
            Education: {education}
            """

            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }

            data = {
                "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                "messages": [{"role": "user", "content": prompt}]
            }

            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=data
            )

            if response.status_code == 200:
                result = response.json()
                ai_resume_text = result["choices"][0]["message"]["content"]

                # Generate PDF using cleaned data
                pdf_buffer = generate_stylish_pdf(name, email, phone, summary, skills, exp_title, exp_period, exp_points, education)

                # Base64 encode for new tab view
                pdf_base64 = base64.b64encode(pdf_buffer.read()).decode()
                pdf_buffer.seek(0)

                st.success("✅ Resume ready!")

                st.download_button("📥 Download PDF", data=pdf_buffer, file_name="resume.pdf", mime="application/pdf")

                # Open in new tab
                st.markdown(f'<a href="data:application/pdf;base64,{pdf_base64}" target="_blank">🔗 Open in New Tab</a>', unsafe_allow_html=True)
            else:
                st.error(f"❌ API Error: {response.status_code}")
                st.text(response.text)
