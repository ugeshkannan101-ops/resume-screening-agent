# Resume Screening Agent (Agent Template Pack)

An AI-driven resume screening agent that accepts a job description and candidate resume, evaluates them across three core pillars, and computes an explainable candidate fit score with actionable recommendations.

---

## 3-Pillar Evaluation Matrix

1. **Skill Alignment (40%)**:
   - Matches core required skills vs candidate skills.
   - Evaluates preferred/bonus skills.
   - Highlights matched skills (green tags), missing core skills (red tags), and candidate bonus skills.

2. **Experience Relevance (40%)**:
   - Parses minimum required tenure from JD (e.g. 2+ years).
   - Extracts candidate experience from resume.
   - Evaluates title and domain relevance.

3. **Education & Certifications Match (20%)**:
   - Verifies degree requirements (Bachelors, Masters, etc.).
   - Awards bonus for industry certifications (AWS, Power BI, Databricks, PMP, etc.).

---

## Quickstart

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Google Gemini (Free Tier)
Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`:
```toml
AI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
AI_MODEL = "gemini-1.5-flash"
AI_API_KEY = "YOUR_GEMINI_API_KEY"
```

### 3. Run the Streamlit Web Application
```bash
python -m streamlit run app.py
```
Open your browser at: `http://localhost:8501`

### 4. CLI Screening Runner
You can also run quick screenings directly in your terminal:
```bash
python screen_cli.py --jd samples/job_descriptions/analytics_engineer.txt --resume samples/resumes/analytics_engineer_ugesh.txt
```
