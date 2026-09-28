import json
import os
import sys

# Add the backend dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

EMAIL = "admin@example.com"
PASSWORD = "Admin123!"

def main():
    print("Logging in...")
    # Login
    login_data = {"email": EMAIL, "password": PASSWORD}
    res = client.post("/api/v1/auth/login", json=login_data)
    if not res.is_success:
        print("Login failed:", res.text)
        return
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Login successful.")

    # Upload Resume
    print("\nUploading Resume...")
    resume_path = r"C:\Users\pinak\Downloads\PINAKI_CHOUDHURI_RESUME_REVISED.pdf"
    with open(resume_path, "rb") as f:
        files = {"file": ("PINAKI_CHOUDHURI_RESUME_REVISED.pdf", f, "application/pdf")}
        res = client.post("/api/v1/resumes/upload", headers=headers, files=files)
        
    if not res.is_success:
        print("Upload failed:", res.text)
        return
        
    resume_data = res.json()
    resume_id = resume_data["public_id"]
    print(f"Resume uploaded. ID: {resume_id}")
    print("Resume status:", resume_data["status"])
    print("Predicted Domain:", resume_data.get("predicted_domain"))
    print("Skills extracted:", len(resume_data.get("extracted_skills", [])))
    
    # Print a few skills
    skills = resume_data.get("extracted_skills", [])
    if skills:
        print("Sample skills:", [s["canonical_name"] for s in skills[:5]])

    # Create Job
    print("\nCreating Job...")
    job_data = {
        "title": "Software Engineer (Full Stack)",
        "department": "Engineering",
        "description": "Looking for an experienced software engineer with Python, Machine Learning, and Web technologies.",
        "domain": "Engineering",
        "requirements": [
            {"skill_name": "Python", "is_required": True, "weight": 5, "notes": "Core programming language"},
            {"skill_name": "Machine Learning", "is_required": True, "weight": 4, "notes": "AI background"},
            {"skill_name": "Data Analytics", "is_required": False, "weight": 3, "notes": "Analytics"}
        ]
    }
    res = client.post("/api/v1/jobs", headers=headers, json=job_data)
    if not res.is_success:
        print("Job creation failed:", res.text)
        return
        
    job = res.json()
    job_id = job["public_id"]
    print(f"Job created. ID: {job_id}")

    # Screen Resume against Job
    print("\nScreening Resume against Job...")
    res = client.post(f"/api/v1/screening/{job_id}/match/{resume_id}", headers=headers)
    if not res.is_success:
        print("Screening failed:", res.text)
        return
        
    match_result = res.json()
    print("Screening successful.")
    print("Relevance Score:", match_result["relevance_score"])
    print("Required Skill Coverage:", match_result["required_skill_coverage"])
    print("Combined Skill Match:", match_result["combined_skill_match"])
    print("\nScore Breakdown:")
    print(json.dumps(match_result["score_breakdown"], indent=2))
    
    print("\nMatched Required Skills:", match_result["matched_required_skills"])
    print("Missing Required Skills:", match_result["missing_required_skills"])

if __name__ == "__main__":
    main()
