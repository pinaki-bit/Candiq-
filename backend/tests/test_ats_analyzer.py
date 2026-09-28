"""
backend/tests/test_ats_analyzer.py

Unit test suite for Phase 10: ATS Compatibility Analyzer & Parser Compliance Suite.
"""

import pytest
from app.services.ats_analyzer_service import ATSAnalysisResult, analyze_ats_compatibility


def test_analyze_ats_compatibility_complete_resume():
    text = (
        "SARAH CONNOR\nsarah.connor@example.com | (555) 019-2834 | San Francisco, CA | linkedin.com/in/sconnor\n\n"
        "PROFESSIONAL SUMMARY\n"
        "Results-oriented Senior Cloud Architect with over 8 years of proven experience designing, deploying, and maintaining "
        "high-availability AWS cloud infrastructure and microservice architectures. Expert in container orchestration, "
        "infrastructure-as-code, automated CI/CD pipelines, and enterprise security compliance.\n\n"
        "WORK EXPERIENCE\n"
        "Lead Infrastructure Engineer — Cyberdyne Systems (2020 – Present)\n"
        "• Architected multi-region Kubernetes clusters handling 500k active requests per minute, achieving 99.99% uptime availability.\n"
        "• Spearheaded comprehensive CI/CD automation with Terraform, Docker, and Python, saving $150k in operational costs annually.\n"
        "• Engineered automated backup and disaster recovery mechanisms across multiple cloud regions, reducing RTO by 75%.\n"
        "• Mentored junior cloud engineers and established engineering best practices for container security and secrets management.\n\n"
        "Cloud Systems Engineer — Skynet Solutions (2016 – 2020)\n"
        "• Managed enterprise Linux server deployments and optimized database performance across distributed PostgreSQL instances.\n"
        "• Built automated monitoring and alerting dashboards using Prometheus and Grafana, lowering mean time to resolution by 40%.\n"
        "• Refactored monolithic backend services into microservices, improving deployment frequency threefold.\n\n"
        "TECHNICAL SKILLS\n"
        "AWS, Kubernetes, Terraform, Docker, Python, Linux, CI/CD, Bash, Git, PostgreSQL, Redis, Microservices, Prometheus, Security.\n\n"
        "EDUCATION\n"
        "B.S. in Electrical Engineering and Computer Science — Massachusetts Institute of Technology (2012 – 2016)\n"
    )
    result = analyze_ats_compatibility(text)
    
    assert isinstance(result, ATSAnalysisResult)
    assert result.overall_score >= 85.0
    assert result.compliance_category == "EXCELLENT"
    assert "WORK EXPERIENCE" in result.detected_sections
    assert len(result.critical_issues) == 0


def test_analyze_ats_compatibility_sparse_resume():
    text = "Just a quick note. I worked on some projects using code."
    result = analyze_ats_compatibility(text)
    
    assert result.overall_score < 60.0
    assert result.compliance_category in ("CRITICAL", "NEEDS_IMPROVEMENT")
    assert len(result.missing_essential_sections) > 0
    assert len(result.critical_issues) > 0


def test_api_ats_check_endpoint(client, hr_token):
    headers = {"Authorization": f"Bearer {hr_token}"}
    payload = {
        "resume_text": (
            "JOHN DOE\njohn@example.com | (555) 123-4567\n\n"
            "WORK EXPERIENCE\nDeveloped REST APIs in Python and FastAPI.\n\n"
            "TECHNICAL SKILLS\nPython, FastAPI, SQL, Git.\n\n"
            "EDUCATION\nB.S. Computer Science\n"
        )
    }
    
    response = client.post("/api/v1/resumes/ats-check", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "overall_score" in data
    assert "structure_score" in data
    assert "compliance_category" in data
    assert "detected_sections" in data
