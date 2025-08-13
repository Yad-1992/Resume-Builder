import streamlit as st
import requests
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT
import io

# Load Groq API key from Streamlit secrets
API_KEY = st.secrets["GROQ_API_KEY"]

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

# Stylish PDF generator
def generate_stylish_pdf(name, email, summary, skills, experience, education):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=40, leftMargin=40,
                            topMargin=60, bottomMargin=40)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='SectionHeader', fontSize=14, leading=16, spaceAfter=10, spaceBefore=20, alignment=TA_LEFT, textColor="#333333", fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name='BodyText', fontSize=11, leading=14, spaceAfter=8, alignment=TA_LEFT))

    content = []

    # Header
    content.append(Paragraph(f"<b>{name}</b><br/><font size=10>{email}</font>", styles['Title']))
    content.append(Spacer(1, 0.2 * inch))

    # Summary
    content.append(Paragraph("📝 Summary", styles['SectionHeader']))
    content.append(Paragraph(summary, styles['BodyText']))

    # Skills
    content.append(Paragraph("🛠️ Skills", styles['SectionHeader']))
    content.append(Paragraph(skills.replace(",", ", "), styles['BodyText']))

    # Experience
    content.append(Paragraph("💼 Experience", styles['SectionHeader']))
    content.append(Paragraph(experience, styles['BodyText']))

    # Education
    content.append(Paragraph("🎓 Education", styles['SectionHeader']))
    content.append(Paragraph(education, styles['BodyText']))

    doc.build(content)
    buffer.seek(0)
    return buffer

# Resume generation logic
if submitted:
    if not API_KEY:
        st.error("❌ API key not found. Please check your Streamlit secrets.")
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
                st.success("✅ Resume generated successfully!")

                st.markdown("### 📄 Preview")
                st.text_area("Your Resume", resume_text, height=400)

                # TXT download
                st.download_button(
                    label="📥 Download as TXT",
                    data=resume_text,
                    file_name="resume.txt",
                    mime="text/plain"
                )

                # Stylish PDF download
                pdf_buffer = generate_stylish_pdf(name, email, summary, skills, experience, education)
                st.download_button(
                    label="📄 Download as Stylish PDF",
                    data=pdf_buffer,
                    file_name="resume.pdf",
                    mime="application/pdf"
                )
            else:
                st.error(f"❌ API Error: {response.status_code}")
                st.text(response.text)
