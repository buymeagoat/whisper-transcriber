"""
Test suite for API pagination functionality (Issue #009).

This module tests cursor-based pagination, filtering, and edge cases
for job listing endpoints with comprehensive validation.
"""

import pytest
import json
import base64
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app, get_db, Base, Job, User
from app.pagination import PaginationRequest, JobQueryFilters, CursorGenerator
from app.schemas import JobResponseSchema, PaginatedJobsResponseSchema

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Test client
client = TestClient(app)

class TestPaginationCore:
    """Test core pagination functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Set up test database with sample data."""
        Base.metadata.create_all(bind=engine)
        
        db = TestingSessionLocal()
        
        # Create test user
        test_user = User(
            username="testuser",
            password_hash="$2b$12$LCZKmAoDSG7eHNrHv1LCYe1zt2tG9wGYo1nN1VzD2Z5JC3vCB2Z7G",  # "password"
            role="user"
        )
        db.add(test_user)
        
        # Create test admin
        admin_user = User(
            username="admin",
            password_hash="$2b$12$LCZKmAoDSG7eHNrHv1LCYe1zt2tG9wGYo1nN1VzD2Z5JC3vCB2Z7G",  # "password"
            role="admin"
        )
        db.add(admin_user)
        
        # Create sample jobs with varying attributes
        base_time = datetime.utcnow()
        
        jobs_data = [
            {
                "id": f"job-{i:03d}",
                "filename": f"test_{i}.mp3",
                "original_filename": f"test_file_{i}.mp3",
                "status": ["pending", "processing", "completed", "failed"][i % 4],
                "model_used": ["tiny", "small", "medium", "large"][i % 4],
                "created_at": base_time - timedelta(hours=i),
                "completed_at": base_time - timedelta(hours=i-1) if i % 4 == 2 else None,
                "file_size": 1000 * (i + 1),
                "duration": 60 * (i + 1),
                "error_message": "Test error" if i % 4 == 3 else None
            }
            for i in range(50)  # Create 50 test jobs
        ]
        
        for job_data in jobs_data:
            job = Job(**job_data)
            db.add(job)
        
        db.commit()
        db.close()
        
        yield
        
        # Cleanup
        Base.metadata.drop_all(bind=engine)
    
    def get_auth_headers(self, username="testuser"):
        """Get authentication headers for testing."""
        login_response = client.post(
            "/login",
            data={"username": username, "password": "password"}
        )
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_basic_pagination(self):
        """Test basic pagination without cursor."""
        headers = self.get_auth_headers()
        
        response = client.get("/jobs?page_size=10", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "data" in data
        assert "pagination" in data
        assert len(data["data"]) == 10
        
        pagination = data["pagination"]
        assert pagination["page_size"] == 10
        assert pagination["has_next"] is True
        assert pagination["has_previous"] is False
        assert pagination["next_cursor"] is not None
        assert pagination["previous_cursor"] is None
        assert pagination["sort_by"] == "created_at"
        assert pagination["sort_order"] == "desc"
    
    def test_cursor_navigation(self):
        """Test cursor-based navigation through pages."""
        headers = self.get_auth_headers()
        
        # Get first page
        response1 = client.get("/jobs?page_size=5", headers=headers)
        assert response1.status_code == 200
        
        data1 = response1.json()
        next_cursor = data1["pagination"]["next_cursor"]
        assert next_cursor is not None
        
        # Get second page using cursor
        response2 = client.get(
            f"/jobs?page_size=5&cursor={next_cursor}",
            headers=headers
        )
        assert response2.status_code == 200
        
        data2 = response2.json()
        
        # Verify different data
        job_ids_1 = {job["id"] for job in data1["data"]}
        job_ids_2 = {job["id"] for job in data2["data"]}
        assert job_ids_1.isdisjoint(job_ids_2)
        
        # Verify pagination metadata
        assert data2["pagination"]["has_previous"] is True
        assert data2["pagination"]["previous_cursor"] is not None
    
    def test_sorting_options(self):
        """Test different sorting options."""
        headers = self.get_auth_headers()
        
        # Test ascending order by created_at
        response = client.get(
            "/jobs?page_size=5&sort_by=created_at&sort_order=asc",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        jobs = data["data"]
        
        # Verify ascending order
        for i in range(len(jobs) - 1):
            current_time = datetime.fromisoformat(jobs[i]["created_at"].replace("Z", "+00:00"))
            next_time = datetime.fromisoformat(jobs[i+1]["created_at"].replace("Z", "+00:00"))
            assert current_time <= next_time
    
    def test_filtering(self):
        """Test job filtering capabilities."""
        headers = self.get_auth_headers()
        
        # Test status filtering
        response = client.get("/jobs?status=completed&page_size=20", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        for job in data["data"]:
            assert job["status"] == "completed"
        
        # Test model filtering
        response = client.get("/jobs?model_used=small&page_size=20", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        for job in data["data"]:
            assert job["model_used"] == "small"
    
    def test_total_count_optional(self):
        """Test optional total count functionality."""
        headers = self.get_auth_headers()
        
        # Without total count
        response = client.get("/jobs?page_size=10", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["total_count"] is None
        
        # With total count
        response = client.get("/jobs?page_size=10&include_total=true", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["total_count"] == 50
    
    def test_admin_endpoint(self):
        """Test admin-specific job listing endpoint."""
        headers = self.get_auth_headers("admin")
        
        response = client.get("/admin/jobs?page_size=10&include_total=true", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["data"]) == 10
        assert data["pagination"]["total_count"] == 50
        
        # Test admin access restriction
        user_headers = self.get_auth_headers("testuser")
        response = client.get("/admin/jobs", headers=user_headers)
        assert response.status_code in [401, 403]  # Forbidden or unauthorized


class TestPaginationEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Set up minimal test database."""
        Base.metadata.create_all(bind=engine)
        
        db = TestingSessionLocal()
        
        # Create test user
        test_user = User(
            username="testuser",
            password_hash="$2b$12$LCZKmAoDSG7eHNrHv1LCYe1zt2tG9wGYo1nN1VzD2Z5JC3vCB2Z7G",
            role="user"
        )
        db.add(test_user)
        db.commit()
        db.close()
        
        yield
        
        Base.metadata.drop_all(bind=engine)
    
    def get_auth_headers(self):
        """Get authentication headers for testing."""
        login_response = client.post(
            "/login",
            data={"username": "testuser", "password": "password"}
        )
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_empty_dataset(self):
        """Test pagination with no data."""
        headers = self.get_auth_headers()
        
        response = client.get("/jobs?page_size=10", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["data"] == []
        assert data["pagination"]["has_next"] is False
        assert data["pagination"]["has_previous"] is False
        assert data["pagination"]["next_cursor"] is None
        assert data["pagination"]["previous_cursor"] is None
    
    def test_invalid_page_size(self):
        """Test invalid page size validation."""
        headers = self.get_auth_headers()
        
        # Too large
        response = client.get("/jobs?page_size=200", headers=headers)
        assert response.status_code == 400
        
        # Too small
        response = client.get("/jobs?page_size=0", headers=headers)
        assert response.status_code == 400
        
        # Negative
        response = client.get("/jobs?page_size=-1", headers=headers)
        assert response.status_code == 400
    
    def test_invalid_cursor(self):
        """Test invalid cursor handling."""
        headers = self.get_auth_headers()
        
        # Malformed cursor
        response = client.get("/jobs?cursor=invalid_cursor", headers=headers)
        assert response.status_code == 400
        assert "invalid_cursor" in response.json()["detail"]["error"]
        
        # Expired cursor (simulate)
        expired_cursor_data = {
            'id': 'test-id',
            'sort_value': '2023-01-01T00:00:00',
            'sort_by': 'created_at',
            'sort_order': 'desc',
            'timestamp': (datetime.utcnow() - timedelta(hours=25)).isoformat()
        }
        expired_cursor = base64.b64encode(
            json.dumps(expired_cursor_data).encode('utf-8')
        ).decode('utf-8')
        
        response = client.get(f"/jobs?cursor={expired_cursor}", headers=headers)
        assert response.status_code == 400
    
    def test_invalid_sort_field(self):
        """Test invalid sort field validation."""
        headers = self.get_auth_headers()
        
        response = client.get("/jobs?sort_by=invalid_field", headers=headers)
        assert response.status_code == 400
    
    def test_invalid_sort_order(self):
        """Test invalid sort order validation."""
        headers = self.get_auth_headers()
        
        response = client.get("/jobs?sort_order=invalid", headers=headers)
        assert response.status_code == 400
    
    def test_invalid_filter_values(self):
        """Test invalid filter value validation."""
        headers = self.get_auth_headers()
        
        # Invalid status
        response = client.get("/jobs?status=invalid_status", headers=headers)
        assert response.status_code == 400
        
        # Invalid model
        response = client.get("/jobs?model_used=invalid_model", headers=headers)
        assert response.status_code == 400


class TestPaginationPerformance:
    """Test pagination performance characteristics."""
    
    @pytest.fixture(autouse=True)
    def setup_large_dataset(self):
        """Set up large dataset for performance testing."""
        Base.metadata.create_all(bind=engine)
        
        db = TestingSessionLocal()
        
        # Create test user
        test_user = User(
            username="testuser",
            password_hash="$2b$12$LCZKmAoDSG7eHNrHv1LCYe1zt2tG9wGYo1nN1VzD2Z5JC3vCB2Z7G",
            role="user"
        )
        db.add(test_user)
        
        # Create larger dataset for performance testing
        base_time = datetime.utcnow()
        
        jobs = []
        for i in range(1000):  # 1000 jobs for performance testing
            job = Job(
                id=f"perf-job-{i:04d}",
                filename=f"perf_{i}.mp3",
                original_filename=f"performance_test_{i}.mp3",
                status="completed",
                model_used="small",
                created_at=base_time - timedelta(seconds=i),
                completed_at=base_time - timedelta(seconds=i-10),
                file_size=1000 * (i + 1),
                duration=60 + i
            )
            jobs.append(job)
        
        db.add_all(jobs)
        db.commit()
        db.close()
        
        yield
        
        Base.metadata.drop_all(bind=engine)
    
    def get_auth_headers(self):
        """Get authentication headers for testing."""
        login_response = client.post(
            "/login",
            data={"username": "testuser", "password": "password"}
        )
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_large_dataset_pagination(self):
        """Test pagination with large dataset."""
        headers = self.get_auth_headers()
        
        # Test first page
        response = client.get("/jobs?page_size=50", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["data"]) == 50
        assert data["pagination"]["has_next"] is True
        
        # Navigate through multiple pages
        cursor = data["pagination"]["next_cursor"]
        pages_navigated = 1
        
        while cursor and pages_navigated < 5:  # Test first 5 pages
            response = client.get(
                f"/jobs?page_size=50&cursor={cursor}",
                headers=headers
            )
            assert response.status_code == 200
            
            data = response.json()
            assert len(data["data"]) == 50
            
            cursor = data["pagination"]["next_cursor"]
            pages_navigated += 1
        
        assert pages_navigated == 5
    
    def test_total_count_performance(self):
        """Test total count performance impact."""
        headers = self.get_auth_headers()
        
        import time
        
        # Measure without total count
        start_time = time.time()
        response = client.get("/jobs?page_size=50&include_total=false", headers=headers)
        time_without_count = time.time() - start_time
        assert response.status_code == 200
        
        # Measure with total count
        start_time = time.time()
        response = client.get("/jobs?page_size=50&include_total=true", headers=headers)
        time_with_count = time.time() - start_time
        assert response.status_code == 200
        
        data = response.json()
        assert data["pagination"]["total_count"] == 1000
        
        # Total count should add some overhead but not be excessive
        assert time_with_count > time_without_count
        assert time_with_count < time_without_count * 5  # Less than 5x overhead


class TestCursorGeneration:
    """Test cursor generation and parsing utilities."""
    
    def test_cursor_generation(self):
        """Test cursor generation and parsing."""
        cursor = CursorGenerator.generate_cursor(
            item_id="test-123",
            sort_field_value="2025-10-15T10:00:00",
            sort_by="created_at",
            sort_order="desc"
        )
        
        assert isinstance(cursor, str)
        assert len(cursor) > 0
        
        # Parse cursor
        parsed = CursorGenerator.parse_cursor(cursor)
        
        assert parsed["id"] == "test-123"
        assert parsed["sort_value"] == "2025-10-15T10:00:00"
        assert parsed["sort_by"] == "created_at"
        assert parsed["sort_order"] == "desc"
        assert "timestamp" in parsed
    
    def test_cursor_parsing_errors(self):
        """Test cursor parsing error handling."""
        # Invalid base64
        with pytest.raises(ValueError):
            CursorGenerator.parse_cursor("invalid_base64!")
        
        # Invalid JSON
        invalid_json = base64.b64encode(b"invalid json").decode('utf-8')
        with pytest.raises(ValueError):
            CursorGenerator.parse_cursor(invalid_json)
        
        # Missing required fields
        incomplete_data = base64.b64encode(
            json.dumps({"id": "test"}).encode('utf-8')
        ).decode('utf-8')
        with pytest.raises(ValueError):
            CursorGenerator.parse_cursor(incomplete_data)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
