import json
from fastapi.testclient import TestClient
from api.main import app
from api.routes.progress import send_progress_update
from api.routes.auth import get_current_user
from api.models import JobStatusEnum, User
from datetime import datetime

app.dependency_overrides[get_current_user] = lambda: User(
    id=1,
    username="testuser",
    hashed_password="hash",
    role="user",
    created_at=datetime.utcnow(),
)
client = TestClient(app)


def test_progress_websocket_reports_detailed_status():
    job_id = "job123"
    with client.websocket_connect(f"/ws/progress/{job_id}") as websocket:
        send_progress_update(job_id, JobStatusEnum.FAILED_TIMEOUT.value)
        message = websocket.receive_json()
        assert message == {"status": JobStatusEnum.FAILED_TIMEOUT.value}
