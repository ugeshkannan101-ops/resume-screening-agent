"""
app.py
Streamlit Application: Resume Screening Agent (Agent Template Pack)
Supports both offline deterministic 3-pillar evaluation and live Google Gemini AI model synthesis.
"""

import os
import sys
import tempfile
import streamlit as st

# Add current directory to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.extractor import DocumentExtractor
from core.screener import ResumeScreeningAgent


# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="Resume Screening Agent",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1e3a8a;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #64748b;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .score-card {
        padding: 20px;
        border-radius: 12px;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        text-align: center;
    }
    .badge-success {
        background-color: #dcfce7;
        color: #15803d;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .badge-warning {
        background-color: #fef9c3;
        color: #854d0e;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .badge-danger {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .skill-tag-match {
        display: inline-block;
        background: #dcfce7;
        color: #166534;
        padding: 2px 8px;
        margin: 3px;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .skill-tag-missing {
        display: inline-block;
        background: #fee2e2;
        color: #991b1b;
        padding: 2px 8px;
        margin: 3px;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .skill-tag-bonus {
        display: inline-block;
        background: #e0f2fe;
        color: #0369a1;
        padding: 2px 8px;
        margin: 3px;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# AI Secrets & Provider Configuration
# ---------------------------------------------------------
ai_base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
ai_model = "gemini-1.5-flash"
ai_api_key = ""
has_real_ai = False

try:
    if "AI_BASE_URL" in st.secrets:
        ai_base_url = st.secrets["AI_BASE_URL"]
    if "AI_MODEL" in st.secrets:
        ai_model = st.secrets["AI_MODEL"]
    if "AI_API_KEY" in st.secrets:
        raw_key = st.secrets["AI_API_KEY"].strip()
        if raw_key and raw_key != "PASTE_YOUR_GEMINI_API_KEY_HERE":
            ai_api_key = raw_key
            has_real_ai = True
except Exception:
    pass


# ---------------------------------------------------------
# Sidebar: Settings & Preloaded Samples
# ---------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/color/96/artificial-intelligence.png", width=64)
    st.title("Screening Agent")
    
    st.markdown("### 🤖 Model Provider")
    st.info(f"**Provider**: Google Gemini (Free Tier)\n\n**Model**: `{ai_model}`\n\n**AI Mode**: {'🟢 Live Gemini Connected' if has_real_ai else '🟡 Offline Engine (Key Not Set)'}")
    
    if not has_real_ai:
        st.caption("Paste your Gemini API key inside `.streamlit/secrets.toml` to activate live generative reasoning.")

    st.markdown("---")
    st.markdown("### 🎯 Quick Test Presets")

    sample_choice = st.radio(
        "Load Preloaded Sample:",
        ("Analytics Engineer (High Fit)", "Full Stack Developer (Gap Test)", "Custom / Blank"),
        index=0
    )

    st.markdown("---")
    st.markdown("### ⚖️ Evaluation Weights")
    w_skill = st.slider("Skill Alignment (%)", min_value=10, max_value=80, value=40, step=5)
    w_exp = st.slider("Experience Relevance (%)", min_value=10, max_value=80, value=40, step=5)
    w_edu = st.slider("Education & Certs (%)", min_value=0, max_value=50, value=20, step=5)
    
    total_w = w_skill + w_exp + w_edu
    if total_w != 100:
        st.warning(f"Total weight is {total_w}%. Normalizing to 100% automatically.")
        w_skill_norm = w_skill / total_w
        w_exp_norm = w_exp / total_w
        w_edu_norm = w_edu / total_w
    else:
        w_skill_norm = w_skill / 100.0
        w_exp_norm = w_exp / 100.0
        w_edu_norm = w_edu / 100.0


# ---------------------------------------------------------
# Sample Data Preparation
# ---------------------------------------------------------
sample_jd_path = os.path.join(BASE_DIR, "samples", "job_descriptions")
sample_res_path = os.path.join(BASE_DIR, "samples", "resumes")

def load_file_content(path: str) -> str:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    return ""

default_jd = ""
default_res = ""

if sample_choice == "Analytics Engineer (High Fit)":
    default_jd = load_file_content(os.path.join(sample_jd_path, "analytics_engineer.txt"))
    default_res = load_file_content(os.path.join(sample_res_path, "analytics_engineer_ugesh.txt"))
elif sample_choice == "Full Stack Developer (Gap Test)":
    default_jd = load_file_content(os.path.join(sample_jd_path, "fullstack_developer.txt"))
    default_res = load_file_content(os.path.join(sample_res_path, "junior_frontend_dev.txt"))


# ---------------------------------------------------------
# Main UI Header
# ---------------------------------------------------------
st.markdown('<div class="main-title">📋 AI Resume Screening Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Automated candidate evaluation across <b>Skill Alignment</b>, <b>Experience Relevance</b>, and <b>Education Match</b>.</div>', unsafe_allow_html=True)


# ---------------------------------------------------------
# Ingestion: Job Description & Resume
# ---------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Job Description (JD)")
    uploaded_jd = st.file_uploader("Upload JD (.txt, .pdf, .docx)", type=["txt", "pdf", "docx"], key="jd_upload")
    if uploaded_jd:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_jd.name)[1]) as tmp:
            tmp.write(uploaded_jd.read())
            tmp_path = tmp.name
        jd_input = DocumentExtractor.extract_from_file(tmp_path)
        os.remove(tmp_path)
    else:
        jd_input = st.text_area("Or paste Job Description text:", value=default_jd, height=280)

with col2:
    st.subheader("2. Candidate Resume")
    uploaded_res = st.file_uploader("Upload Resume (.txt, .pdf, .docx)", type=["txt", "pdf", "docx"], key="res_upload")
    if uploaded_res:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_res.name)[1]) as tmp:
            tmp.write(uploaded_res.read())
            tmp_path = tmp.name
        res_input = DocumentExtractor.extract_from_file(tmp_path)
        os.remove(tmp_path)
    else:
        res_input = st.text_area("Or paste Candidate Resume text:", value=default_res, height=280)


# ---------------------------------------------------------
# Screen Candidate Action
# ---------------------------------------------------------
st.markdown("<br>", unsafe_allow_html=True)
screen_button = st.button("🚀 Evaluate Candidate Fit", type="primary", use_container_width=True)

if screen_button:
    if not jd_input.strip() or not res_input.strip():
        st.error("Please provide both a Job Description and a Candidate Resume to evaluate.")
    else:
        with st.spinner("Analyzing skill alignment, calculating tenure relevance, and checking credentials..."):
            agent = ResumeScreeningAgent(weights={
                "skills": w_skill_norm,
                "experience": w_exp_norm,
                "education": w_edu_norm
            })
            report = agent.screen(jd_input, res_input)

            # Optional AI Synthesis if Gemini Key is available
            ai_synthesis = None
            if has_real_ai:
                try:
                    from openai import OpenAI
                    client = OpenAI(base_url=ai_base_url, api_key=ai_api_key)
                    prompt = f"""
You are an executive recruiting specialist. Analyze the following candidate screening evaluation:
Candidate: {report['candidate_name']}
Overall Fit Score: {report['overall_fit_score']}/100 ({report['verdict']})
Matched Skills: {report['pillars']['skill_alignment']['matched_required']}
Missing Required Skills: {report['pillars']['skill_alignment']['missing_required']}
Candidate Experience: {report['pillars']['experience_relevance']['candidate_years']} yrs vs {report['pillars']['experience_relevance']['required_years']} yrs required.
Candidate Education: {report['pillars']['education_match']['candidate_education']}

Job Description snippet:
{jd_input[:1000]}

Provide a concise 3-paragraph executive hiring brief:
1. Candidate suitability summary and unique selling proposition.
2. Direct assessment of missing skills or tenure deltas and risk level.
3. Concrete interview guidance for the hiring team.
"""
                    response = client.chat.completions.create(
                        model=ai_model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3,
                        max_tokens=600
                    )
                    ai_synthesis = response.choices[0].message.content
                except Exception as e:
                    st.warning(f"Could not reach Gemini model: {e}. Falling back to deterministic analysis.")

        st.success("Screening Evaluation Complete!")

        # ---------------------------------------------------------
        # Candidate Header & Fit Score
        # ---------------------------------------------------------
        st.markdown("---")
        score = report["overall_fit_score"]
        verdict = report["verdict"]
        tier_class = report["tier_class"]

        badge_class = "badge-success" if tier_class == "success" else ("badge-warning" if tier_class == "warning" else "badge-danger")

        m_col1, m_col2, m_col3 = st.columns([1.5, 1, 1.5])
        with m_col1:
            st.markdown(f"### Candidate: **{report['candidate_name']}**")
            st.markdown(f"**Recommendation:** {report['recommendation']}")
        with m_col2:
            st.markdown(f"""
            <div class="score-card">
                <div style="font-size: 0.9rem; color: #64748b; font-weight: 600;">CANDIDATE FIT SCORE</div>
                <div style="font-size: 2.4rem; font-weight: 800; color: #0f172a;">{score}<span style="font-size: 1.2rem; color: #94a3b8;">/100</span></div>
                <span class="{badge_class}">{verdict}</span>
            </div>
            """, unsafe_allow_html=True)
        with m_col3:
            st.write("**Pillar Contribution**")
            st.progress(score / 100.0)
            st.caption(f"Skills: {report['pillars']['skill_alignment']['score']}% | Exp: {report['pillars']['experience_relevance']['score']}% | Edu: {report['pillars']['education_match']['score']}%")

        st.markdown("<br>", unsafe_allow_html=True)

        # ---------------------------------------------------------
        # Pillar Breakdown Tabs
        # ---------------------------------------------------------
        tab_skills, tab_exp, tab_edu, tab_qa, tab_ai = st.tabs([
            "🛠️ Skill Alignment",
            "📈 Experience Relevance",
            "🎓 Education & Credentials",
            "🎯 Tailored Interview Questions",
            "🤖 AI Executive Brief"
        ])

        with tab_skills:
            p_s = report["pillars"]["skill_alignment"]
            st.subheader(f"Skill Alignment Score: {p_s['score']}%")
            
            c_s1, c_s2 = st.columns(2)
            with c_s1:
                st.markdown("**✅ Matched Required Skills:**")
                if p_s["matched_required"]:
                    chips = "".join([f'<span class="skill-tag-match">✓ {s.upper()}</span>' for s in p_s["matched_required"]])
                    st.markdown(chips, unsafe_allow_html=True)
                else:
                    st.write("No direct required skill matches found.")

                if p_s.get("matched_preferred"):
                    st.markdown("<br>**⭐ Matched Preferred/Bonus Skills:**", unsafe_allow_html=True)
                    chips = "".join([f'<span class="skill-tag-bonus">+ {s.upper()}</span>' for s in p_s["matched_preferred"]])
                    st.markdown(chips, unsafe_allow_html=True)

            with c_s2:
                st.markdown("**❌ Missing Required Skills:**")
                if p_s["missing_required"]:
                    chips = "".join([f'<span class="skill-tag-missing">✗ {s.upper()}</span>' for s in p_s["missing_required"]])
                    st.markdown(chips, unsafe_allow_html=True)
                else:
                    st.success("All required skills mentioned in the JD were detected in the resume!")

                if p_s.get("candidate_extra"):
                    st.markdown("<br>**💡 Additional Candidate Skills (Bonus):**", unsafe_allow_html=True)
                    chips = "".join([f'<span class="skill-tag-bonus">{s.upper()}</span>' for s in p_s["candidate_extra"][:8]])
                    st.markdown(chips, unsafe_allow_html=True)

        with tab_exp:
            p_e = report["pillars"]["experience_relevance"]
            st.subheader(f"Experience Relevance Score: {p_e['score']}%")
            
            e_col1, e_col2, e_col3 = st.columns(3)
            with e_col1:
                st.metric("Candidate Tenure", f"{p_e['candidate_years']} yrs", delta=f"{round(p_e['candidate_years'] - p_e['required_years'], 1)} vs req")
            with e_col2:
                st.metric("Required Minimum", f"{p_e['required_years']} yrs")
            with e_col3:
                st.metric("Title / Role Match", f"{p_e['title_relevance_score']}%")

            if p_e["meets_experience_threshold"]:
                st.success(f"Candidate meets or exceeds the required tenure threshold of {p_e['required_years']} years.")
            else:
                st.warning(f"Candidate has approximately {p_e['candidate_years']} years of experience, which is below the desired {p_e['required_years']} years.")

        with tab_edu:
            p_ed = report["pillars"]["education_match"]
            st.subheader(f"Education & Credentials Score: {p_ed['score']}%")
            
            ed_col1, ed_col2 = st.columns(2)
            with ed_col1:
                st.write(f"**Required Education:** {p_ed['required_education']}")
                st.write(f"**Candidate Education:** {p_ed['candidate_education']}")
                if p_ed["meets_education_req"]:
                    st.success("Candidate satisfies baseline academic qualifications.")
                else:
                    st.info("Candidate holds alternative or partial academic qualifications.")

            with ed_col2:
                st.write("**Professional Certifications Found:**")
                if p_ed["certifications_found"]:
                    for cert in p_ed["certifications_found"]:
                        st.markdown(f"- 🏅 **{cert}**")
                else:
                    st.write("No major standardized certifications identified.")

        with tab_qa:
            st.subheader("Targeted Interview Questions for Hiring Team")
            st.write("These questions are dynamically generated based on candidate's exact profile gaps and core strengths:")
            for idx, q in enumerate(report["interview_questions"], 1):
                with st.expander(f"Q{idx}: {q['category']}", expanded=True):
                    st.markdown(f"**Question:** {q['question']}")
                    st.caption(f"🎯 **Evaluation Objective:** {q['focus']}")

        with tab_ai:
            st.subheader("Google Gemini Executive Synthesis")
            if ai_synthesis:
                st.markdown(ai_synthesis)
            else:
                st.info("To see real-time Google Gemini LLM reasoning and tailored recruiter narratives, add your API key to `.streamlit/secrets.toml`:\n\n```toml\nAI_API_KEY = \"your_gemini_api_key\"\n```")
                st.markdown("**Offline Strengths Analysis:**")
                for s in report["strengths"]:
                    st.markdown(f"- ✅ {s}")
                st.markdown("**Offline Flags & Gaps:**")
                for f in report["critical_flags"]:
                    st.markdown(f"- ⚠️ {f}")

        # Recruiter Markdown Export
        st.markdown("---")
        st.subheader("📄 Export Recruiter Report")
        md_text = agent.format_markdown_summary(report)
        st.download_button(
            label="📥 Download Candidate Screening Report (Markdown)",
            data=md_text,
            file_name=f"{report['candidate_name'].replace(' ', '_')}_Screening_Report.md",
            mime="text/markdown"
        )
