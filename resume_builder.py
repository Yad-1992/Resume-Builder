import os
import re
import io
import base64
import streamlit as st
import requests
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
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
# PDF Generator from AI Text (with cleanup)
# -------------------
def generate_pdf_from_ai(ai_text):
    # --- Clean AI text ---
    ai_text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", ai_text)  # Remove markdown links
    ai_text = ai_text.replace("mailto:", "")                    # Remove 'mailto:'
    ai_text = re.sub(r"\*\*(.*?)\*\*", r"\1", ai_text)           # Remove bold markdown
    ai_text = re.sub(r"\*(.*?)\*", r"\1", ai_text)               # Remove italic markdown
    ai_text = re.sub(r"_(.*?)_", r"\1", ai_text)                 # Remove underline markdown

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=50, bottomMargin=40)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="BodyCustom", fontSize=10, leading=14, alignment=TA_LEFT, fontName="Helvetica"))

    content = []
    for line in ai_text.split("\n"):
        line = line.strip()
        if line:
            if line.endswith(":") or line.isupper():
                # Section Header style
                content.append(Paragraph(line, ParagraphStyle(
                    name="Header", fontSize=12, leading=14, textColor=colors.HexColor("#0d47a1"),
                    fontName="Helvetica-Bold", spaceBefore=12, spaceAfter=6)))
            elif line.startswith("- ") or line.startswith("* "):
                # Bullet point
                line_text = line[2:] if line.startswith(("- ", "* ")) else line
                content.append(Paragraph("• " + line_text, styles["BodyCustom"]))
            else:
                # Normal body text
                content.append(Paragraph(line, styles["BodyCustom"]))
            content.append(Spacer(1, 0.05 * inch))

    doc.build(content)
    buffer.seek(0)
    return buffer

# -------------------
# Streamlit UI
# -------------------
st.set_page_config(page_title="AI Resume Builder", page_icon="📄", layout="centered")
st.markdown("## 📄 AI Resume Builder")
st.caption("Fill in your details → AI polishes them → Get a clean, ATS-friendly PDF")

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
            Create a professional, ATS-friendly resume in plain text with clear section headings and bullet points.
            Do not use Markdown link syntax for email or phone numbers; write them as plain text.
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

                # Generate cleaned PDF from AI output
                pdf_buffer = generate_pdf_from_ai(ai_resume_text)

                # Base64 encode for open-in-new-tab
                pdf_base64 = base64.b64encode(pdf_buffer.read()).decode()
                pdf_buffer.seek(0)

                st.success("✅ Resume ready!")

                st.download_button("📥 Download PDF", data=pdf_buffer, file_name="resume.pdf", mime="application/pdf")
                st.markdown(f'<a href="data:application/pdf;base64,{pdf_base64}" target="_blank">🔗 Open in New Tab</a>', unsafe_allow_html=True)

            else:
                st.error(f"❌ API Error: {response.status_code}")
                st.text(response.text)
