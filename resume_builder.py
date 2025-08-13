import streamlit as st
import requests

# Load API key from Streamlit secrets
API_KEY = st.secrets["GOOGLE_API_KEY"]

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
            "contents": [{"parts": [{"text": prompt}]}]
        }

        response = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
            headers=headers,
            json=data
        )

        if response.status_code == 200:
            result = response.json()
            resume_text = result['candidates'][0]['content']['parts'][0]['text']
            st.success("✅ Resume generated successfully!")
            st.markdown("### 📄 Your AI-Generated Resume")
            st.text_area("Resume", resume_text, height=400)

            # Optional: Download button
            st.download_button(
                label="📥 Download Resume as TXT",
                data=resume_text,
                file_name="resume.txt",
                mime="text/plain"
            )
        else:
            st.error("❌ Failed to generate resume. Please check your API key or try again later.")
