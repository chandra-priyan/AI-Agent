import os
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.database import Base, engine

@pytest.fixture(autouse=True)
def init_test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

@pytest.mark.anyio
async def test_auth_register_login_flow():
    """Test 1-4: Registration, login, duplicate email, invalid credentials."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        email = f"user1_{os.urandom(4).hex()}@example.com"

        reg_res = await ac.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
        assert reg_res.status_code == 200
        reg_data = reg_res.json()
        assert "token" in reg_data
        assert reg_data["user"]["email"] == email

        dup_res = await ac.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
        assert dup_res.status_code == 400

        bad_login = await ac.post("/api/v1/auth/login", json={"email": email, "password": "wrongpassword"})
        assert bad_login.status_code == 401

        login_res = await ac.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
        assert login_res.status_code == 200
        assert "token" in login_res.json()

@pytest.mark.anyio
async def test_auth_me_and_protected_endpoint():
    """Test 5-6: Protected endpoint requiring auth token, GET /me."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        email = f"user2_{os.urandom(4).hex()}@example.com"
        reg_res = await ac.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
        assert reg_res.status_code == 200
        token = reg_res.json()["token"]

        me_res = await ac.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_res.status_code == 200
        assert me_res.json()["email"] == email

        no_auth = await ac.get("/api/v1/auth/me")
        assert no_auth.status_code == 401

@pytest.mark.anyio
async def test_background_job_start_and_status():
    """Test 7-10: Upload CSV, start non-blocking job, poll QUEUED/RUNNING status."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        email = f"worker_user_{os.urandom(4).hex()}@example.com"
        reg_res = await ac.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
        assert reg_res.status_code == 200
        token = reg_res.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        csv_bytes = b"Region,Sales\nNorth,100\nSouth,200\n"
        up_res = await ac.post(
            "/api/v1/analysis/upload",
            files={"file": ("data.csv", csv_bytes, "text/csv")},
            headers=headers
        )
        assert up_res.status_code == 200, f"Upload failed: {up_res.text}"
        analysis_id = up_res.json()["analysis_id"]

        start_res = await ac.post(
            f"/api/v1/analysis/{analysis_id}/start",
            json={"user_question": "Why did sales decrease?"},
            headers=headers
        )
        assert start_res.status_code == 200, f"Start failed: {start_res.text}"
        start_data = start_res.json()
        assert start_data.get("status") == "QUEUED", f"Unexpected start response: {start_data}"

        status_res = await ac.get(f"/api/v1/analysis/{analysis_id}/status", headers=headers)
        assert status_res.status_code == 200, f"Status poll failed: {status_res.text}"
        sdata = status_res.json()
        assert sdata.get("status") in ("QUEUED", "RUNNING", "COMPLETED")
        assert "stage" in sdata
        assert "progress" in sdata

@pytest.mark.anyio
async def test_user_isolation():
    """Test 15-16, 18-19: User A cannot access or delete User B's analysis."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        reg_a = await ac.post("/api/v1/auth/register", json={"email": f"usera_{os.urandom(3).hex()}@ex.com", "password": "password123"})
        assert reg_a.status_code == 200
        token_a = reg_a.json()["token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        reg_b = await ac.post("/api/v1/auth/register", json={"email": f"userb_{os.urandom(3).hex()}@ex.com", "password": "password123"})
        assert reg_b.status_code == 200
        token_b = reg_b.json()["token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        csv_bytes = b"Region,Sales\nNorth,100\nSouth,200\n"
        up_res = await ac.post(
            "/api/v1/analysis/upload",
            files={"file": ("a_data.csv", csv_bytes, "text/csv")},
            headers=headers_a
        )
        assert up_res.status_code == 200, f"User A upload failed: {up_res.text}"
        analysis_id = up_res.json()["analysis_id"]

        status_b = await ac.get(f"/api/v1/analysis/{analysis_id}/status", headers=headers_b)
        assert status_b.status_code == 403, f"Expected 403, got {status_b.status_code}: {status_b.text}"

        del_b = await ac.delete(f"/api/v1/analysis/{analysis_id}", headers=headers_b)
        assert del_b.status_code == 403, f"Expected 403, got {del_b.status_code}: {del_b.text}"

        del_a = await ac.delete(f"/api/v1/analysis/{analysis_id}", headers=headers_a)
        assert del_a.status_code == 200, f"Expected 200, got {del_a.status_code}: {del_a.text}"

@pytest.mark.anyio
async def test_retry_and_cancel_endpoints():
    """Test 12-13: Retry & Cancel job management endpoints."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        user_email = f"job_mgr_{os.urandom(3).hex()}@ex.com"
        reg = await ac.post("/api/v1/auth/register", json={"email": user_email, "password": "password123"})
        assert reg.status_code == 200
        headers = {"Authorization": f"Bearer {reg.json()['token']}"}

        csv_data = b"Region,Sales\nNorth,100\nSouth,200\n"
        up = await ac.post("/api/v1/analysis/upload", files={"file": ("test.csv", csv_data, "text/csv")}, headers=headers)
        assert up.status_code == 200, f"Upload failed: {up.text}"
        aid = up.json()["analysis_id"]

        cancel_res = await ac.post(f"/api/v1/analysis/{aid}/cancel", headers=headers)
        assert cancel_res.status_code == 200, f"Cancel failed: {cancel_res.text}"
        assert cancel_res.json().get("status") == "CANCELLED"

        retry_res = await ac.post(f"/api/v1/analysis/{aid}/retry", headers=headers)
        assert retry_res.status_code == 200, f"Retry failed: {retry_res.text}"
        assert retry_res.json().get("status") == "QUEUED"

@pytest.mark.anyio
async def test_health_check_endpoint():
    """Test 20: Comprehensive health check endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        h_res = await ac.get("/api/v1/health")
        assert h_res.status_code == 200
        h_data = h_res.json()
        assert "status" in h_data
        assert "services" in h_data
        assert h_data["services"]["backend"] == "healthy"
        assert h_data["services"]["database"] == "healthy"
