# app.py — Run: streamlit run app.py
import os, io, re, json, base64, time, requests, streamlit as st
from typing import Any, Dict, List
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch

# -------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="AI Resume Builder", page_icon="📄", layout="centered")
st.markdown("""<style>
.block-container {max-width: 760px;}
h1,h2 {margin-bottom:.2rem}
.small {color:#6b7280;font-size:12px}
</style>""", unsafe_allow_html=True)

# -------------------- API KEY HANDLING --------------------
API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))
if not API_KEY:
    st.warning("🔑 No GROQ API key found. Enter it below to continue.")
    API_KEY = st.text_input("Enter GROQ API Key", type="password")
    if not API_KEY:
        st.stop()

MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# -------------------- UI --------------------
st.markdown("## 📄 AI Resume Builder — Professional & Minimal")
st.caption("Enter minimal info, AI will build the rest.")

with st.form("f"):
    name = st.text_input("Full Name")
    email = st.text_input("Email")
    phone = st.text_input("Phone")
    role  = st.text_input("Target Role (optional)")
    summary_hint = st.text_area("1–2 lines about you (optional)", height=80)
    skills_raw   = st.text_input("Skills (comma separated, optional)")
    exp_raw      = st.text_area("Past roles (free text, optional)", height=100,
                 help="e.g., Project Coordinator at Nokia, 2019–Now; handled reporting, Python, SQL.")
    edu_raw      = st.text_input("Education (optional)", help="e.g., MBA, BPUT, 2023")
    city_country = st.text_input("Location (optional)")
    submitted    = st.form_submit_button("✨ Generate Resume")

# -------------------- HELPERS --------------------
def clean_text(s: str) -> str:
    if not s: return ""
    s = s.replace("mailto:", "")
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    s = re.sub(r"\*\*(.*?)\*\*", r"\1", s)
    s = re.sub(r"\*(.*?)\*", r"\1", s)
    s = re.sub(r"_(.*?)_", r"\1", s)
    return s.strip()

def ensure_list(x: Any) -> List[str]:
    if x is None: return []
    if isinstance(x, list): return [clean_text(str(i)) for i in x if str(i).strip()]
    return [clean_text(i) for i in str(x).split(",") if i.strip()]

def clip(text: str, n: int = 500) -> str:
    return (text[:n] + "…") if text and len(text) > n else (text or "")

# -------------------- STRONGER PROMPT --------------------
PROMPT = """You are a professional resume writer.
Return JSON ONLY. No explanations. Follow this schema EXACTLY:
{{
  "name": "Full Name",
  "contact": {{"email": "email", "phone": "phone", "location": "City, Country"}},
  "role": "Target Role",
  "summary": "A polished, concise 2–3 sentence summary that highlights expertise, achievements, and industry keywords.",
  "skills": ["Skill 1","Skill 2","Skill 3","..."],
  "experience": [
    {{"title":"Job Title","company":"Company","period":"YYYY–YYYY",
     "points":["Achievement with metric or impact","Another achievement","Another"]}}
  ],
  "education": [{{"degree":"Degree","institution":"Institution","year":"Year"}}]
}}

Rules:
- If user input is incomplete, intelligently expand with relevant professional details.
- Always add 8–12 role-relevant skills.
- Always add 3–5 bullet points per job, written in action-result format.
- Make summary impactful and aligned with target role.
- Use realistic company names, metrics, and responsibilities if missing.
- Keep language simple, professional, and ATS-friendly.
- No markdown, no links.

User data:
Name: {name}
Email: {email}
Phone: {phone}
Location: {loc}
Target Role: {role}
Summary hint: {summary_hint}
Skills (comma): {skills}
Past roles: {exp}
Education: {edu}
"""

# -------------------- AI CALL --------------------
def call_groq_json(prompt: str, retries: int = 2, timeout: int = 60) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"model": MODEL, "messages": [{"role":"user","content": prompt}],
               "temperature": 0.4, "max_tokens": 1400}
    for i in range(retries + 1):
        try:
            r = requests.post(GROQ_URL, headers=headers, json=payload, timeout=timeout)
            r.raise_for_status()
            txt = r.json()["choices"][0]["message"]["content"].strip()
            m = re.search(r"\{[\s\S]*\}\s*$", txt)
            raw = m.group(0) if m else "{}"
            return json.loads(raw)
        except Exception:
            if i == retries: return {}
            time.sleep(0.8 * (i+1))
    return {}

def coalesce(ai: Dict[str, Any]) -> Dict[str, Any]:
    out = {
        "name": clean_text(ai.get("name") or name),
        "contact": {
            "email": clean_text(ai.get("contact", {}).get("email") or email),
            "phone": clean_text(ai.get("contact", {}).get("phone") or phone),
            "location": clean_text(ai.get("contact", {}).get("location") or city_country),
        },
        "role": clean_text(ai.get("role") or role),
        "summary": clip(clean_text(ai.get("summary") or summary_hint), 500),
        "skills": ensure_list(ai.get("skills") or skills_raw),
        "experience": ai.get("experience", []),
        "education": ai.get("education", [])
    }
    return out

# -------------------- PDF --------------------
def divider():
    t = Table([[""]], colWidths=[460])
    t.setStyle(TableStyle([("LINEBELOW",(0,0),(-1,-1), 0.6, colors.HexColor("#E5E7EB"))]))
    return t

def make_pdf(data: Dict[str, Any]) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=44, rightMargin=44, topMargin=56, bottomMargin=44)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Name", fontName="Helvetica-Bold", fontSize=18, leading=22, alignment=TA_CENTER))
    styles.add(ParagraphStyle(name="Role", fontName="Helvetica", fontSize=11, leading=14, alignment=TA_CENTER, textColor=colors.HexColor("#374151")))
    styles.add(ParagraphStyle(name="Contact", fontName="Helvetica", fontSize=10, leading=14, alignment=TA_CENTER, textColor=colors.HexColor("#6B7280")))
    styles.add(ParagraphStyle(name="H", fontName="Helvetica-Bold", fontSize=11, textColor=colors.HexColor("#0D47A1"), spaceBefore=12, spaceAfter=6))
    styles.add(ParagraphStyle(name="Body", fontName="Helvetica", fontSize=10, leading=14, alignment=TA_LEFT))
    styles.add(ParagraphStyle(name="BulletCustom", fontName="Helvetica", fontSize=10, leading=14, leftIndent=12))

    flow = []
    flow.append(Paragraph(data["name"] or "", styles["Name"]))
    if data.get("role"): flow.append(Paragraph(data["role"], styles["Role"]))
    contact_line = "  •  ".join([x for x in [data["contact"].get("email",""), data["contact"].get("phone",""), data["contact"].get("location","")] if x])
    if contact_line: flow.append(Paragraph(contact_line, styles["Contact"]))
    flow.append(Spacer(1, 0.12*inch))
    flow.append(divider()); flow.append(Spacer(1, 0.04*inch))

    if data.get("summary"):
        flow.append(Paragraph("PROFESSIONAL SUMMARY", styles["H"]))
        flow.append(Paragraph(data["summary"], styles["Body"]))
        flow.append(Spacer(1, 0.04*inch))

    if data.get("skills"):
        flow.append(Paragraph("CORE SKILLS", styles["H"]))
        line, count = "", 0
        for s in data["skills"]:
            token = (" • " if count else "") + s
            if len(line + token) > 95:
                flow.append(Paragraph(line, styles["Body"]))
                line, count = s, 1
            else:
                line = line + token if count else s
                count += 1
        if line: flow.append(Paragraph(line, styles["Body"]))
        flow.append(Spacer(1, 0.04*inch))

    if data.get("experience"):
        flow.append(Paragraph("EXPERIENCE", styles["H"]))
        for x in data["experience"]:
            header = " — ".join([v for v in [x.get("title",""), x.get("company","")] if v])
            per = x.get("period","")
            flow.append(Paragraph(f"{header}  {f'({per})' if per else ''}", styles["Body"]))
            for p in x.get("points", []):
                if p: flow.append(Paragraph("• " + p, styles["BulletCustom"]))
            flow.append(Spacer(1, 0.02*inch))

    if data.get("education"):
        flow.append(Paragraph("EDUCATION", styles["H"]))
        for e in data["education"]:
            line = " — ".join([v for v in [e.get("degree",""), e.get("institution","")] if v])
            yr = e.get("year","")
            flow.append(Paragraph(f"{line} {f'({yr})' if yr else ''}", styles["Body"]))

    doc.build(flow)
    buf.seek(0)
    return buf.read()

# -------------------- MAIN --------------------
if submitted:
    if not name or not email:
        st.warning("Name & Email required.")
        st.stop()

    with st.spinner("Building resume with AI..."):
        prompt = PROMPT.format(
            name=clean_text(name), email=clean_text(email), phone=clean_text(phone),
            loc=clean_text(city_country), role=clean_text(role),
            summary_hint=clip(clean_text(summary_hint), 400),
            skills=clean_text(skills_raw), exp=clip(clean_text(exp_raw), 1200),
            edu=clean_text(edu_raw)
        )
        ai = call_groq_json(prompt)
        data = coalesce(ai)
        pdf_bytes = make_pdf(data)
        b64 = base64.b64encode(pdf_bytes).decode()

    st.success("✅ Ready")
    st.download_button("📥 Download PDF", data=pdf_bytes, file_name="resume.pdf", mime="application/pdf")
    st.markdown(f'<a class="small" href="data:application/pdf;base64,{b64}" target="_blank">🔗 Open in new tab</a>', unsafe_allow_html=True)
