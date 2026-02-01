"""
Unit tests for common models.
Run with: pytest tests/test_models.py -v
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.common.models import (
    Citation, 
    CitationType, 
    VerificationResult, 
    AnalysisResult, 
    HallucinationReport
)


def test_citation_model():
    """Test Citation model creation and serialization."""
    citation = Citation(
        id="test123",
        type=CitationType.DOI,
        raw_text="doi:10.1234/test",
        doi="10.1234/test",
        title="Test Paper",
        authors=["Smith, J.", "Doe, A."],
        year=2024
    )
    
    assert citation.id == "test123"
    assert citation.type == CitationType.DOI
    assert citation.doi == "10.1234/test"
    
    # Test JSON serialization
    data = citation.model_dump()
    assert data["id"] == "test123"
    assert data["type"] == "doi"


def test_verification_result_model():
    """Test VerificationResult model."""
    result = VerificationResult(
        source="crossref",
        found=True,
        confidence=0.95,
        metadata={"title": "Test Paper"},
        content_snippet="This is a snippet..."
    )
    
    assert result.source == "crossref"
    assert result.found is True
    assert result.confidence == 0.95


def test_analysis_result_model():
    """Test AnalysisResult model."""
    result = AnalysisResult(
        citation_id="test123",
        verdict="supported",
        confidence_score=85.5,
        analysis_mode="llm",
        explanation="The source supports the claim."
    )
    
    assert result.verdict == "supported"
    assert result.confidence_score == 85.5
    assert result.analysis_mode == "llm"


def test_hallucination_report_model():
    """Test HallucinationReport model."""
    citation = Citation(
        id="test123",
        type=CitationType.DOI,
        raw_text="doi:10.1234/test"
    )
    
    report = HallucinationReport(
        overall_score=75.0,
        total_citations=1,
        verified_count=1,
        flagged_count=0,
        analysis_mode="llm",
        citations=[citation],
        results={}
    )
    
    assert report.overall_score == 75.0
    assert len(report.citations) == 1


if __name__ == "__main__":
    test_citation_model()
    test_verification_result_model()
    test_analysis_result_model()
    test_hallucination_report_model()
    print("All model tests passed!")
