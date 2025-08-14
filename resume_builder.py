import os
import streamlit as st
import requests
import base64
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT
import io

# --- API Key loader ---
API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))

# Page config
st.set_page_config(
    page_title="AI Resume Builder",
    page_icon="📄",
    layout="centered"
)

# Custom styling
st.markdown("""
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 700px;
        margin: auto;
    }
    textarea {
        font-size: 14px !important;
    }
    .stTextInput > div > input {
        background-color: #f9f9f9;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("## 📄 Minimal AI Resume Builder")
st.markdown("Craft a clean, professional resume with AI in seconds.")
st.markdown("---")

# Resume style selection
template = st.selectbox("🎨 Resume Style", [
    "Modern", "Minimalist", "Professional", "Creative", "Compact"
])

# Input form
with st.form("resume_form"):
    name = st.text_input("👤 Full Name")
    email = st.text_input("📧 Email")
    summary = st.text_area("📝 Professional Summary", height=100)
    skills = st.text_area("🛠️ Skills (comma-separated)", height=80)
    experience = st.text_area("💼 Work Experience", height=120)
    education = st.text_area("🎓 Education", height=100)
    submitted = st.form_submit_button("✨ Generate Resume")

# PDF generator using AI text
def generate_pdf_from_ai(ai_text):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=40, leftMargin=40,
                            topMargin=60, bottomMargin=40)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='BodyText', fontSize=11, leading=14, spaceAfter=8, alignment=TA_LEFT))

    content = []
    for line in ai_text.split("\n"):
        if line.strip():
            content.append(Paragraph(line.strip(), styles['BodyText']))
            content.append(Spacer(1, 0.1 * inch))

    doc.build(content)
    buffer.seek(0)
    return buffer

# Resume generation logic
if submitted:
    if not API_KEY:
        st.error("❌ API key not found. Please set it in Streamlit secrets or as an environment variable.")
    elif not name or not email:
        st.warning("⚠️ Please enter at least your name and email.")
    else:
        with st.spinner("Generating your resume..."):
            prompt = f"""
            Create a {template.lower()} style resume using the following details:
            Name: {name}
            Email: {email}
            Summary: {summary}
            Skills: {skills}
            Experience: {experience}
            Education: {education}
            Format it with clear headings, bullet points, and a layout that reflects the '{template}' style.
            """

            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }

            data = {
                "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }

            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=data
            )

            if response.status_code == 200:
                result = response.json()
                resume_text = result["choices"][0]["message"]["content"]

                # Generate PDF from AI text
                pdf_buffer = generate_pdf_from_ai(resume_text)

                # Encode PDF to Base64
                pdf_base64 = base64.b64encode(pdf_buffer.read()).decode()
                pdf_buffer.seek(0)

                st.success("✅ Resume generated successfully!")

                # Download button
                st.download_button(
                    label="📄 Download Resume as PDF",
                    data=pdf_buffer,
                    file_name="resume.pdf",
                    mime="application/pdf"
                )

                # Open in new tab link
                open_link_html = f'<a href="data:application/pdf;base64,{pdf_base64}" target="_blank">🔗 Open Resume in New Tab</a>'
                st.markdown(open_link_html, unsafe_allow_html=True)

            else:
                st.error(f"❌ API Error: {response.status_code}")
                st.text(response.text)
