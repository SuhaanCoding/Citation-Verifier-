"""
Shared Pydantic models for all agents.
These models define the common data structures used across the Citation Verifier system.
"""
from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from enum import Enum


class CitationType(str, Enum):
    DOI = "doi"
    URL = "url"
    ISBN = "isbn"
    PAPER = "paper"
    BOOK = "book"
    UNKNOWN = "unknown"


class Citation(BaseModel):
    """A parsed citation extracted from text."""
    id: str = Field(description="Unique identifier for this citation")
    type: CitationType = Field(description="Type of citation")
    raw_text: str = Field(description="Original text of the citation")
    doi: Optional[str] = Field(default=None, description="DOI if found")
    url: Optional[str] = Field(default=None, description="URL if found")
    isbn: Optional[str] = Field(default=None, description="ISBN if found")
    title: Optional[str] = Field(default=None, description="Extracted title")
    authors: Optional[List[str]] = Field(default=None, description="List of authors")
    year: Optional[int] = Field(default=None, description="Publication year")
    context: Optional[str] = Field(default=None, description="Surrounding text context")


class VerificationResult(BaseModel):
    """Result from a verifier agent checking a citation."""
    source: str = Field(description="Name of the verification source (e.g., 'crossref', 'semantic_scholar')")
    found: bool = Field(description="Whether the citation was found in this source")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score 0-1")
    metadata: Optional[dict] = Field(default=None, description="Raw metadata from the source")
    content_snippet: Optional[str] = Field(default=None, description="Relevant content excerpt")
    error: Optional[str] = Field(default=None, description="Error message if verification failed")


class AnalysisResult(BaseModel):
    """Result from the analyst agent comparing a claim to source content."""
    citation_id: str = Field(description="ID of the citation being analyzed")
    verdict: Literal["supported", "contradicted", "unrelated", "insufficient_source"] = Field(
        description="Whether the source supports the claim"
    )
    confidence_score: float = Field(ge=0.0, le=100.0, description="Overall confidence 0-100")
    analysis_mode: Literal["llm", "tfidf"] = Field(description="Which analysis method was used")
    explanation: Optional[str] = Field(default=None, description="Human-readable explanation")
    source_exists_score: float = Field(default=0.0, description="Score for source existence")
    metadata_match_score: float = Field(default=0.0, description="Score for metadata match")
    content_similarity_score: float = Field(default=0.0, description="Score for content similarity")
    source_quality_score: float = Field(default=0.0, description="Score for source quality")


class HallucinationReport(BaseModel):
    """Final report returned to the user."""
    overall_score: float = Field(ge=0.0, le=100.0, description="Overall trustworthiness score")
    total_citations: int = Field(description="Total number of citations found")
    verified_count: int = Field(description="Number of citations successfully verified")
    flagged_count: int = Field(description="Number of citations flagged as problematic")
    analysis_mode: Literal["llm", "tfidf"] = Field(description="Primary analysis method used")
    citations: List[Citation] = Field(description="All parsed citations")
    results: dict = Field(description="Mapping of citation_id to AnalysisResult")
