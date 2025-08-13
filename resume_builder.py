import streamlit as st
import requests
from fpdf import FPDF
import io

# Load Groq API key from Streamlit secrets
API_KEY = st.secrets["GROQ_API_KEY"]

# Streamlit UI
st.set_page_config(page_title="AI Resume Builder", page_icon="🧠", layout="centered")
st.title("🧠 AI Resume Builder")
st.write("Fill in your details below and let AI craft a professional resume for you.")

# Input fields
name = st.text_input("👤 Full Name")
email = st.text_input("📧 Email")
summary = st.text_area("📝 Professional Summary")
skills = st.text_area("🛠️ Skills (comma-separated)")
experience = st.text_area("💼 Work Experience")
education = st.text_area("🎓 Education")

# Generate button
if st.button("✨ Generate Resume"):
    if not API_KEY:
        st.error("❌ API key not found. Please check your Streamlit secrets.")
    elif not name or not email:
        st.warning("⚠️ Please enter at least your name and email.")
    else:
        with st.spinner("Generating your resume..."):
            prompt = f"""
            Create a professional resume using the following details:
            Name: {name}
            Email: {email}
            Summary: {summary}
            Skills: {skills}
            Experience: {experience}
            Education: {education}
            Format it with clear headings, bullet points, and a clean layout.
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
                st.markdown("### 📄 Your AI-Generated Resume")
                st.text_area("Resume", resume_text, height=400)

                # TXT download
                st.download_button(
                    label="📥 Download as TXT",
                    data=resume_text,
                    file_name="resume.txt",
                    mime="text/plain"
                )

                # PDF generation
                pdf = FPDF()
                pdf.add_page()
                pdf.set_auto_page_break(auto=True, margin=15)
                pdf.set_font("Arial", size=12)

                for line in resume_text.split("\n"):
                    pdf.multi_cell(0, 10, line)

                pdf_buffer = io.BytesIO()
                pdf.output(pdf_buffer)
                pdf_buffer.seek(0)

                st.download_button(
                    label="📄 Download as PDF",
                    data=pdf_buffer,
                    file_name="resume.pdf",
                    mime="application/pdf"
                )
            else:
                st.error(f"❌ API Error: {response.status_code}")
                st.text(response.text)
