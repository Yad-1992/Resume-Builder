import streamlit as st
import requests
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
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

# PDF generation function using ReportLab
def generate_pdf(text):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50

    for line in text.split("\n"):
        c.drawString(50, y, line)
        y -= 15
        if y < 50:
            c.showPage()
            y = height - 50

    c.save()
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

                # PDF download
                pdf_buffer = generate_pdf(resume_text)
                st.download_button(
                    label="📄 Download as PDF",
                    data=pdf_buffer,
                    file_name="resume.pdf",
                    mime="application/pdf"
                )
            else:
                st.error(f"❌ API Error: {response.status_code}")
                st.text(response.text)
