"""
Tests for document processing endpoints and services.
"""
import io
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock


class TestDocumentUpload:
    """Tests for document upload functionality."""
    
    def test_upload_pdf_success(self, client: TestClient, sample_pdf_content: bytes):
        """Test successful PDF upload."""
        files = {"file": ("test.pdf", io.BytesIO(sample_pdf_content), "application/pdf")}
        
        response = client.post("/api/process-docs/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["filename"] == "test.pdf"
        assert data["file_type"] == "pdf"
        assert "file_size" in data
    
    def test_upload_unsupported_type(self, client: TestClient):
        """Test rejection of unsupported file types."""
        files = {"file": ("test.exe", io.BytesIO(b"fake content"), "application/x-executable")}
        
        response = client.post("/api/process-docs/upload", files=files)
        
        assert response.status_code == 400
        assert "not supported" in response.json()["detail"].lower()
    
    def test_upload_too_large(self, client: TestClient, test_settings):
        """Test rejection of files exceeding size limit."""
        # Create content larger than max size
        large_content = b"x" * (test_settings.max_file_size_mb * 1024 * 1024 + 1)
        files = {"file": ("large.pdf", io.BytesIO(large_content), "application/pdf")}
        
        response = client.post("/api/process-docs/upload", files=files)
        
        assert response.status_code == 400
        assert "size" in response.json()["detail"].lower()
    
    def test_upload_docx(self, client: TestClient):
        """Test DOCX file upload."""
        # Minimal DOCX-like content (ZIP header)
        docx_content = b"PK\x03\x04" + b"\x00" * 100
        files = {
            "file": (
                "test.docx",
                io.BytesIO(docx_content),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        }
        
        response = client.post("/api/process-docs/upload", files=files)
        
        assert response.status_code == 200
        assert response.json()["file_type"] == "docx"


class TestDocumentProcessing:
    """Tests for document processing endpoint."""
    
    def test_process_empty_request(self, client: TestClient):
        """Test processing with no documents or URLs."""
        response = client.post("/api/process-docs", json={
            "document_ids": [],
            "urls": [],
            "query": "Test query"
        })
        
        assert response.status_code == 400
        assert "no documents" in response.json()["detail"].lower()
    
    def test_process_missing_query(self, client: TestClient):
        """Test processing without a query."""
        response = client.post("/api/process-docs", json={
            "document_ids": ["doc-1"],
            "urls": [],
            "query": ""
        })
        
        assert response.status_code == 400
        assert "query" in response.json()["detail"].lower()
    
    @patch("api.routes.documents.docling_service")
    @patch("api.routes.documents.vector_store")
    @patch("api.routes.documents.embedding_service")
    def test_process_documents_success(
        self,
        mock_embedding,
        mock_vector,
        mock_docling,
        client: TestClient,
        sample_pdf_content: bytes
    ):
        """Test successful document processing pipeline."""
        # Setup mocks
        mock_docling.process_document = AsyncMock(return_value=MagicMock(
            id="doc-1",
            filename="test.pdf",
            title="Test Document",
            authors=["Author One"],
            date="2024",
            file_type="pdf",
            status="processed",
            chunk_count=5,
            content_preview="Test content...",
            metadata={},
            processed_at="2024-01-01T00:00:00"
        ))
        mock_docling.chunk_document = AsyncMock(return_value=[
            MagicMock(id="chunk-1", content="Test chunk", document_id="doc-1")
        ])
        mock_embedding.get_embeddings = MagicMock(return_value=[[0.1] * 384])
        mock_vector.index_chunks = AsyncMock(return_value=["chunk-1"])
        mock_vector.save_session_metadata = AsyncMock()
        
        # First upload a file
        files = {"file": ("test.pdf", io.BytesIO(sample_pdf_content), "application/pdf")}
        upload_response = client.post("/api/process-docs/upload", files=files)
        doc_id = upload_response.json()["id"]
        
        # Then process it
        response = client.post("/api/process-docs", json={
            "document_ids": [doc_id],
            "urls": [],
            "query": "What is in this document?"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "session_id" in data
        assert "sources" in data


class TestProcessingStatus:
    """Tests for processing status endpoint."""
    
    @patch("api.routes.documents.vector_store")
    def test_status_found(self, mock_vector, client: TestClient):
        """Test getting status for existing session."""
        mock_vector.get_session_metadata = AsyncMock(return_value=MagicMock(
            session_id="test-session",
            query="Test query",
            sources=[]
        ))
        
        response = client.get("/api/process-docs/status/test-session")
        
        assert response.status_code == 200
        assert response.json()["status"] == "processed"
    
    @patch("api.routes.documents.vector_store")
    def test_status_not_found(self, mock_vector, client: TestClient):
        """Test getting status for non-existent session."""
        mock_vector.get_session_metadata = AsyncMock(return_value=None)
        
        response = client.get("/api/process-docs/status/nonexistent")
        
        assert response.status_code == 404
