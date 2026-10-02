import requests
import sqlite3

r = requests.post('http://127.0.0.1:8000/api/v1/auth/login', json={'email':'admin@example.com','password':'changeme123'})
token = r.json()['access_token']
h = {'Authorization': f'Bearer {token}'}

jobs = requests.get('http://127.0.0.1:8000/api/v1/jobs/', headers=h).json()
if jobs:
    job_id = jobs[0]['id']
    conn = sqlite3.connect('resume_screening.db')
    candidates = conn.execute('SELECT id FROM candidates').fetchall()
    conn.close()
    
    if len(candidates) >= 2:
        cids = [c[0] for c in candidates[:2]]
        print(f'Comparing candidates: {cids} for job {job_id}')
        res = requests.post(f'http://127.0.0.1:8000/api/v1/compare/{job_id}', headers=h, json={'candidate_ids': cids})
        print(f'Status: {res.status_code}')
        if res.status_code == 200:
            data = res.json()
            print(f'Radar dimensions: {len(data["radar_chart"])}')
            print(f'Shared skills: {len(data["skill_overlap"]["shared_skills"])}')
            print(f'AI Summary: {data["ai_summary"][:100]}...')
        else:
            print(res.text)
