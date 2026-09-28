"""
backend/tests/test_load_stress.py

Phase 18: Load & Concurrency Stress Test Suite.
Verifies API response stability and clean exception handling under multi-worker load simulation.
"""

import threading
import pytest


def test_concurrent_api_stress_simulation(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    lock = threading.Lock()
    results = []

    def _worker_task(worker_id: int):
        # Health check liveness
        resp1 = client.get("/health")
        assert resp1.status_code == 200

        # ATS check with mutex lock for test client thread safety
        with lock:
            ats_payload = {
                "resume_text": f"Worker {worker_id} Candidate Resume text with Python, FastAPI, SQL, Docker, and PyTorch.",
                "job_title": "Senior AI Systems Engineer",
            }
            resp2 = client.post("/api/v1/resumes/ats-check", json=ats_payload, headers=headers)
            assert resp2.status_code == 200

            # ATS connection test
            conn_payload = {"provider": "mock"}
            resp3 = client.post("/api/v1/ats/test-connection", json=conn_payload, headers=headers)
            assert resp3.status_code == 200

            results.append(worker_id)

    threads = [threading.Thread(target=_worker_task, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 5
