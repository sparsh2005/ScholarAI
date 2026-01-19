"""
Tests for research brief synthesis endpoints and services.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock


class TestSynthesis:
    """Tests for the /api/synthesize-report endpoint."""
    
    def test_synthesize_missing_session(self, client: TestClient):
        """Test synthesis with missing session_id."""
        response = client.post("/api/synthesize-report", json={
            "session_id": "",
            "query": "test query"
        })
        
        assert response.status_code == 400
    
    def test_synthesize_missing_query(self, client: TestClient):
        """Test synthesis with missing query."""
        response = client.post("/api/synthesize-report", json={
            "session_id": "test-session",
            "query": ""
        })
        
        assert response.status_code == 400
    
    @patch("api.routes.synthesis.synthesizer")
    @patch("api.routes.synthesis.vector_store")
    def test_synthesize_success(
        self,
        mock_vector,
        mock_synthesizer,
        client: TestClient,
        sample_synthesis_request: dict
    ):
        """Test successful research brief synthesis."""
        mock_vector.get_session_metadata = AsyncMock(return_value=MagicMock(
            session_id="test-session",
            query="What are the effects of exercise?",
            sources=[
                MagicMock(
                    id="s1", title="Study 1", authors=["Author A"],
                    date="2023", type="pdf", status="processed",
                    claims_extracted=5, relevance_score=0.9,
                    thumbnail_color="#4A90D9"
                )
            ],
            claims=[
                MagicMock(
                    id="c1", statement="Exercise helps", type="consensus",
                    confidence=85, supporting_sources=3, contradicting_sources=0,
                    source_ids=["s1"], evidence=["Strong evidence"], metadata={}
                )
            ]
        ))
        
        mock_brief = MagicMock(
            query="What are the effects of exercise?",
            session_id="test-session",
            sources=[],
            consensus=[
                MagicMock(
                    id="con-1",
                    statement="Exercise improves mental health",
                    confidence=85,
                    sources=3,
                    source_ids=["s1"],
                    evidence_summary="Multiple studies confirm benefits"
                )
            ],
            disagreements=[
                MagicMock(
                    id="dis-1",
                    claim="Optimal exercise duration",
                    perspective1="30 minutes daily is sufficient",
                    perspective2="60 minutes shows better results",
                    sources=4,
                    source_ids=["s1", "s2"]
                )
            ],
            open_questions=[
                MagicMock(
                    id="q-1",
                    question="What is the long-term effect?",
                    context="Limited longitudinal studies",
                    related_claim_ids=["c1"]
                )
            ],
            confidence_level="high",
            confidence_score=82,
            limitations=["Limited sample sizes in some studies"],
            generated_at="2024-01-01T00:00:00"
        )
        mock_synthesizer.synthesize_report = AsyncMock(return_value=mock_brief)
        mock_vector.update_session_brief = AsyncMock()
        
        response = client.post("/api/synthesize-report", json=sample_synthesis_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "brief" in data
        assert "processing_time_ms" in data
        
        brief = data["brief"]
        assert brief["confidence_level"] == "high"
        assert len(brief["consensus"]) > 0
        assert len(brief["disagreements"]) > 0
        assert len(brief["open_questions"]) > 0


class TestBriefStructure:
    """Tests for research brief structure validation."""
    
    @patch("api.routes.synthesis.synthesizer")
    @patch("api.routes.synthesis.vector_store")
    def test_brief_contains_all_sections(
        self,
        mock_vector,
        mock_synthesizer,
        client: TestClient
    ):
        """Test that brief contains all required sections."""
        mock_vector.get_session_metadata = AsyncMock(return_value=MagicMock(
            session_id="test", sources=[], claims=[]
        ))
        mock_synthesizer.synthesize_report = AsyncMock(return_value=MagicMock(
            query="test",
            session_id="test-session",
            sources=[],
            consensus=[],
            disagreements=[],
            open_questions=[],
            confidence_level="medium",
            confidence_score=60,
            limitations=["Limited data"],
            generated_at="2024-01-01T00:00:00"
        ))
        mock_vector.update_session_brief = AsyncMock()
        
        response = client.post("/api/synthesize-report", json={
            "session_id": "test-session",
            "query": "test query"
        })
        
        brief = response.json()["brief"]
        
        # Check all required fields exist
        assert "query" in brief
        assert "session_id" in brief
        assert "sources" in brief
        assert "consensus" in brief
        assert "disagreements" in brief
        assert "open_questions" in brief
        assert "confidence_level" in brief
        assert "confidence_score" in brief
        assert "limitations" in brief
        assert "generated_at" in brief
    
    @patch("api.routes.synthesis.synthesizer")
    @patch("api.routes.synthesis.vector_store")
    def test_confidence_levels(
        self,
        mock_vector,
        mock_synthesizer,
        client: TestClient
    ):
        """Test that confidence level corresponds to score."""
        test_cases = [
            (90, "high"),
            (70, "medium"),
            (40, "low"),
        ]
        
        for score, expected_level in test_cases:
            mock_vector.get_session_metadata = AsyncMock(return_value=MagicMock(
                session_id="test", sources=[], claims=[]
            ))
            mock_synthesizer.synthesize_report = AsyncMock(return_value=MagicMock(
                query="test",
                session_id="test-session",
                sources=[],
                consensus=[],
                disagreements=[],
                open_questions=[],
                confidence_level=expected_level,
                confidence_score=score,
                limitations=[],
                generated_at="2024-01-01T00:00:00"
            ))
            mock_vector.update_session_brief = AsyncMock()
            
            response = client.post("/api/synthesize-report", json={
                "session_id": "test-session",
                "query": "test"
            })
            
            brief = response.json()["brief"]
            assert brief["confidence_level"] == expected_level


class TestGetExistingBrief:
    """Tests for retrieving existing research briefs."""
    
    @patch("api.routes.synthesis.vector_store")
    def test_get_brief_success(
        self,
        mock_vector,
        client: TestClient
    ):
        """Test retrieving an existing brief."""
        mock_vector.get_session_metadata = AsyncMock(return_value=MagicMock(
            session_id="test-session",
            brief=MagicMock(
                query="test",
                session_id="test-session",
                sources=[],
                consensus=[],
                disagreements=[],
                open_questions=[],
                confidence_level="high",
                confidence_score=85,
                limitations=[],
                generated_at="2024-01-01T00:00:00"
            )
        ))
        
        response = client.get("/api/synthesize-report/test-session")
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-session"
    
    @patch("api.routes.synthesis.vector_store")
    def test_get_brief_not_found(
        self,
        mock_vector,
        client: TestClient
    ):
        """Test retrieving brief for non-existent session."""
        mock_vector.get_session_metadata = AsyncMock(return_value=None)
        
        response = client.get("/api/synthesize-report/nonexistent")
        
        assert response.status_code == 404
