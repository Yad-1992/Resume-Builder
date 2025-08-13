import streamlit as st
import requests

# Load API key from Streamlit secrets
API_KEY = st.secrets["GOOGLE_API_KEY"]

# Streamlit page config
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
                "contents": [{"parts": [{"text": prompt}]}]
            }

            response = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
                headers=headers,
                json=data
            )

            if response.status_code == 200:
                result = response.json()
                try:
                    resume_text = result['candidates'][0]['content']['parts'][0]['text']
                    st.success("✅ Resume generated successfully!")
                    st.markdown("### 📄 Your AI-Generated Resume")
                    st.text_area("Resume", resume_text, height=400)

                    # Download button
                    st.download_button(
                        label="📥 Download Resume as TXT",
                        data=resume_text,
                        file_name="resume.txt",
                        mime="text/plain"
                    )
                except Exception as e:
                    st.error("⚠️ Unexpected response format. Please try again.")
            else:
                st.error(f"❌ API Error: {response.status_code}")
