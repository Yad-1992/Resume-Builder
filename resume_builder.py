import os
import streamlit as st
from fpdf import FPDF
from groq import Groq

# -------------------
# API Key Handling
# -------------------
GROQ_API_KEY = None

if "GROQ_API_KEY" in st.secrets:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
elif "GROQ_API_KEY" in os.environ:
    GROQ_API_KEY = os.environ["GROQ_API_KEY"]

if not GROQ_API_KEY:
    st.error("❌ GROQ_API_KEY not found. Please set it in Streamlit Secrets or as an environment variable.")
    st.stop()

# -------------------
# Streamlit UI
# -------------------
st.set_page_config(page_title="AI Resume Generator", layout="centered")

st.title("📄 AI Resume Generator")
st.write("Fill in the details below to generate a professional resume in PDF format.")

name = st.text_input("Full Name")
email = st.text_input("Email")
phone = st.text_input("Phone")
summary = st.text_area("Professional Summary")
skills = st.text_area("Skills (comma separated)")
experience = st.text_area("Experience (one job per line: Job Title - Company - Years)")
education = st.text_area("Education (one entry per line: Degree - Institution - Year)")

if st.button("Generate Resume PDF"):
    with st.spinner("Creating your AI-powered resume..."):

        # -------------------
        # AI Resume Generation
        # -------------------
        client = Groq(api_key=GROQ_API_KEY)

        prompt = f"""
        Create a professional, ATS-friendly resume in plain text using the details below:
        Name: {name}
        Email: {email}
        Phone: {phone}
        Summary: {summary}
        Skills: {skills}
        Experience: {experience}
        Education: {education}
        Format it neatly for a resume.
        """

        try:
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )

            resume_text = response.choices[0].message.content.strip()

            # -------------------
            # PDF Creation
            # -------------------
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            for line in resume_text.split("\n"):
                pdf.multi_cell(0, 8, line)

            pdf_filename = "resume.pdf"
            pdf.output(pdf_filename)

            # -------------------
            # Download Button
            # -------------------
            with open(pdf_filename, "rb") as file:
                st.download_button(
                    label="📥 Download Resume PDF",
                    data=file,
                    file_name="resume.pdf",
                    mime="application/pdf"
                )

        except Exception as e:
            st.error(f"❌ Error: {e}")
