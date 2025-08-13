import streamlit as st
import openai
from fpdf import FPDF

# Load OpenAI API key
openai.api_key = st.secrets.get("OPENAI_API_KEY", "")

# Enhance experience with OpenAI
def enhance_text(prompt):
    if not openai.api_key:
        return prompt
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"Improve this resume bullet point:\n{prompt}",
            max_tokens=60
        )
        return response.choices[0].text.strip()
    except:
        return prompt

# Generate PDF
def create_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.set_font("Arial", 'B', size=16)
    pdf.cell(200, 10, txt=data['name'], ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"{data['email']} | {data['phone']}", ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", 'B', size=14)
    pdf.cell(200, 10, txt="Education", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=data['education'])

    pdf.set_font("Arial", 'B', size=14)
    pdf.cell(200, 10, txt="Experience", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=data['experience'])

    pdf.set_font("Arial", 'B', size=14)
    pdf.cell(200, 10, txt="Skills", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=data['skills'])

    output_file = "resume.pdf"
    pdf.output(output_file)
    return output_file

# Streamlit App
st.set_page_config(page_title="AI Resume Builder", page_icon="📝")
st.title("📝 AI Resume Builder")

with st.form("form"):
    name = st.text_input("Full Name")
    email = st.text_input("Email")
    phone = st.text_input("Phone Number")
    education = st.text_area("Education")
    experience = st.text_area("Experience")
    skills = st.text_input("Skills (comma separated)")
    enhance = st.checkbox("Enhance experience with AI")
    submitted = st.form_submit_button("Generate Resume")

if submitted:
    if not name or not email or not phone:
        st.warning("Please fill in all required fields.")
    else:
        enhanced_exp = enhance_text(experience) if enhance else experience

        resume = {
            "name": name,
            "email": email,
            "phone": phone,
            "education": education,
            "experience": enhanced_exp,
            "skills": skills
        }

        pdf_file = create_pdf(resume)

        with open(pdf_file, "rb") as f:
            st.success("✅ Resume created!")
            st.download_button("📄 Download PDF", data=f, file_name="resume.pdf", mime="application/pdf")
