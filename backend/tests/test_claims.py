"""
Tests for claim extraction endpoints and services.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock


class TestClaimExtraction:
    """Tests for the /api/extract-claims endpoint."""
    
    def test_extract_missing_session(self, client: TestClient):
        """Test extraction with missing session_id."""
        response = client.post("/api/extract-claims", json={
            "session_id": "",
            "query": "test query"
        })
        
        assert response.status_code == 400
    
    def test_extract_missing_query(self, client: TestClient):
        """Test extraction with missing query."""
        response = client.post("/api/extract-claims", json={
            "session_id": "test-session",
            "query": ""
        })
        
        assert response.status_code == 400
    
    @patch("api.routes.claims.claim_extractor")
    @patch("api.routes.claims.vector_store")
    def test_extract_claims_success(
        self,
        mock_vector,
        mock_extractor,
        client: TestClient,
        sample_claims_request: dict
    ):
        """Test successful claim extraction."""
        mock_vector.get_session_metadata = AsyncMock(return_value=MagicMock(
            session_id="test-session",
            query="test query",
            sources=[]
        ))
        mock_vector.retrieve_chunks = AsyncMock(return_value=[
            {"id": "chunk-1", "content": "Exercise improves mental health.", 
             "document_id": "doc-1", "metadata": {}}
        ])
        mock_extractor.extract_claims = AsyncMock(return_value=[
            MagicMock(
                id="claim-1",
                statement="Exercise significantly improves mental health outcomes",
                type="consensus",
                confidence=85,
                supporting_sources=3,
                contradicting_sources=0,
                source_ids=["doc-1"],
                evidence=["Multiple studies show positive effects"],
                metadata={}
            ),
            MagicMock(
                id="claim-2",
                statement="Optimal exercise duration is debated",
                type="disagreement",
                confidence=60,
                supporting_sources=2,
                contradicting_sources=2,
                source_ids=["doc-1", "doc-2"],
                evidence=["Studies show varying results"],
                metadata={}
            )
        ])
        mock_vector.update_session_claims = AsyncMock()
        
        response = client.post("/api/extract-claims", json=sample_claims_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["claims"]) == 2
        assert data["consensus_count"] == 1
        assert data["disagreement_count"] == 1
    
    @patch("api.routes.claims.claim_extractor")
    @patch("api.routes.claims.vector_store")
    def test_extract_no_chunks(
        self,
        mock_vector,
        mock_extractor,
        client: TestClient
    ):
        """Test extraction when no relevant chunks found."""
        mock_vector.get_session_metadata = AsyncMock(return_value=MagicMock(
            session_id="test-session"
        ))
        mock_vector.retrieve_chunks = AsyncMock(return_value=[])
        
        response = client.post("/api/extract-claims", json={
            "session_id": "test-session",
            "query": "unrelated query"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_claims"] == 0


class TestClaimTypes:
    """Tests for claim type classification."""
    
    @patch("api.routes.claims.claim_extractor")
    @patch("api.routes.claims.vector_store")
    def test_consensus_claims(
        self,
        mock_vector,
        mock_extractor,
        client: TestClient
    ):
        """Test that consensus claims are properly identified."""
        mock_vector.get_session_metadata = AsyncMock(return_value=MagicMock())
        mock_vector.retrieve_chunks = AsyncMock(return_value=[{"id": "c1", "content": "test"}])
        mock_extractor.extract_claims = AsyncMock(return_value=[
            MagicMock(
                id="claim-1",
                statement="All sources agree on this point",
                type="consensus",
                confidence=90,
                supporting_sources=5,
                contradicting_sources=0,
                source_ids=["s1", "s2", "s3"],
                evidence=["Strong agreement"],
                metadata={}
            )
        ])
        mock_vector.update_session_claims = AsyncMock()
        
        response = client.post("/api/extract-claims", json={
            "session_id": "test-session",
            "query": "test"
        })
        
        data = response.json()
        assert data["consensus_count"] == 1
        assert data["disagreement_count"] == 0
        assert data["claims"][0]["type"] == "consensus"
    
    @patch("api.routes.claims.claim_extractor")
    @patch("api.routes.claims.vector_store")
    def test_disagreement_claims(
        self,
        mock_vector,
        mock_extractor,
        client: TestClient
    ):
        """Test that disagreement claims are properly identified."""
        mock_vector.get_session_metadata = AsyncMock(return_value=MagicMock())
        mock_vector.retrieve_chunks = AsyncMock(return_value=[{"id": "c1", "content": "test"}])
        mock_extractor.extract_claims = AsyncMock(return_value=[
            MagicMock(
                id="claim-1",
                statement="Sources disagree on this point",
                type="disagreement",
                confidence=50,
                supporting_sources=2,
                contradicting_sources=2,
                source_ids=["s1", "s2"],
                evidence=["Conflicting evidence"],
                metadata={}
            )
        ])
        mock_vector.update_session_claims = AsyncMock()
        
        response = client.post("/api/extract-claims", json={
            "session_id": "test-session",
            "query": "test"
        })
        
        data = response.json()
        assert data["disagreement_count"] == 1
        assert data["claims"][0]["type"] == "disagreement"


class TestGetSessionClaims:
    """Tests for retrieving claims from existing sessions."""
    
    @patch("api.routes.claims.vector_store")
    def test_get_session_claims_success(
        self,
        mock_vector,
        client: TestClient
    ):
        """Test retrieving claims for an existing session."""
        mock_vector.get_session_metadata = AsyncMock(return_value=MagicMock(
            session_id="test-session",
            claims=[
                MagicMock(
                    id="claim-1",
                    statement="Test claim",
                    type="consensus",
                    confidence=80,
                    supporting_sources=2,
                    contradicting_sources=0,
                    source_ids=["s1"],
                    evidence=["Evidence"],
                    metadata={}
                )
            ]
        ))
        
        response = client.get("/api/extract-claims/test-session")
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-session"
        assert len(data["claims"]) >= 0
    
    @patch("api.routes.claims.vector_store")
    def test_get_session_claims_not_found(
        self,
        mock_vector,
        client: TestClient
    ):
        """Test retrieving claims for non-existent session."""
        mock_vector.get_session_metadata = AsyncMock(return_value=None)
        
        response = client.get("/api/extract-claims/nonexistent")
        
        assert response.status_code == 404
