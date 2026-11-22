"""
core/evaluator.py
Multi-dimensional evaluation engine assessing:
1. Skill Alignment (Core vs Preferred skills)
2. Experience Relevance (Years, role title match, domain)
3. Education & Certifications Match
Produces composite Candidate Fit Score (0-100) and structured breakdown.
"""

import re
from typing import Dict, List, Set, Any, Tuple
from datetime import datetime


# Standard skills knowledge base with common aliases
SKILL_TAXONOMY = {
    # Data & Analytics
    "sql": ["sql", "structured query language", "tsql", "t-sql", "plsql", "pl/sql", "mysql", "postgresql", "postgres"],
    "python": ["python", "python3", "py"],
    "power bi": ["power bi", "powerbi", "dax", "power query"],
    "tableau": ["tableau", "tableau desktop", "tableau server"],
    "excel": ["excel", "advanced excel", "vba", "macros", "vlookup"],
    "etl": ["etl", "elt", "data pipeline", "data pipelines", "data warehousing", "dwh"],
    "dbt": ["dbt", "data build tool"],
    "snowflake": ["snowflake", "snowsql"],
    "bigquery": ["bigquery", "google bigquery", "bq"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "spark": ["spark", "apache spark", "pyspark"],
    "airflow": ["airflow", "apache airflow"],
    "looker": ["looker", "lookml"],
    
    # Software Engineering & Languages
    "javascript": ["javascript", "js", "ecmascript"],
    "typescript": ["typescript", "ts"],
    "react": ["react", "react.js", "reactjs"],
    "node.js": ["node.js", "nodejs", "node"],
    "html/css": ["html", "html5", "css", "css3", "sass", "tailwind", "bootstrap"],
    "java": ["java", "j2ee", "spring", "spring boot"],
    "c#": ["c#", "csharp", ".net", "dotnet", "asp.net"],
    "c++": ["c++", "cpp"],
    "go": ["golang", "go"],
    "rest api": ["rest", "restful", "rest api", "apis", "api development", "fastapi", "flask", "django"],
    "git": ["git", "github", "gitlab", "version control"],
    
    # Cloud & DevOps
    "aws": ["aws", "amazon web services", "s3", "ec2", "lambda", "redshift"],
    "gcp": ["gcp", "google cloud", "google cloud platform"],
    "azure": ["azure", "microsoft azure", "azure data factory", "synapse"],
    "docker": ["docker", "containerization", "containers"],
    "kubernetes": ["kubernetes", "k8s"],
    "ci/cd": ["ci/cd", "continuous integration", "jenkins", "github actions"],
    "linux": ["linux", "bash", "shell scripting", "unix"],

    # AI & Machine Learning
    "machine learning": ["machine learning", "ml", "scikit-learn", "supervised learning"],
    "deep learning": ["deep learning", "tensorflow", "pytorch", "keras", "neural networks"],
    "nlp": ["nlp", "natural language processing", "llm", "llms", "genai", "generative ai", "langchain"],

    # Process & Domain
    "agile": ["agile", "scrum", "sprints", "jira", "kanban"],
    "data modeling": ["data modeling", "star schema", "dimensional modeling", "snowflake schema"],
    "sla monitoring": ["sla", "sla monitoring", "incident management", "triage", "production support"],
    "data quality": ["data quality", "data reconciliation", "validation", "data validation", "qa"]
}

EDUCATION_LEVELS = {
    "doctorate": 5,
    "phd": 5,
    "master": 4,
    "m.tech": 4,
    "m.s.": 4,
    "ms": 4,
    "mba": 4,
    "mca": 4,
    "post graduate": 4,
    "bachelor": 3,
    "b.tech": 3,
    "b.e.": 3,
    "b.s.": 3,
    "bs": 3,
    "bca": 3,
    "b.sc": 3,
    "undergraduate": 3,
    "associate": 2,
    "diploma": 2,
    "high school": 1
}

CERTIFICATIONS_LIST = [
    "aws certified", "azure certified", "gcp professional", "google cloud certified",
    "power bi certified", "pl-300", "pmp", "scrum master", "csm", "databricks certified",
    "snowflake snowpro", "terraform associate", "cissp", "comptia"
]


class ResumeEvaluator:
    """Evaluates resume against job description across 3 key pillars."""

    def __init__(self, weights: Dict[str, float] = None):
        # Default weights: Skills 40%, Experience 40%, Education 20%
        self.weights = weights or {"skills": 0.40, "experience": 0.40, "education": 0.20}

    # ==========================================
    # Pillar 1: Skill Alignment
    # ==========================================
    def extract_skills(self, text: str) -> Set[str]:
        """Identifies skills present in text using the skill taxonomy."""
        text_lower = " " + text.lower() + " "
        found_skills = set()

        for canonical_name, aliases in SKILL_TAXONOMY.items():
            for alias in aliases:
                # Use word boundary checking
                pattern = r"(?:^|[\s,;./\(\)\[\]\|'\"])" + re.escape(alias) + r"(?:$|[\s,;./\(\)\[\]\|'\"])"
                if re.search(pattern, text_lower):
                    found_skills.add(canonical_name)
                    break
        return found_skills

    def partition_jd_skills(self, jd_text: str) -> Tuple[Set[str], Set[str]]:
        """Separates required vs preferred skills from Job Description."""
        req_pattern = re.compile(
            r"(?:requirements|required\s+skills|minimum\s+qualifications|what\s+you(?:'ll)?\s+need|must\s+have|basic\s+qualifications)(.*?)(?=(?:preferred|bonus|nice\s+to\s+have|plus|benefits|about\s+us|$))",
            re.I | re.DOTALL
        )
        pref_pattern = re.compile(
            r"(?:preferred\s+qualifications|nice\s+to\s+have|bonus\s+points?|preferred\s+skills|pluses)(.*?)(?=(?:benefits|about\s+us|what\s+we\s+offer|$))",
            re.I | re.DOTALL
        )

        req_match = req_pattern.search(jd_text)
        pref_match = pref_pattern.search(jd_text)

        all_skills = self.extract_skills(jd_text)

        if req_match:
            req_text = req_match.group(1)
            required_skills = self.extract_skills(req_text)
        else:
            required_skills = set()

        if pref_match:
            pref_text = pref_match.group(1)
            preferred_skills = self.extract_skills(pref_text)
        else:
            preferred_skills = set()

        # If partition was incomplete, assign remaining to required
        if not required_skills and not preferred_skills:
            required_skills = all_skills
        else:
            # Clean up overlaps
            preferred_skills = preferred_skills - required_skills
            # Any remaining unassigned skills in JD go into required
            remaining = all_skills - (required_skills | preferred_skills)
            required_skills.update(remaining)

        return required_skills, preferred_skills

    def evaluate_skills(self, jd_text: str, resume_text: str) -> Dict[str, Any]:
        """Calculates Skill Alignment score and matched/missing itemization."""
        required_skills, preferred_skills = self.partition_jd_skills(jd_text)
        candidate_skills = self.extract_skills(resume_text)

        matched_required = required_skills.intersection(candidate_skills)
        missing_required = required_skills - candidate_skills

        matched_preferred = preferred_skills.intersection(candidate_skills)
        missing_preferred = preferred_skills - candidate_skills

        extra_skills = candidate_skills - (required_skills | preferred_skills)

        # Scoring: 75% weight on required, 25% on preferred
        if required_skills:
            req_score = (len(matched_required) / len(required_skills)) * 100
        else:
            req_score = 100.0

        if preferred_skills:
            pref_score = (len(matched_preferred) / len(preferred_skills)) * 100
            score = (req_score * 0.75) + (pref_score * 0.25)
        else:
            # If no preferred skills specified, score is directly based on required skills
            score = req_score

        # Add slight boost for valuable extra skills (up to +5%)
        if extra_skills and score < 95:
            score = min(100.0, score + min(5.0, len(extra_skills) * 0.8))

        return {
            "score": round(score, 1),
            "matched_required": sorted(list(matched_required)),
            "missing_required": sorted(list(missing_required)),
            "matched_preferred": sorted(list(matched_preferred)),
            "missing_preferred": sorted(list(missing_preferred)),
            "candidate_extra": sorted(list(extra_skills)),
            "total_jd_skills": len(required_skills | preferred_skills),
            "total_candidate_skills": len(candidate_skills)
        }

    # ==========================================
    # Pillar 2: Experience Relevance
    # ==========================================
    def extract_required_experience_years(self, jd_text: str) -> float:
        """Extracts required minimum years of experience from JD."""
        patterns = [
            r"(\d+(?:\.\d+)?)\s*(?:\+|-|\s+to\s+\d+)?\s*(?:years?|yrs?)(?:\s+of)?(?:\s+relevant)?\s+experience",
            r"minimum\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",
            r"at\s+least\s+(\d+(?:\.\d+)?)\s*(?:years?|yrs?)"
        ]
        years_found = []
        for p in patterns:
            for match in re.finditer(p, jd_text, re.I):
                try:
                    val = float(match.group(1))
                    if 0 < val <= 25:
                        years_found.append(val)
                except ValueError:
                    pass
        return min(years_found) if years_found else 2.0  # Default 2 years if unstated

    def extract_candidate_experience_years(self, resume_text: str) -> float:
        """Estimates candidate's total years of experience from resume."""
        # 1. Check explicit summary claims like '2.4 years of experience', '5+ years'
        explicit_patterns = [
            r"(\d+(?:\.\d+)?)\s*(?:\+)?\s*(?:years?|yrs?)(?:\s+of)?(?:\s+experience|\s+working|\s+in)",
            r"experience:\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)"
        ]
        for p in explicit_patterns:
            m = re.search(p, resume_text, re.I)
            if m:
                try:
                    val = float(m.group(1))
                    if 0.5 <= val <= 40:
                        return val
                except ValueError:
                    pass

        # 2. Date ranges extraction: e.g. Sep 2023 - Jan 2026 or 2021 - 2024
        date_pattern = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)?\.?\s*(\d{4})\s*(?:-|–|to)\s*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)?\.?\s*(\d{4}|present|current)"
        ranges = re.findall(date_pattern, resume_text, re.I)
        current_year = datetime.now().year

        total_years = 0.0
        for start_str, end_str in ranges:
            try:
                start_yr = int(start_str)
                end_yr = current_year if end_str.lower() in ["present", "current"] else int(end_str)
                if 1990 <= start_yr <= current_year and end_yr >= start_yr:
                    dur = max(0.5, end_yr - start_yr)
                    total_years += dur
            except ValueError:
                pass

        return min(total_years, 35.0) if total_years > 0 else 1.0

    def calculate_title_similarity(self, jd_text: str, resume_text: str) -> float:
        """Measures keyword alignment between job title and candidate's past titles."""
        # Common tech titles tokens
        title_tokens = [
            "analytics engineer", "bi analyst", "business intelligence", "data engineer",
            "data analyst", "software engineer", "frontend developer", "backend developer",
            "full stack", "fullstack", "devops engineer", "product manager", "machine learning engineer",
            "data scientist", "qa engineer", "system architect"
        ]
        jd_lower = jd_text[:500].lower()  # First 500 chars usually have the title
        resume_lower = resume_text.lower()

        jd_titles = [t for t in title_tokens if t in jd_lower]
        if not jd_titles:
            # Fallback: scan whole JD
            jd_titles = [t for t in title_tokens if t in jd_text.lower()]

        if not jd_titles:
            return 80.0  # Neutral baseline if title is unconventional

        res_matches = [t for t in jd_titles if t in resume_lower]
        if res_matches:
            return 100.0  # Direct title match

        # Check partial overlap (e.g. 'analyst' in 'bi analyst' vs 'data analyst')
        jd_words = set(" ".join(jd_titles).split())
        resume_title_section = resume_text[:1200].lower()
        matched_words = [w for w in jd_words if len(w) > 3 and w in resume_title_section]
        if matched_words:
            return 75.0

        return 45.0

    def evaluate_experience(self, jd_text: str, resume_text: str) -> Dict[str, Any]:
        """Calculates Experience Relevance score."""
        req_years = self.extract_required_experience_years(jd_text)
        cand_years = self.extract_candidate_experience_years(resume_text)
        title_score = self.calculate_title_similarity(jd_text, resume_text)

        # Years ratio scoring
        if cand_years >= req_years:
            years_score = 100.0
        else:
            # Proportional with soft floor
            ratio = cand_years / req_years
            years_score = max(20.0, ratio * 90.0)

        # Experience composite: 60% duration match, 40% role relevance
        composite_exp_score = round((0.60 * years_score) + (0.40 * title_score), 1)

        return {
            "score": composite_exp_score,
            "required_years": req_years,
            "candidate_years": round(cand_years, 1),
            "years_score": round(years_score, 1),
            "title_relevance_score": round(title_score, 1),
            "meets_experience_threshold": cand_years >= req_years
        }

    # ==========================================
    # Pillar 3: Education & Certifications
    # ==========================================
    def extract_highest_education(self, text: str) -> Tuple[str, int]:
        """Determines highest degree found in text."""
        text_lower = text.lower()
        highest_rank = 0
        highest_label = "Not specified"

        for term, rank in EDUCATION_LEVELS.items():
            pattern = r"\b" + re.escape(term) + r"\b"
            if re.search(pattern, text_lower):
                if rank > highest_rank:
                    highest_rank = rank
                    highest_label = term.title()

        return highest_label, highest_rank

    def extract_certifications(self, text: str) -> List[str]:
        """Extracts recognizable professional certifications."""
        text_lower = text.lower()
        found = []
        for cert in CERTIFICATIONS_LIST:
            if cert in text_lower:
                found.append(cert.title())
        return found

    def evaluate_education(self, jd_text: str, resume_text: str) -> Dict[str, Any]:
        """Calculates Education Match score and certification bonus."""
        jd_edu_label, jd_edu_rank = self.extract_highest_education(jd_text)
        if jd_edu_rank == 0:
            # Default to Bachelor's if JD doesn't explicitly state
            jd_edu_rank = 3
            jd_edu_label = "Bachelor's (assumed standard)"

        cand_edu_label, cand_edu_rank = self.extract_highest_education(resume_text)
        if cand_edu_rank == 0:
            # Check for generic indicators like "University", "College", "Degree"
            if re.search(r"\b(university|college|institute|graduated|bachelor|degree)\b", resume_text, re.I):
                cand_edu_rank = 3
                cand_edu_label = "Degree (implied)"
            else:
                cand_edu_rank = 1
                cand_edu_label = "Unspecified"

        certs = self.extract_certifications(resume_text)

        # Baseline degree match score
        if cand_edu_rank >= jd_edu_rank:
            base_score = 85.0
            if cand_edu_rank > jd_edu_rank:
                base_score = 95.0  # Advanced degree bonus
        elif cand_edu_rank == jd_edu_rank - 1:
            base_score = 65.0  # One tier below (e.g. Diploma vs Bachelor's)
        else:
            base_score = 45.0

        # Certification bonus (+5% per cert, max +15%)
        cert_bonus = min(15.0, len(certs) * 7.5)
        final_score = min(100.0, base_score + cert_bonus)

        return {
            "score": round(final_score, 1),
            "required_education": jd_edu_label,
            "candidate_education": cand_edu_label,
            "meets_education_req": cand_edu_rank >= jd_edu_rank,
            "certifications_found": certs
        }

    # ==========================================
    # Composite Fit Score & Final Report
    # ==========================================
    def evaluate(self, jd_text: str, resume_text: str) -> Dict[str, Any]:
        """Runs complete 3-pillar evaluation and builds fit score."""
        skills_res = self.evaluate_skills(jd_text, resume_text)
        exp_res = self.evaluate_experience(jd_text, resume_text)
        edu_res = self.evaluate_education(jd_text, resume_text)

        fit_score = round(
            (self.weights["skills"] * skills_res["score"]) +
            (self.weights["experience"] * exp_res["score"]) +
            (self.weights["education"] * edu_res["score"]),
            1
        )

        # Determine Recommendation Tier
        if fit_score >= 80.0:
            verdict = "STRONG FIT"
            recommendation = "Recommend Fast-Track Technical Interview"
            tier_class = "success"
        elif fit_score >= 60.0:
            verdict = "MODERATE FIT"
            recommendation = "Recommend Recruiter / Hiring Manager Screening"
            tier_class = "warning"
        else:
            verdict = "LOW FIT"
            recommendation = "Pass / Keep on File for Alternative Openings"
            tier_class = "danger"

        return {
            "candidate_fit_score": fit_score,
            "verdict": verdict,
            "recommendation": recommendation,
            "tier_class": tier_class,
            "pillars": {
                "skill_alignment": skills_res,
                "experience_relevance": exp_res,
                "education_match": edu_res
            },
            "weights_used": self.weights
        }
