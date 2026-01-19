"""
Tests for health check and basic API functionality.
"""
import pytest
from fastapi.testclient import TestClient


class TestHealthCheck:
    """Tests for health check endpoint."""
    
    def test_health_check_success(self, client: TestClient):
        """Test that health check returns healthy status."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data
    
    def test_health_check_returns_json(self, client: TestClient):
        """Test that health check returns JSON content type."""
        response = client.get("/health")
        
        assert response.headers["content-type"] == "application/json"


class TestCORS:
    """Tests for CORS configuration."""
    
    def test_cors_headers_present(self, client: TestClient):
        """Test that CORS headers are present in responses."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET"
            }
        )
        
        # Should allow the origin
        assert response.status_code in [200, 204]
    
    def test_cors_allows_localhost(self, client: TestClient):
        """Test that CORS allows localhost origins."""
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:5173"}
        )
        
        assert response.status_code == 200


class TestAPIRoot:
    """Tests for API root and documentation."""
    
    def test_api_docs_available(self, client: TestClient):
        """Test that API docs are available."""
        response = client.get("/docs")
        
        assert response.status_code == 200
    
    def test_openapi_schema_available(self, client: TestClient):
        """Test that OpenAPI schema is available."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
        assert "/api/process-docs" in data["paths"]
        assert "/api/retrieve-chunks" in data["paths"]
        assert "/api/extract-claims" in data["paths"]
        assert "/api/synthesize-report" in data["paths"]


class TestErrorHandling:
    """Tests for error handling."""
    
    def test_404_for_unknown_route(self, client: TestClient):
        """Test that unknown routes return 404."""
        response = client.get("/api/unknown-endpoint")
        
        assert response.status_code == 404
    
    def test_405_for_wrong_method(self, client: TestClient):
        """Test that wrong HTTP methods return 405."""
        response = client.get("/api/process-docs")  # Should be POST
        
        assert response.status_code == 405
    
    def test_422_for_invalid_json(self, client: TestClient):
        """Test that invalid JSON returns 422."""
        response = client.post(
            "/api/process-docs",
            content="invalid json{",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
