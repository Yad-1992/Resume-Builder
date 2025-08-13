import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
import base64

st.title("Resume Builder Web App")

# Function to convert PDF to base64 for download
def pdf_to_base64(pdf_bytes):
    return base64.b64encode(pdf_bytes).decode('utf-8')

# Function to create resume PDF
def create_resume_pdf(data, output):
    doc = SimpleDocTemplate(output, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    styles = getSampleStyleSheet()
    story = []

    # Custom styles
    title_style = ParagraphStyle(name='Title', fontSize=20, leading=24, spaceAfter=20, fontName='Helvetica-Bold')
    section_style = ParagraphStyle(name='Section', fontSize=14, leading=18, spaceAfter=10, fontName='Helvetica-Bold')
    normal_style = ParagraphStyle(name='Normal', fontSize=12, leading=14, spaceAfter=8)

    # Personal Information
    story.append(Paragraph(f"{data['name']}", title_style))
    story.append(Paragraph(f"{data['email']} | {data['phone']} | {data['address']}", normal_style))
    story.append(Spacer(1, 12))

    # Education
    story.append(Paragraph("Education", section_style))
    for edu in data['education']:
        story.append(Paragraph(f"{edu['degree']} - {edu['institution']}", normal_style))
        story.append(Paragraph(f"{edu['years']}", normal_style))
        story.append(Spacer(1, 6))

    # Work Experience
    story.append(Paragraph("Work Experience", section_style))
    for job in data['experience']:
        story.append(Paragraph(f"{job['title']} at {job['company']}", normal_style))
        story.append(Paragraph(f"{job['years']}", normal_style))
        story.append(Paragraph(f"{job['description']}", normal_style))
        story.append(Spacer(1, 6))

    # Skills
    story.append(Paragraph("Skills", section_style))
    skills = [[skill] for skill in data['skills'].split(', ')] if data['skills'] else []
    if skills:
        table = Table(skills, colWidths=[400])
        table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(table)
    story.append(Spacer(1, 12))

    # Projects
    story.append(Paragraph("Projects", section_style))
    for proj in data['projects']:
        story.append(Paragraph(f"{proj['name']}", normal_style))
        story.append(Paragraph(f"{proj['description']}", normal_style))
        story.append(Spacer(1, 6))

    doc.build(story)

# Initialize session state for resume data
if 'resume_data' not in st.session_state:
    st.session_state.resume_data = {
        'name': '',
        'email': '',
        'phone': '',
        'address': '',
        'education': [],
        'experience': [],
        'skills': '',
        'projects': []
    }

# Form for user input
with st.form("resume_form"):
    st.subheader("Personal Information")
    st.session_state.resume_data['name'] = st.text_input("Full Name", value=st.session_state.resume_data['name'])
    st.session_state.resume_data['email'] = st.text_input("Email", value=st.session_state.resume_data['email'])
    st.session_state.resume_data['phone'] = st.text_input("Phone", value=st.session_state.resume_data['phone'])
    st.session_state.resume_data['address'] = st.text_input("Address", value=st.session_state.resume_data['address'])

    st.subheader("Education")
    num_education = st.number_input("Number of Education Entries", min_value=0, value=len(st.session_state.resume_data['education']) or 1)
    education = []
    for i in range(num_education):
        st.write(f"Education {i+1}")
        degree = st.text_input(f"Degree {i+1}", value=st.session_state.resume_data['education'][i]['degree'] if i < len(st.session_state.resume_data['education']) else "")
        institution = st.text_input(f"Institution {i+1}", value=st.session_state.resume_data['education'][i]['institution'] if i < len(st.session_state.resume_data['education']) else "")
        years = st.text_input(f"Years {i+1}", value=st.session_state.resume_data['education'][i]['years'] if i < len(st.session_state.resume_data['education']) else "")
        education.append({'degree': degree, 'institution': institution, 'years': years})
    st.session_state.resume_data['education'] = education

    st.subheader("Work Experience")
    num_experience = st.number_input("Number of Work Experiences", min_value=0, value=len(st.session_state.resume_data['experience']) or 1)
    experience = []
    for i in range(num_experience):
        st.write(f"Experience {i+1}")
        title = st.text_input(f"Job Title {i+1}", value=st.session_state.resume_data['experience'][i]['title'] if i < len(st.session_state.resume_data['experience']) else "")
        company = st.text_input(f"Company {i+1}", value=st.session_state.resume_data['experience'][i]['company'] if i < len(st.session_state.resume_data['experience']) else "")
        years = st.text_input(f"Years {i+1}", value=st.session_state.resume_data['experience'][i]['years'] if i < len(st.session_state.resume_data['experience']) else "")
        description = st.text_area(f"Description {i+1}", value=st.session_state.resume_data['experience'][i]['description'] if i < len(st.session_state.resume_data['experience']) else "")
        experience.append({'title': title, 'company': company, 'years': years, 'description': description})
    st.session_state.resume_data['experience'] = experience

    st.subheader("Skills")
    st.session_state.resume_data['skills'] = st.text_input("Skills (comma-separated)", value=st.session_state.resume_data['skills'])

    st.subheader("Projects")
    num_projects = st.number_input("Number of Projects", min_value=0, value=len(st.session_state.resume_data['projects']) or 1)
    projects = []
    for i in range(num_projects):
        st.write(f"Project {i+1}")
        name = st.text_input(f"Project Name {i+1}", value=st.session_state.resume_data['projects'][i]['name'] if i < len(st.session_state.resume_data['projects']) else "")
        description = st.text_area(f"Project Description {i+1}", value=st.session_state.resume_data['projects'][i]['description'] if i < len(st.session_state.resume_data['projects']) else "")
        projects.append({'name': name, 'description': description})
    st.session_state.resume_data['projects'] = projects

    submitted = st.form_submit_button("Generate Resume PDF")

# Real-time preview
st.subheader("Resume Preview")
if st.session_state.resume_data['name']:
    st.write(f"**{st.session_state.resume_data['name']}**")
    st.write(f"{st.session_state.resume_data['email']} | {st.session_state.resume_data['phone']} | {st.session_state.resume_data['address']}")
    st.write("### Education")
    for edu in st.session_state.resume_data['education']:
        if edu['degree']:
            st.write(f"- {edu['degree']} - {edu['institution']} ({edu['years']})")
    st.write("### Work Experience")
    for job in st.session_state.resume_data['experience']:
        if job['title']:
            st.write(f"- {job['title']} at {job['company']} ({job['years']})")
            st.write(f"  {job['description']}")
    st.write("### Skills")
    if st.session_state.resume_data['skills']:
        st.write(f"- {st.session_state.resume_data['skills']}")
    st.write("### Projects")
    for proj in st.session_state.resume_data['projects']:
        if proj['name']:
            st.write(f"- {proj['name']}")
            st.write(f"  {proj['description']}")

# Generate and download PDF
if submitted and st.session_state.resume_data['name']:
    output = BytesIO()
    create_resume_pdf(st.session_state.resume_data, output)
    st.download_button(
        label="Download Resume PDF",
        data=output.getvalue(),
        file_name="resume.pdf",
        mime="application/pdf"
    )
else:
    st.info("Please fill in at least your name to generate a resume.")