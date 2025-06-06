import time

def test_backend_job_lifecycle(client, submit_stub_job):
    job_id = submit_stub_job(client)

    # Wait for job to be marked complete
    for _ in range(30):  # Extend time window to allow real subprocess
        status = client.get(f"/jobs/{job_id}").json()["status"]
        if status == "completed":
            break
        elif status == "failed":
            raise AssertionError(f"Job failed unexpectedly: {job_id}")
        time.sleep(0.5)

    # Transcript should exist
    resp = client.get(f"/transcript/{job_id}")
    assert resp.status_code == 200
    assert "stub transcript" in resp.text

    # Metadata should exist
    resp = client.get(f"/metadata/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["tokens"] == 2
