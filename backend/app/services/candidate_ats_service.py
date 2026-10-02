from typing import List, Dict, Any, Optional
import re
import math
from app.schemas.candidate import (
    CandidateATSAnalysisResponse,
    ImprovementPriority,
    SectionAnalysis,
    JobAlignment,
    ContactInfo,
    SkillDetail,
    ExperienceDetail,
    FormattingCheck,
)
from app.services.ats_analyzer_service import analyze_ats_compatibility, ESSENTIAL_SECTIONS
from app.services.skill_service import match_skills
from app.services.matching_service import compute_hybrid_match

ACTION_VERB_SET = {
    "architected", "built", "spearheaded", "engineered", "developed", "orchestrated",
    "implemented", "designed", "optimized", "managed", "led", "created", "refactored",
    "scaled", "automated", "delivered", "deployed", "reduced", "increased", "accelerated",
    "integrated", "pioneered", "championed", "overhauled", "mentored", "configured"
}

WEAK_PHRASES_SET = {
    "worked on", "helped with", "responsible for", "assisted", "handled", "participated in",
    "did", "was involved in", "helped to", "duties included"
}

SKILL_CATEGORY_MAP = {
    "Languages": {"python", "javascript", "typescript", "java", "c++", "c#", "go", "rust", "ruby", "php", "sql", "html", "css", "bash", "shell", "kotlin", "swift", "r", "scala"},
    "Frameworks & Libraries": {"react", "react.js", "node", "node.js", "fastapi", "flask", "django", "spring", "express", "angular", "vue", "next.js", "pytorch", "tensorflow", "pandas", "numpy", "scikit-learn", "scikit", "keras", "tailwind", "bootstrap"},
    "DevOps & Infrastructure": {"aws", "azure", "gcp", "docker", "kubernetes", "k8s", "terraform", "ansible", "jenkins", "ci/cd", "linux", "nginx", "helm", "prometheus", "grafana", "git", "github", "gitlab"},
    "Databases & Storage": {"postgresql", "postgres", "mysql", "mongodb", "redis", "sqlite", "elasticsearch", "dynamodb", "snowflake", "oracle", "cassandra"},
    "Data Science & AI": {"machine learning", "deep learning", "nlp", "computer vision", "llm", "llms", "rag", "scikit-learn", "opencv", "data pipelines", "neural networks"},
    "Software Architecture & Methodology": {"microservices", "rest", "restful", "rest api", "graphql", "system design", "agile", "scrum", "oop", "tdd", "ci/cd", "distributed systems"}
}

def analyze_candidate_resume(resume_text: str, job_description: Optional[str] = None) -> CandidateATSAnalysisResponse:
    text = resume_text.strip()
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    words = text.split()
    word_count = len(words)
    
    # 1. Base ATS Analysis
    ats_result = analyze_ats_compatibility(text)
    
    # 2. Contact Info Extraction
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    phone_match = re.search(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\+?\d{1,3}[-.\s]?\d{3,4}[-.\s]?\d{4}", text)
    linkedin_match = re.search(r"linkedin\.com/in/[\w\-]+", text, re.IGNORECASE)
    github_match = re.search(r"github\.com/[\w\-]+", text, re.IGNORECASE)
    location_match = re.search(r"\b([A-Z][a-zA-Z\s]+,\s*(?:[A-Z]{2}|[A-Z][a-zA-Z\s]+))\b", text)
    
    extracted_name = None
    for line in lines[:5]:
        if not re.search(r"@|\d{5,}|http|www|linkedin|github", line, re.IGNORECASE) and len(line) < 40:
            extracted_name = line
            break
            
    contact_info = ContactInfo(
        name=extracted_name,
        email=email_match.group(0) if email_match else None,
        phone=phone_match.group(0) if phone_match else None,
        linkedin=linkedin_match.group(0) if linkedin_match else None,
        github=github_match.group(0) if github_match else None,
        location=location_match.group(1) if location_match else None,
    )

    # 3. Skill Extraction & Categorization
    extracted_skills = match_skills(text)
    detected_skill_names = [s.canonical_name for s in extracted_skills]
    
    skill_categories: Dict[str, List[str]] = {}
    skill_details: List[SkillDetail] = []
    
    for s in extracted_skills:
        name_lower = s.canonical_name.lower()
        matched_cat = "Tools & Core Concepts"
        for cat, kw_set in SKILL_CATEGORY_MAP.items():
            if name_lower in kw_set or any(kw in name_lower for kw in kw_set):
                matched_cat = cat
                break
        
        freq = len(re.findall(r"\b" + re.escape(s.canonical_name) + r"\b", text, re.IGNORECASE))
        freq = max(1, freq)
        
        skill_categories.setdefault(matched_cat, []).append(s.canonical_name)
        skill_details.append(SkillDetail(
            name=s.canonical_name,
            category=matched_cat,
            domain=s.domain or "General",
            frequency=freq
        ))

    # Deduplicate skill categories
    for cat in skill_categories:
        skill_categories[cat] = list(dict.fromkeys(skill_categories[cat]))

    # 4. Experience & Bullet / Metric Analysis
    action_verbs_found = []
    weak_verbs_found = []
    
    words_lower = [w.lower().strip("•-*,.;:()") for w in words]
    for w in set(words_lower):
        if w in ACTION_VERB_SET:
            action_verbs_found.append(w.capitalize())
            
    for phrase in WEAK_PHRASES_SET:
        if phrase in text.lower():
            weak_verbs_found.append(phrase)
            
    metric_matches = re.findall(
        r"\b\d+(?:\.\d+)?%\b|\$\d+(?:\.\d+)?[kKM]?|\b\d+\s*(?:x|k|M|users|clients|ms|sec|requests|tps|fps)\b",
        text,
        re.IGNORECASE
    )
    metrics_found = list(dict.fromkeys(metric_matches))
    
    bullet_lines = [l for l in lines if l.startswith(("•", "-", "*", "1.", "2.", "3.", "4.", "5.")) or len(l) > 30]
    bullet_count = len(bullet_lines)
    avg_bullet_len = round(sum(len(l) for l in bullet_lines) / max(1, bullet_count), 1)
    
    experience_analysis = ExperienceDetail(
        total_entries=max(1, bullet_count // 3),
        action_verbs_found=action_verbs_found[:10],
        weak_verbs_found=weak_verbs_found[:5],
        metrics_found=metrics_found[:10],
        bullet_count=bullet_count,
        avg_bullet_length=avg_bullet_len,
    )

    # 5. Formatting & ATS Parsability Check
    formatting_issues = []
    non_ascii_count = len(re.findall(r"[^\x00-\x7F]", text))
    if non_ascii_count > 20:
        formatting_issues.append(f"Contains {non_ascii_count} non-standard symbol characters. Use standard bullets.")
    if word_count < 200:
        formatting_issues.append("Word count is under 200 words. Resume is too sparse for ATS scanners.")
    elif word_count > 1200:
        formatting_issues.append("Word count exceeds 1200 words. Excess length risks ATS parsing errors.")
        
    has_tables = "|" in text or "\t\t" in text
    if has_tables:
        formatting_issues.append("Table-like formatting detected. Many ATS parsers struggle to parse text in multi-column tables.")
        
    formatting = FormattingCheck(
        has_tables=has_tables,
        has_images=False,
        has_headers_or_footers=False,
        has_columns=has_tables,
        uses_standard_fonts=non_ascii_count <= 20,
        file_type_ok=True,
        issues=formatting_issues,
    )

    # 6. Section Health Analysis
    sections: Dict[str, SectionAnalysis] = {}
    for std_name, aliases in ESSENTIAL_SECTIONS.items():
        detected = std_name in ats_result.detected_sections
        section_text = ""
        if detected:
            for alias in aliases:
                if alias in text.upper():
                    idx = text.upper().find(alias)
                    section_text = text[idx:idx+800]
                    break
        sec_words = len(section_text.split())
        sec_bullets = len([l for l in section_text.split("\n") if l.strip().startswith(("•", "-", "*"))])
        sec_metrics = bool(re.search(r"\d+%|\$\d+|\d+\s*(?:k|M|users|clients|ms|sec)", section_text, re.IGNORECASE))
        sec_verbs = any(v.lower() in section_text.lower() for v in ACTION_VERB_SET)
        
        quality = "Good" if detected else "Missing"
        if detected and not sec_metrics and std_name == "WORK EXPERIENCE":
            quality = "Needs Quantified Results"
            
        rec = None
        if not detected:
            rec = f"Add a clearly labeled '{std_name}' header in ALL CAPS."
        elif quality == "Needs Quantified Results":
            rec = "Incorporate quantifiable metrics (e.g. percentages, user scale, speedups) into your experience bullets."
            
        sections[std_name] = SectionAnalysis(
            detected=detected,
            quality_signal=quality,
            recommendation=rec,
            word_count=sec_words,
            bullet_count=sec_bullets,
            has_metrics=sec_metrics,
            has_action_verbs=sec_verbs,
        )

    # 7. Job Alignment Analysis
    matched_skills = []
    missing_skills = []
    matched_keywords = []
    missing_keywords = []
    job_alignment = JobAlignment(job_provided=False)
    
    if job_description and job_description.strip():
        jd_skills = match_skills(job_description)
        required_job_skills = [(s.canonical_name, 1.0) for s in jd_skills[:len(jd_skills)//2]]
        preferred_job_skills = [(s.canonical_name, 1.0) for s in jd_skills[len(jd_skills)//2:]]
        
        match_res = compute_hybrid_match(
            required_skills=required_job_skills,
            preferred_skills=preferred_job_skills,
            candidate_skills=extracted_skills,
            resume_text=text,
            job_description=job_description
        )
        
        job_alignment = JobAlignment(
            job_provided=True,
            relevance_score=match_res.combined_match,
            domain_alignment=match_res.score_breakdown.get("signal_scores", {}).get("domain_alignment"),
            required_coverage=match_res.score_breakdown.get("signal_scores", {}).get("required_coverage"),
            preferred_coverage=match_res.score_breakdown.get("signal_scores", {}).get("preferred_coverage"),
            semantic_similarity=match_res.score_breakdown.get("signal_scores", {}).get("semantic_similarity"),
        )
        
        jd_skill_names = set(s.canonical_name for s in jd_skills)
        my_skill_names = set(detected_skill_names)
        
        matched_skills = list(jd_skill_names.intersection(my_skill_names))
        missing_skills = list(jd_skill_names.difference(my_skill_names))
        
        jd_words = set(w.lower() for w in re.findall(r"\w{5,}", job_description))
        resume_words = set(w.lower() for w in re.findall(r"\w{5,}", text))
        matched_keywords = list(jd_words.intersection(resume_words))[:15]
        missing_keywords = list(jd_words.difference(resume_words))[:10]

    # 8. Prioritized Recommendations
    priorities: List[ImprovementPriority] = []
    
    if missing_skills and job_description:
        priorities.append(ImprovementPriority(
            category="Job Skill Alignment",
            impact="HIGH IMPACT",
            issue=f"Missing {len(missing_skills)} target skills from the job description.",
            why_it_matters="ATS screeners rank candidates primarily by skill overlap with the job posting.",
            what_to_change=f"Add relevant missing skills to your Technical Skills or Experience section: {', '.join(missing_skills[:4])}.",
            example=f"e.g. Include '{missing_skills[0]}' under Technical Skills or describe a project where you applied it." if missing_skills else None
        ))
        
    for issue in ats_result.critical_issues:
        priorities.append(ImprovementPriority(
            category="Format & Structure",
            impact="HIGH IMPACT",
            issue=issue,
            why_it_matters="Formatting barriers prevent ATS parsers from correctly extracting your sections and work history.",
            what_to_change="Fix the header formatting or add standard section labels immediately.",
            example=None
        ))
        
    if weak_verbs_found:
        priorities.append(ImprovementPriority(
            category="Action Verb Optimization",
            impact="MEDIUM IMPACT",
            issue=f"Found passive or weak phrasing: '{', '.join(weak_verbs_found[:3])}'.",
            why_it_matters="Recruiters scan bullet points for strong ownership verbs to gauge leadership and execution strength.",
            what_to_change="Replace passive words with strong action verbs (Architected, Engineered, Spearheaded, Accelerated).",
            example=f"Before: '{weak_verbs_found[0]} python APIs' -> After: 'Engineered high-throughput Python APIs...'"
        ))

    if len(metrics_found) < 2:
        priorities.append(ImprovementPriority(
            category="Impact & Quantifiable Metrics",
            impact="HIGH IMPACT",
            issue="Fewer than 2 quantifiable metrics (percentages, scale, speedups, revenue) detected.",
            why_it_matters="Resumes with quantified metrics achieve up to 40% higher recruiter call-back rates.",
            what_to_change="Add concrete numbers or percentages to your experience bullet points.",
            example="Before: 'Built API endpoints' -> After: 'Architected REST API endpoints handling 50k requests/day with 99.9% uptime.'"
        ))
        
    if job_alignment.job_provided and job_alignment.relevance_score and job_alignment.relevance_score < 75:
        priorities.append(ImprovementPriority(
            category="Target Job Match",
            impact="HIGH IMPACT",
            issue=f"Overall Job Match Score is {job_alignment.relevance_score:.1f}/100.",
            why_it_matters="Scores below 75 typically fall into the lower percentile for automated screening filters.",
            what_to_change="Tailor your summary and experience bullet points to echo key responsibilities in the job posting.",
            example=None
        ))

    est_pages = max(1, math.ceil(word_count / 450))
    readability_grade = "Optimal (1-2 pages)"
    if word_count < 200:
        readability_grade = "Too Brief (<200 words)"
    elif word_count > 1200:
        readability_grade = "Overly Lengthy (>1200 words)"

    return CandidateATSAnalysisResponse(
        ats_score=ats_result.overall_score,
        compliance_category=ats_result.compliance_category,
        score_breakdown={
            "structure": ats_result.structure_score,
            "readability": ats_result.readability_score,
            "contact": ats_result.contact_score,
            "density": ats_result.density_score,
            "job_match": job_alignment.relevance_score or 0.0
        },
        contact_info=contact_info,
        detected_skills=detected_skill_names,
        skill_details=skill_details,
        skill_categories=skill_categories,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        matched_keywords=matched_keywords,
        missing_keywords=missing_keywords,
        sections=sections,
        experience_analysis=experience_analysis,
        formatting=formatting,
        improvement_priorities=priorities,
        recommendations=ats_result.actionable_recommendations,
        critical_issues=ats_result.critical_issues,
        warnings=ats_result.warnings,
        job_alignment=job_alignment,
        extraction={"char_count": len(text)},
        word_count=word_count,
        estimated_page_count=est_pages,
        readability_grade=readability_grade,
    )
