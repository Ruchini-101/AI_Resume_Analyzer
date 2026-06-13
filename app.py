import streamlit as st
import PyPDF2
from google import genai
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page config - MUST be the first Streamlit command
st.set_page_config(page_title="Resume ATS Analysis Dashboard", page_icon="📊", layout="wide")

# Custom CSS to match the dashboard design
st.markdown("""
<style>
    /* Global styles */
    .stApp {
        background-color: #f4f7fc;
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }
    
    /* Hide default Streamlit padding */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1200px !important;
    }
    
    /* Top Banner */
    .top-banner {
        background-color: #0b2559;
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 15px;
    }
    .top-banner h1 {
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
        letter-spacing: 1px;
    }
    .top-banner p {
        margin: 0;
        opacity: 0.8;
        font-size: 0.9rem;
    }
    
    /* Cards */
    .card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        height: 100%;
        border: 1px solid #e2e8f0;
    }
    .card-title {
        color: #1e3a8a;
        font-weight: 700;
        font-size: 1.1rem;
        margin-bottom: 1rem;
        text-transform: uppercase;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Score Card */
    .score-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
    }
    .circular-chart {
        display: block;
        margin: 10px auto;
        max-width: 80%;
        max-height: 250px;
    }
    .circle-bg {
        fill: none;
        stroke: #eee;
        stroke-width: 3.8;
    }
    .circle {
        fill: none;
        stroke-width: 2.8;
        stroke-linecap: round;
        animation: progress 1s ease-out forwards;
    }
    @keyframes progress {
        0% { stroke-dasharray: 0 100; }
    }
    .percentage {
        fill: #22c55e;
        font-family: sans-serif;
        font-size: 0.5em;
        text-anchor: middle;
        font-weight: bold;
    }
    .score-match {
        color: #22c55e;
        font-weight: 700;
        font-size: 1.2rem;
        margin-top: 10px;
    }
    .score-subtext {
        font-size: 0.8rem;
        color: #64748b;
        margin-top: 5px;
    }
    
    /* Strengths & Weaknesses */
    .strengths-card .card-title { color: #16a34a; }
    .weaknesses-card .card-title { color: #ef4444; }
    .strengths-card { border: 1px solid #bbf7d0; background: #f0fdf4; }
    .weaknesses-card { border: 1px solid #fecaca; background: #fef2f2; }
    
    ul.custom-list {
        list-style-type: none;
        padding-left: 0;
    }
    ul.custom-list li {
        position: relative;
        padding-left: 25px;
        margin-bottom: 12px;
        font-size: 0.9rem;
        color: #334155;
    }
    ul.custom-list.green li::before {
        content: '✅';
        position: absolute;
        left: 0;
        top: 2px;
        font-size: 0.8rem;
    }
    ul.custom-list.red li::before {
        content: '❗';
        position: absolute;
        left: 0;
        top: 2px;
        font-size: 0.8rem;
    }

    /* Snapshot Table */
    .snapshot-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.9rem;
    }
    .snapshot-table td {
        padding: 8px 0;
        border-bottom: 1px solid #f1f5f9;
    }
    .snapshot-table td:first-child {
        font-weight: 600;
        color: #475569;
        width: 40%;
    }
    .snapshot-table td:last-child {
        text-align: right;
        color: #1e293b;
    }
    
    /* Skills Breakdown */
    .skill-cat {
        margin-bottom: 12px;
    }
    .skill-cat-title {
        font-weight: 600;
        font-size: 0.85rem;
        color: #1e3a8a;
    }
    .skill-cat-list {
        font-size: 0.8rem;
        color: #64748b;
    }
    
    /* Bottom Banner */
    .bottom-banner {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1.5rem;
        margin-top: 1.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 20px;
    }
    .recommendation-text {
        font-size: 0.95rem;
        color: #334155;
        flex: 1;
    }
    .score-potential {
        background: #1e3a8a;
        color: white;
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: 700;
        white-space: nowrap;
    }
    
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# UI Header
# ---------------------------------------------------------
st.markdown("""
<div class="top-banner">
    <div style="font-size: 2.5rem;">🕵️‍♂️</div>
    <div>
        <h1>RESUME ATS ANALYSIS DASHBOARD</h1>
        <p>Comprehensive analysis of resume suitability for Applicant Tracking Systems</p>
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------
def read_resume(file):
    text = ""
    reader = PyPDF2.PdfReader(file)
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted
    return text

def analyze_resume(text, client):
    prompt = f"""
You are an advanced ATS resume analyzer.

Analyze the resume below and extract detailed information to populate a dashboard.
If a piece of information is missing from the resume, use "N/A".

Resume:
{text}

Return ONLY valid JSON with exactly this structure:
{{
  "ats_score": (integer between 0-100),
  "match_status": (string, e.g., "GOOD MATCH", "NEEDS WORK", "EXCELLENT"),
  "score_subtext": (string, 1 brief sentence summarizing the overall score),
  "strengths": [(list of 4-6 strings summarizing strong points)],
  "weaknesses": [(list of 4-6 strings summarizing areas for improvement)],
  "snapshot": {{
    "field": (string, general industry/field),
    "level": (string, e.g., "Undergraduate", "Entry-level", "Senior"),
    "gpa": (string, e.g., "3.75 / 4.00" or "N/A"),
    "education": (string, e.g., "2024 - Present" or graduation year),
    "career_interests": (string, summarizing inferred career goals),
    "key_areas": (string, 3-4 key domain areas)
  }},
  "technical_skills": [
    {{"category": "Languages", "skills": "List of languages"}},
    {{"category": "Databases", "skills": "List of databases"}},
    {{"category": "Frameworks", "skills": "List of frameworks"}},
    {{"category": "Tools", "skills": "List of tools"}}
  ],
  "keyword_match": {{
    "technical_skills": (integer 0-100),
    "tools_and_technologies": (integer 0-100),
    "core_competencies": (integer 0-100),
    "education_and_coursework": (integer 0-100),
    "experience": (integer 0-100)
  }},
  "overall_recommendation": (string, 1-2 sentences of final advice),
  "score_potential": (string, e.g., "85+")
}}
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return str(e)


def render_dashboard(data):
    # ROW 1: Score, Strengths, Weaknesses
    r1c1, r1c2, r1c3 = st.columns([1, 1.5, 1.5])
    
    with r1c1:
        score = data.get("ats_score", 0)
        color = "#22c55e" if score >= 70 else ("#eab308" if score >= 50 else "#ef4444")
        dasharray = f"{score}, 100"
        
        st.markdown(f"""
        <div class="card">
            <div class="card-title">🎯 ATS SCORE</div>
            <div class="score-container">
                <svg viewBox="0 0 36 36" class="circular-chart">
                    <path class="circle-bg"
                        d="M18 2.0845
                        a 15.9155 15.9155 0 0 1 0 31.831
                        a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                    <path class="circle"
                        stroke="{color}"
                        stroke-dasharray="{dasharray}"
                        d="M18 2.0845
                        a 15.9155 15.9155 0 0 1 0 31.831
                        a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                    <text x="18" y="20.35" class="percentage" fill="{color}">{score}</text>
                    <text x="18" y="25.35" style="font-size: 0.15em; text-anchor: middle; fill: #64748b;">/100</text>
                </svg>
                <div class="score-match" style="color: {color}">{data.get("match_status", "")}</div>
                <div class="score-subtext">{data.get("score_subtext", "")}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with r1c2:
        strengths_html = "".join([f"<li>{s}</li>" for s in data.get("strengths", [])])
        st.markdown(f"""
        <div class="card strengths-card">
            <div class="card-title">👍 STRENGTHS</div>
            <ul class="custom-list green">
                {strengths_html}
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    with r1c3:
        weaknesses_html = "".join([f"<li>{w}</li>" for w in data.get("weaknesses", [])])
        st.markdown(f"""
        <div class="card weaknesses-card">
            <div class="card-title">👎 WEAKNESSES</div>
            <ul class="custom-list red">
                {weaknesses_html}
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)
        
    # ROW 2: Snapshot, Tech Skills, Keyword Match
    r2c1, r2c2, r2c3 = st.columns([1, 1, 1.2])
    
    with r2c1:
        snap = data.get("snapshot", {})
        st.markdown(f"""
        <div class="card">
            <div class="card-title">👤 CANDIDATE SNAPSHOT</div>
            <table class="snapshot-table">
                <tr><td>🎓 Field</td><td>{snap.get("field", "N/A")}</td></tr>
                <tr><td>📊 Level</td><td>{snap.get("level", "N/A")}</td></tr>
                <tr><td>⭐ GPA</td><td>{snap.get("gpa", "N/A")}</td></tr>
                <tr><td>📅 Education</td><td>{snap.get("education", "N/A")}</td></tr>
                <tr><td>🎯 Interests</td><td>{snap.get("career_interests", "N/A")}</td></tr>
                <tr><td>💼 Key Areas</td><td>{snap.get("key_areas", "N/A")}</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        
    with r2c2:
        skills = data.get("technical_skills", [])
        skills_html = ""
        for s in skills:
            skills_html += f"""<div class="skill-cat">
<div class="skill-cat-title">&lt;/&gt; {s.get("category", "")}</div>
<div class="skill-cat-list">{s.get("skills", "None")}</div>
</div>"""
            
        st.markdown(f"""<div class="card">
<div class="card-title">&lt;/&gt; TECHNICAL SKILLS BREAKDOWN</div>
<div style="margin-top: 10px;">
{skills_html}
</div>
</div>""", unsafe_allow_html=True)
        
    with r2c3:
        # Use a Streamlit container for progress bars so they render correctly
        st.markdown("""
        <div style="background: white; border-radius: 10px; padding: 1.5rem; box-shadow: 0 2px 10px rgba(0,0,0,0.05); height: 100%; border: 1px solid #e2e8f0;">
            <div style="color: #1e3a8a; font-weight: 700; font-size: 1.1rem; margin-bottom: 1rem; text-transform: uppercase;">
                🔍 KEYWORD MATCH SUMMARY
            </div>
        """, unsafe_allow_html=True)
        
        matches = data.get("keyword_match", {})
        labels = {
            "technical_skills": "✅ Technical Skills",
            "tools_and_technologies": "🛠 Tools & Technologies",
            "core_competencies": "📄 Core Competencies",
            "education_and_coursework": "🎓 Education & Coursework",
            "experience": "💼 Experience"
        }
        
        for key, label in labels.items():
            val = matches.get(key, 0)
            colA, colB, colC = st.columns([4, 5, 1])
            with colA: st.markdown(f"<span style='font-size:0.85rem; color:#475569;'>{label}</span>", unsafe_allow_html=True)
            with colB: st.progress(val / 100.0)
            with colC: st.markdown(f"<span style='font-size:0.85rem; font-weight:bold; color:#1e293b;'>{val}%</span>", unsafe_allow_html=True)
            
        st.markdown("</div>", unsafe_allow_html=True)
        
    # BOTTOM BANNER
    st.markdown(f"""
    <div class="bottom-banner">
        <div style="font-size: 1.5rem;">💡</div>
        <div class="recommendation-text">
            <strong>OVERALL RECOMMENDATION:</strong> {data.get("overall_recommendation", "")}
        </div>
        <div class="score-potential">
            📈 SCORE POTENTIAL: {data.get("score_potential", "")}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------
# Main App Logic
# ---------------------------------------------------------
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key or api_key == "your_api_key_here":
    st.warning("⚠️ Please set your GOOGLE_API_KEY in the `.env` file to use this app.")
else:
    client = genai.Client(api_key=api_key)
    
    with st.sidebar:
        st.header("Upload Document")
        uploaded_file = st.file_uploader("Upload your CV (PDF)", type=["pdf"])
        analyze_btn = st.button("Analyze Resume", type="primary", use_container_width=True)
        st.markdown("---")
        st.markdown("Upload your resume to get a comprehensive ATS analysis dashboard matching modern industry standards.")

    if uploaded_file is not None and analyze_btn:
        with st.spinner("Analyzing your resume... Extracting details..."):
            resume_text = read_resume(uploaded_file)
            
            if not resume_text.strip():
                st.error("Could not extract text from the PDF.")
            else:
                result_text = analyze_resume(resume_text, client)
                
                try:
                    cleaned = result_text.strip()
                    if cleaned.startswith("```json"):
                        cleaned = cleaned[7:]
                    if cleaned.endswith("```"):
                        cleaned = cleaned[:-3]
                        
                    data = json.loads(cleaned.strip())
                    render_dashboard(data)

                except json.JSONDecodeError:
                    st.error("Failed to parse the response from the AI.")
                    with st.expander("Show raw response"):
                        st.write(result_text)
    elif uploaded_file is None:
        st.info("👈 Please upload a PDF resume in the sidebar to begin.")
