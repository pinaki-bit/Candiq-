import requests
import sqlite3

r = requests.post('http://127.0.0.1:8000/api/v1/auth/login', json={'email':'admin@example.com','password':'changeme123'})
token = r.json()['access_token']
h = {'Authorization': f'Bearer {token}'}

# Get candidates from DB
conn = sqlite3.connect('resume_screening.db')
candidates = conn.execute('SELECT id, display_name, email FROM candidates').fetchall()
conn.close()
print(f'Candidates in DB: {len(candidates)}')

# Get jobs
jobs = requests.get('http://127.0.0.1:8000/api/v1/jobs/', headers=h).json()
print(f'Jobs: {len(jobs)}')

if jobs and candidates:
    job_id = jobs[0]['id']
    print(f'Seeding pipeline for job_id={job_id}')

    # Add first 4 candidates to pipeline
    for c in candidates[:4]:
        r = requests.post(
            f'http://127.0.0.1:8000/api/v1/pipeline/{job_id}/add',
            headers=h,
            json={'candidate_id': c[0], 'stage': 'applied'}
        )
        print(f'  Added candidate id={c[0]} name={c[1]}: {r.status_code}')

    # Fetch pipeline entries
    pipeline = requests.get(f'http://127.0.0.1:8000/api/v1/pipeline/{job_id}', headers=h).json()
    print(f'Pipeline entries: {len(pipeline)}')

    # Move some candidates forward
    if len(pipeline) >= 2:
        eid0 = pipeline[0]['id']
        eid1 = pipeline[1]['id']

        r = requests.patch(f'http://127.0.0.1:8000/api/v1/pipeline/{eid0}/move', headers=h, json={'to_stage': 'screened'})
        print(f'  Move {eid0} -> screened: {r.status_code}')

        r = requests.patch(f'http://127.0.0.1:8000/api/v1/pipeline/{eid1}/move', headers=h, json={'to_stage': 'screened'})
        print(f'  Move {eid1} -> screened: {r.status_code}')

        r = requests.patch(f'http://127.0.0.1:8000/api/v1/pipeline/{eid0}/move', headers=h, json={'to_stage': 'shortlisted'})
        print(f'  Move {eid0} -> shortlisted: {r.status_code}')

    # Final stats
    stats = requests.get(f'http://127.0.0.1:8000/api/v1/pipeline/stats/{job_id}', headers=h).json()
    print(f'Final stats: {stats["stage_counts"]}')
