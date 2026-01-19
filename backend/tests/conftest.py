"""
Pytest configuration and fixtures for ScholarAI backend tests.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, AsyncMock

import pytest
from fastapi.testclient import TestClient

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from config import Settings, get_settings


# =============================================================================
# Test Settings
# =============================================================================

def get_test_settings() -> Settings:
    """Create test settings with temporary directories."""
    temp_dir = tempfile.mkdtemp()
    return Settings(
        openai_api_key="test-api-key",
        upload_directory=os.path.join(temp_dir, "uploads"),
        processed_directory=os.path.join(temp_dir, "processed"),
        chroma_persist_directory=os.path.join(temp_dir, "chroma"),
        chunk_size=500,
        chunk_overlap=50,
        embedding_model="all-MiniLM-L6-v2",
        max_file_size_mb=10,
    )


@pytest.fixture
def test_settings() -> Generator[Settings, None, None]:
    """Fixture providing test settings with cleanup."""
    settings = get_test_settings()
    
    # Create directories
    os.makedirs(settings.upload_directory, exist_ok=True)
    os.makedirs(settings.processed_directory, exist_ok=True)
    os.makedirs(settings.chroma_persist_directory, exist_ok=True)
    
    yield settings
    
    # Cleanup
    parent_dir = Path(settings.upload_directory).parent
    if parent_dir.exists():
        shutil.rmtree(parent_dir)


# =============================================================================
# Test Client
# =============================================================================

@pytest.fixture
def client(test_settings: Settings) -> Generator[TestClient, None, None]:
    """Create a test client with mocked settings."""
    app.dependency_overrides[get_settings] = lambda: test_settings
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


# =============================================================================
# Sample Data Fixtures
# =============================================================================

@pytest.fixture
def sample_pdf_content() -> bytes:
    """Minimal valid PDF content for testing."""
    return b"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >> endobj
4 0 obj << /Length 44 >> stream
BT /F1 12 Tf 100 700 Td (Test Document) Tj ET
endstream endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer << /Size 5 /Root 1 0 R >>
startxref
300
%%EOF"""


@pytest.fixture
def sample_text_content() -> str:
    """Sample research text content for testing."""
    return """
# Effects of Exercise on Mental Health

## Abstract
This study examines the relationship between regular physical exercise 
and mental health outcomes. We conducted a meta-analysis of 50 randomized 
controlled trials involving 3,000 participants.

## Key Findings
1. Regular exercise significantly reduces symptoms of depression (p < 0.001)
2. Moderate-intensity exercise showed the strongest effects
3. Benefits were observed across all age groups
4. Exercise combined with therapy showed synergistic effects

## Conclusion
Physical exercise is an effective intervention for improving mental health 
outcomes. Healthcare providers should consider exercise as part of comprehensive 
treatment plans.

## References
- Smith et al. (2023) Exercise and Depression Meta-analysis
- Johnson & Williams (2022) Physical Activity Guidelines
"""


@pytest.fixture
def sample_process_request() -> dict:
    """Sample document processing request."""
    return {
        "document_ids": [],
        "urls": [],
        "query": "What are the effects of exercise on mental health?"
    }


@pytest.fixture
def sample_retrieve_request() -> dict:
    """Sample chunk retrieval request."""
    return {
        "session_id": "test-session-123",
        "query": "exercise depression treatment",
        "top_k": 10
    }


@pytest.fixture
def sample_claims_request() -> dict:
    """Sample claim extraction request."""
    return {
        "session_id": "test-session-123",
        "query": "What are the effects of exercise on mental health?"
    }


@pytest.fixture
def sample_synthesis_request() -> dict:
    """Sample synthesis request."""
    return {
        "session_id": "test-session-123",
        "query": "What are the effects of exercise on mental health?"
    }


# =============================================================================
# Mock Services
# =============================================================================

@pytest.fixture
def mock_embedding_service():
    """Mock embedding service."""
    mock = MagicMock()
    mock.get_embeddings = MagicMock(return_value=[[0.1] * 384])
    return mock


@pytest.fixture
def mock_vector_store():
    """Mock vector store service."""
    mock = MagicMock()
    mock.index_chunks = AsyncMock(return_value=["chunk-1", "chunk-2"])
    mock.retrieve_chunks = AsyncMock(return_value=[
        {
            "id": "chunk-1",
            "document_id": "doc-1",
            "content": "Exercise reduces depression symptoms.",
            "relevance_score": 0.95,
            "metadata": {"source_title": "Test Paper"}
        }
    ])
    mock.save_session_metadata = AsyncMock()
    mock.get_session_metadata = AsyncMock(return_value=None)
    return mock


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    return {
        "choices": [{
            "message": {
                "content": """{
                    "claims": [
                        {
                            "statement": "Exercise reduces depression symptoms",
                            "type": "consensus",
                            "confidence": 85,
                            "evidence": ["Multiple RCTs show significant reduction"]
                        }
                    ]
                }"""
            }
        }]
    }
