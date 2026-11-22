"""
core/screener.py
Agent coordinator that runs document extraction, multi-pillar evaluation,
generates actionable gap analyses, key strengths, risk flags, and tailored technical interview questions.
"""

import re
from typing import Dict, Any, List, Optional
from core.extractor import DocumentExtractor
from core.evaluator import ResumeEvaluator


class ResumeScreeningAgent:
    """End-to-end intelligent agent for resume screening."""

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.evaluator = ResumeEvaluator(weights=weights)

    def extract_candidate_name(self, resume_text: str) -> str:
        """Attempts to extract candidate name from the top lines of resume."""
        lines = [line.strip() for line in resume_text.split("\n") if line.strip()]
        for line in lines[:5]:
            # Look for a 2-4 word capitalized string without numbers or special chars
            clean = re.sub(r"[^\w\s]", "", line)
            words = clean.split()
            if 2 <= len(words) <= 4 and all(w.isalpha() for w in words):
                # Filter out obvious false positives like 'RESUME', 'CURRICULUM VITAE', 'CONTACT'
                if not re.search(r"\b(resume|curriculum|vitae|contact|phone|email|summary|profile)\b", clean, re.I):
                    return line
        return "Candidate"

    def generate_interview_questions(self, eval_result: Dict[str, Any], resume_text: str) -> List[Dict[str, str]]:
        """Generates targeted technical and behavioral interview questions based on screening gaps & strengths."""
        questions = []
        skills_data = eval_result["pillars"]["skill_alignment"]
        exp_data = eval_result["pillars"]["experience_relevance"]
        
        # 1. Questions targeting missing required skills
        missing_req = skills_data.get("missing_required", [])
        for skill in missing_req[:3]:  # Top 3 missing skills
            questions.append({
                "category": f"Skill Gap: {skill.upper()}",
                "focus": "Assessing adaptability or unlisted experience",
                "question": f"The role requires proficiency in {skill.title()}. While not prominently featured on your resume, have you worked with {skill.title()} or analogous frameworks in past projects? How quickly could you ramp up?"
            })

        # 2. Questions probing core matched skills
        matched_req = skills_data.get("matched_required", [])
        if "sql" in matched_req:
            questions.append({
                "category": "Core Competency: SQL & Data Architecture",
                "focus": "Query optimization and production data pipelines",
                "question": "Can you describe a complex SQL query or pipeline performance bottleneck you resolved? What indexing, partitioning, or execution plan tuning did you apply?"
            })
        if "python" in matched_req:
            questions.append({
                "category": "Core Competency: Python Automation",
                "focus": "Production scripting, exception handling, and testing",
                "question": "Walk us through an end-to-end Python script or automation workflow you developed. How did you structure error handling, logging, and automated execution?"
            })
        if "power bi" in matched_req or "tableau" in matched_req:
            questions.append({
                "category": "Core Competency: Business Intelligence & Reporting",
                "focus": "Data modeling, DAX/LOD calculations, and business impact",
                "question": "How do you approach designing a multi-table dimensional data model for high-performance dashboards? How do you ensure metric consistency across executive reporting?"
            })

        # 3. Experience & Scale questions
        if not exp_data.get("meets_experience_threshold", True):
            questions.append({
                "category": "Experience Depth & Seniority",
                "focus": "Evaluating velocity and project ownership",
                "question": f"This position typically looks for {exp_data['required_years']} years of experience, while your profile shows ~{exp_data['candidate_years']} years. Could you highlight 1-2 high-impact initiatives where you operated above your formal tenure?"
            })
        else:
            questions.append({
                "category": "Production Experience & Reliability",
                "focus": "Incident triage, SLA monitoring, and pre-flight validation",
                "question": "Tell us about a time when a critical reporting dashboard or data pipeline failed under SLA pressure. What was your root cause investigation and remediation process?"
            })

        return questions[:5]

    def generate_strengths_and_flags(self, eval_result: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Identifies top standout strengths and flagged risk factors."""
        strengths = []
        flags = []

        skills_data = eval_result["pillars"]["skill_alignment"]
        exp_data = eval_result["pillars"]["experience_relevance"]
        edu_data = eval_result["pillars"]["education_match"]

        # Strengths
        if skills_data["score"] >= 80:
            strengths.append(f"High technical alignment: Matches {len(skills_data['matched_required'])} required core competencies ({', '.join(skills_data['matched_required'][:4])}).")
        if skills_data.get("matched_preferred"):
            strengths.append(f"Brings desirable bonus skillsets: {', '.join(skills_data['matched_preferred'])}.")
        if exp_data["meets_experience_threshold"]:
            strengths.append(f"Meets or exceeds tenure requirement ({exp_data['candidate_years']} yrs vs {exp_data['required_years']} yrs required).")
        if exp_data["title_relevance_score"] >= 80:
            strengths.append("High title and domain relevance with previous work history.")
        if edu_data.get("certifications_found"):
            strengths.append(f"Professional credentials verified: {', '.join(edu_data['certifications_found'])}.")

        # Flags
        if skills_data.get("missing_required"):
            flags.append(f"Missing {len(skills_data['missing_required'])} core requirement(s): {', '.join(skills_data['missing_required'])}.")
        if not exp_data["meets_experience_threshold"]:
            flags.append(f"Experience gap: Candidate has ~{exp_data['candidate_years']} years vs {exp_data['required_years']} years desired.")
        if not edu_data["meets_education_req"]:
            flags.append(f"Education discrepancy: Role specifies {edu_data['required_education']}, candidate lists {edu_data['candidate_education']}.")

        if not strengths:
            strengths.append("Demonstrates foundational technical literacy with transferable skills.")
        if not flags:
            flags.append("No critical dealbreaker flags detected. Candidate fulfills baseline screening prerequisites.")

        return strengths, flags

    def screen(self, jd_text: str, resume_text: str) -> Dict[str, Any]:
        """Performs full screening evaluation on raw texts."""
        clean_jd = DocumentExtractor.normalize_text(jd_text)
        clean_resume = DocumentExtractor.normalize_text(resume_text)

        eval_res = self.evaluator.evaluate(clean_jd, clean_resume)
        candidate_name = self.extract_candidate_name(clean_resume)
        strengths, flags = self.generate_strengths_and_flags(eval_res)
        interview_questions = self.generate_interview_questions(eval_res, clean_resume)

        report = {
            "candidate_name": candidate_name,
            "overall_fit_score": eval_res["candidate_fit_score"],
            "verdict": eval_res["verdict"],
            "recommendation": eval_res["recommendation"],
            "tier_class": eval_res["tier_class"],
            "strengths": strengths,
            "critical_flags": flags,
            "interview_questions": interview_questions,
            "pillars": eval_res["pillars"],
            "weights": eval_res["weights_used"]
        }
        return report

    def format_markdown_summary(self, report: Dict[str, Any]) -> str:
        """Formats the screening report into a clean recruiter-ready Markdown summary."""
        p_skill = report["pillars"]["skill_alignment"]
        p_exp = report["pillars"]["experience_relevance"]
        p_edu = report["pillars"]["education_match"]

        md = f"""# Candidate Screening Report: {report['candidate_name']}

## Overall Verdict: {report['verdict']} ({report['overall_fit_score']}/100)
**Recommendation**: {report['recommendation']}

---

### 1. Pillar Score Breakdown
- **Skill Alignment Score**: {p_skill['score']}% (Weight: {int(report['weights']['skills']*100)}%)
  - *Matched Required*: {', '.join(p_skill['matched_required']) if p_skill['matched_required'] else 'None'}
  - *Missing Required*: {', '.join(p_skill['missing_required']) if p_skill['missing_required'] else 'None'}
  - *Matched Preferred*: {', '.join(p_skill['matched_preferred']) if p_skill['matched_preferred'] else 'None'}
- **Experience Relevance Score**: {p_exp['score']}% (Weight: {int(report['weights']['experience']*100)}%)
  - *Candidate Tenure*: {p_exp['candidate_years']} yrs (Required: {p_exp['required_years']} yrs)
  - *Title / Domain Match*: {p_exp['title_relevance_score']}%
- **Education & Certs Score**: {p_edu['score']}% (Weight: {int(report['weights']['education']*100)}%)
  - *Candidate Education*: {p_edu['candidate_education']} (Required: {p_edu['required_education']})
  - *Certifications*: {', '.join(p_edu['certifications_found']) if p_edu['certifications_found'] else 'None'}

---

### 2. Key Candidate Strengths
"""
        for s in report["strengths"]:
            md += f"- [x] {s}\n"

        md += "\n### 3. Critical Gaps & Risk Flags\n"
        for f in report["critical_flags"]:
            md += f"- [!] {f}\n"

        md += "\n### 4. Recommended Interview Questions\n"
        for idx, q in enumerate(report["interview_questions"], 1):
            md += f"{idx}. **[{q['category']}]** {q['question']}\n   *(Goal: {q['focus']})*\n"

        return md
