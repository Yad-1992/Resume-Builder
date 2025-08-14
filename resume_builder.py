# app.py  ->  streamlit run app.py
import os, io, re, json, base64, requests, streamlit as st
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch

# -------------------- API KEY (secrets or env) --------------------
API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))
if not API_KEY:
    st.error("Set GROQ_API_KEY in Streamlit Secrets or env.")
    st.stop()

# -------------------- UI --------------------
st.set_page_config(page_title="AI Resume Builder", page_icon="📄", layout="centered")
st.markdown("## 📄 AI Resume Builder (Pro + Minimal)")
with st.form("resume"):
    name = st.text_input("Full Name")
    email = st.text_input("Email")
    phone = st.text_input("Phone")
    summary = st.text_area("Summary", height=80)
    skills = st.text_area("Skills (comma separated)", height=60)
    exp_title = st.text_input("Experience Title")
    exp_company = st.text_input("Company")
    exp_period = st.text_input("Period (e.g., 2021–Present)")
    exp_points = st.text_area("Experience Bullets (one per line)", height=100)
    edu_degree = st.text_input("Degree")
    edu_inst = st.text_input("Institution")
    edu_year = st.text_input("Year")
    submitted = st.form_submit_button("✨ Generate")

# -------------------- AI (JSON ONLY) --------------------
JSON_SCHEMA = {
  "name": "",
  "contact": {"email": "", "phone": ""},
  "summary": "",
  "skills": [],
  "experience": [{"title": "", "company": "", "period": "", "points": []}],
  "education": [{"degree": "", "institution": "", "year": ""}]
}

PROMPT_TMPL = """
You are a resume formatter. Return JSON ONLY. No prose. Use this exact schema:
{
  "name": "Full Name",
  "contact": {"email": "email", "phone": "phone"},
  "summary": "1-3 lines, concise.",
  "skills": ["Skill 1","Skill 2","Skill 3"],
  "experience": [
    {"title":"Job Title","company":"Company","period":"YYYY–YYYY","points":["• result/impact","• action + metric"] }
  ],
  "education": [
    {"degree":"Degree","institution":"Institution","year":"Year"}
  ]
}

Fill the fields using the user data. Do NOT use markdown links. No placeholders if user gave data.
User data:
Name: {name}
Email: {email}
Phone: {phone}
Summary: {summary}
Skills (comma): {skills}
Experience Title: {exp_title}
Company: {exp_company}
Period: {exp_period}
Experience Points (lines): {exp_points}
Education Degree: {edu_degree}
Institution: {edu_inst}
Year: {edu_year}
"""

def call_groq_json(payload: dict) -> dict:
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [{"role": "user", "content": payload["prompt"]}],
        "temperature": 0.2,
        "max_tokens": 1200
    }
    r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=60)
    r.raise_for_status()
    txt = r.json()["choices"][0]["message"]["content"].strip()

    # Extract strict JSON (best-effort)
    if txt.startswith("{") and txt.endswith("}"):
        raw = txt
    else:
        m = re.search(r"\{[\s\S]*\}", txt)
        raw = m.group(0) if m else "{}"

    try:
        obj = json.loads(raw)
    except Exception:
        obj = {}
    return obj

# -------------------- PDF (Professional + Minimal) --------------------
def hr_line(width=1, color=colors.HexColor("#E5E7EB")):
    t = Table([[""]], colWidths=[460])
    t.setStyle(TableStyle([("LINEBELOW", (0,0), (-1,-1), width, color)]))
    return t

def make_pdf(data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=54, bottomMargin=40)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Name", fontName="Helvetica-Bold", fontSize=18, leading=22, alignment=TA_CENTER))
    styles.add(ParagraphStyle(name="Contact", fontName="Helvetica", fontSize=10, textColor=colors.HexColor("#6B7280"), alignment=TA_CENTER, leading=14))
    styles.add(ParagraphStyle(name="H", fontName="Helvetica-Bold", fontSize=11, textColor=colors.HexColor("#0D47A1"), spaceBefore=12, spaceAfter=6))
    styles.add(ParagraphStyle(name="Body", fontName="Helvetica", fontSize=10, leading=14))
    styles.add(ParagraphStyle(name="Bullet", fontName="Helvetica", fontSize=10, leading=14, leftIndent=12))

    flow = []
    flow.append(Paragraph(data["name"], styles["Name"]))
    flow.append(Paragraph(f'{data["contact"].get("email","")}  |  {data["contact"].get("phone","")}', styles["Contact"]))
    flow.append(Spacer(1, 0.15*inch))
    flow.append(hr_line()); flow.append(Spacer(1, 0.08*inch))

    if data.get("summary"):
        flow.append(Paragraph("PROFESSIONAL SUMMARY", styles["H"]))
        flow.append(Paragraph(data["summary"], styles["Body"]))
        flow.append(Spacer(1, 0.06*inch))

    if data.get("skills"):
        flow.append(Paragraph("CORE SKILLS", styles["H"]))
        for s in data["skills"]:
            if s: flow.append(Paragraph(f"• {s}", styles["Bullet"]))
        flow.append(Spacer(1, 0.06*inch))

    if data.get("experience"):
        flow.append(Paragraph("EXPERIENCE", styles["H"]))
        for x in data["experience"]:
            title = x.get("title","").strip()
            company = x.get("company","").strip()
            period = x.get("period","").strip()
            header = " — ".join([y for y in [title, company] if y])
            if header:
                flow.append(Paragraph(f"{header}  ({period})", styles["Body"]))
            for p in x.get("points", []):
                if p: flow.append(Paragraph(f"• {p}", styles["Bullet"]))
            flow.append(Spacer(1, 0.04*inch))

    if data.get("education"):
        flow.append(Paragraph("EDUCATION", styles["H"]))
        for e in data["education"]:
            deg = e.get("degree","").strip()
            inst = e.get("institution","").strip()
            yr = e.get("year","").strip()
            line = " — ".join([v for v in [deg, inst] if v])
            if line:
                flow.append(Paragraph(f"{line} ({yr})", styles["Body"]))

    doc.build(flow)
    buf.seek(0)
    return buf.read()

# -------------------- Submit --------------------
if submitted:
    if not name or not email:
        st.warning("Name & Email required.")
        st.stop()

    prompt = PROMPT_TMPL.format(
        name=name, email=email, phone=phone, summary=summary, skills=skills,
        exp_title=exp_title, exp_company=exp_company, exp_period=exp_period,
        exp_points=exp_points, edu_degree=edu_degree, edu_inst=edu_inst, edu_year=edu_year
    )

    try:
        ai_obj = call_groq_json({"prompt": prompt})
    except Exception as e:
        st.error(f"API error: {e}")
        st.stop()

    # Fallback fill if fields missing
    if not ai_obj:
        ai_obj = JSON_SCHEMA.copy()
    ai_obj.setdefault("name", name)
    ai_obj.setdefault("contact", {"email": email, "phone": phone})
    ai_obj["contact"].setdefault("email", email)
    ai_obj["contact"].setdefault("phone", phone)
    ai_obj.setdefault("summary", summary)
    if not ai_obj.get("skills"):
        ai_obj["skills"] = [s.strip() for s in skills.split(",") if s.strip()]
    if not ai_obj.get("experience"):
        ai_obj["experience"] = [{
            "title": exp_title, "company": exp_company, "period": exp_period,
            "points": [p.strip() for p in exp_points.split("\n") if p.strip()]
        }]
    if not ai_obj.get("education"):
        ai_obj["education"] = [{"degree": edu_degree, "institution": edu_inst, "year": edu_year}]

    pdf_bytes = make_pdf(ai_obj)
    b64 = base64.b64encode(pdf_bytes).decode()

    st.success("✅ Resume ready")
    st.download_button("📥 Download PDF", data=pdf_bytes, file_name="resume.pdf", mime="application/pdf")
    st.markdown(f'<a href="data:application/pdf;base64,{b64}" target="_blank">🔗 Open in New Tab</a>', unsafe_allow_html=True)
