"""
Unit tests for the Parser Agent logic.
Run with: pytest tests/test_parser_logic.py -v
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.parser.agent import ParserAgent
from agents.common.models import CitationType


def test_parse_doi():
    """Test DOI extraction."""
    parser = ParserAgent()
    text = "According to the study (doi:10.1234/example.2024) and https://doi.org/10.5678/another"
    
    citations = parser.parse(text)
    dois = [c for c in citations if c.type == CitationType.DOI]
    
    assert len(dois) == 2
    assert "10.1234/example.2024" in [c.doi for c in dois]
    assert "10.5678/another" in [c.doi for c in dois]


def test_parse_url():
    """Test URL extraction (non-DOI)."""
    parser = ParserAgent()
    text = "See https://example.com/paper for more details."
    
    citations = parser.parse(text)
    urls = [c for c in citations if c.type == CitationType.URL]
    
    assert len(urls) == 1
    assert "https://example.com/paper" in urls[0].url


def test_parse_isbn():
    """Test ISBN extraction."""
    parser = ParserAgent()
    text = "Reference: ISBN 978-3-16-148410-0 and ISBN: 0-306-40615-2"
    
    citations = parser.parse(text)
    isbns = [c for c in citations if c.type == CitationType.ISBN]
    
    assert len(isbns) == 2


def test_parse_apa_citation():
    """Test APA-style citation extraction."""
    parser = ParserAgent()
    text = "Smith, J. A. (2020). The impact of AI on society. Journal of AI Research."
    
    citations = parser.parse(text)
    papers = [c for c in citations if c.type == CitationType.PAPER]
    
    assert len(papers) >= 1
    paper = papers[0]
    assert paper.year == 2020
    assert "The impact of AI on society" in paper.title


def test_parse_mixed():
    """Test extraction of multiple citation types."""
    parser = ParserAgent()
    text = """
    According to Smith (doi:10.1234/test.2024), the results are significant.
    For more information, visit https://example.org/data.
    The book ISBN 978-0-13-468599-1 provides background.
    """
    
    citations = parser.parse(text)
    
    assert len(citations) >= 3
    types = {c.type for c in citations}
    assert CitationType.DOI in types
    assert CitationType.URL in types
    assert CitationType.ISBN in types


def test_parse_empty():
    """Test parsing empty text."""
    parser = ParserAgent()
    citations = parser.parse("")
    assert len(citations) == 0


def test_parse_no_citations():
    """Test parsing text with no citations."""
    parser = ParserAgent()
    text = "This is just regular text without any citations or references."
    citations = parser.parse(text)
    assert len(citations) == 0


if __name__ == "__main__":
    # Run tests manually
    test_parse_doi()
    test_parse_url()
    test_parse_isbn()
    test_parse_apa_citation()
    test_parse_mixed()
    test_parse_empty()
    test_parse_no_citations()
    print("All tests passed!")
