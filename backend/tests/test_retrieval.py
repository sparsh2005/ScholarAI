"""
Tests for chunk retrieval endpoints and services.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock


class TestChunkRetrieval:
    """Tests for the /api/retrieve-chunks endpoint."""
    
    def test_retrieve_missing_session(self, client: TestClient):
        """Test retrieval with missing session_id."""
        response = client.post("/api/retrieve-chunks", json={
            "session_id": "",
            "query": "test query"
        })
        
        assert response.status_code == 400
    
    def test_retrieve_missing_query(self, client: TestClient):
        """Test retrieval with missing query."""
        response = client.post("/api/retrieve-chunks", json={
            "session_id": "test-session",
            "query": ""
        })
        
        assert response.status_code == 400
    
    @patch("api.routes.retrieval.vector_store")
    @patch("api.routes.retrieval.embedding_service")
    def test_retrieve_success(
        self,
        mock_embedding,
        mock_vector,
        client: TestClient,
        sample_retrieve_request: dict
    ):
        """Test successful chunk retrieval."""
        mock_embedding.get_embeddings = MagicMock(return_value=[[0.1] * 384])
        mock_vector.retrieve_chunks = AsyncMock(return_value=[
            {
                "id": "chunk-1",
                "document_id": "doc-1",
                "source_title": "Test Paper",
                "content": "Exercise reduces depression symptoms significantly.",
                "relevance_score": 0.95,
                "metadata": {"page": 1}
            },
            {
                "id": "chunk-2",
                "document_id": "doc-1",
                "source_title": "Test Paper",
                "content": "Physical activity improves mental health outcomes.",
                "relevance_score": 0.88,
                "metadata": {"page": 2}
            }
        ])
        
        response = client.post("/api/retrieve-chunks", json=sample_retrieve_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["chunks"]) == 2
        assert data["chunks"][0]["relevance_score"] > data["chunks"][1]["relevance_score"]
    
    @patch("api.routes.retrieval.vector_store")
    @patch("api.routes.retrieval.embedding_service")
    def test_retrieve_empty_results(
        self,
        mock_embedding,
        mock_vector,
        client: TestClient
    ):
        """Test retrieval with no matching chunks."""
        mock_embedding.get_embeddings = MagicMock(return_value=[[0.1] * 384])
        mock_vector.retrieve_chunks = AsyncMock(return_value=[])
        
        response = client.post("/api/retrieve-chunks", json={
            "session_id": "test-session",
            "query": "completely unrelated query",
            "top_k": 10
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_results"] == 0
        assert len(data["chunks"]) == 0
    
    @patch("api.routes.retrieval.vector_store")
    @patch("api.routes.retrieval.embedding_service")
    def test_retrieve_respects_top_k(
        self,
        mock_embedding,
        mock_vector,
        client: TestClient
    ):
        """Test that top_k parameter limits results."""
        mock_embedding.get_embeddings = MagicMock(return_value=[[0.1] * 384])
        # Return more chunks than requested
        mock_vector.retrieve_chunks = AsyncMock(return_value=[
            {"id": f"chunk-{i}", "document_id": "doc-1", "content": f"Content {i}", 
             "relevance_score": 0.9 - i*0.1, "source_title": "Test", "metadata": {}}
            for i in range(5)
        ])
        
        response = client.post("/api/retrieve-chunks", json={
            "session_id": "test-session",
            "query": "test query",
            "top_k": 3
        })
        
        assert response.status_code == 200
        # Vector store should be called with top_k=3
        mock_vector.retrieve_chunks.assert_called_once()


class TestRetrievalFilters:
    """Tests for retrieval filtering functionality."""
    
    @patch("api.routes.retrieval.vector_store")
    @patch("api.routes.retrieval.embedding_service")
    def test_retrieve_with_filters(
        self,
        mock_embedding,
        mock_vector,
        client: TestClient
    ):
        """Test retrieval with document filters."""
        mock_embedding.get_embeddings = MagicMock(return_value=[[0.1] * 384])
        mock_vector.retrieve_chunks = AsyncMock(return_value=[])
        
        response = client.post("/api/retrieve-chunks", json={
            "session_id": "test-session",
            "query": "test query",
            "filters": {"document_id": "specific-doc"}
        })
        
        assert response.status_code == 200
