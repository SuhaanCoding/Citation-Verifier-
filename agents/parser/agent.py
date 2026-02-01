"""
Citation Parser Agent - Core Logic

Extracts citations from academic text using regex patterns and heuristics.
Supports DOI, URL, ISBN, and common citation formats (APA, MLA).
"""
import re
import uuid
from typing import List, Optional
from agents.common.models import Citation, CitationType


class ParserAgent:
    """Parses text to extract citations."""

    # Regex patterns for citation extraction
    DOI_PATTERN = re.compile(
        r'(?:doi[:\s]*|https?://(?:dx\.)?doi\.org/)?(10\.\d{4,}/[^\s\]\)]+)',
        re.IGNORECASE
    )
    
    URL_PATTERN = re.compile(
        r'https?://[^\s\]\)]+',
        re.IGNORECASE
    )
    
    ISBN_PATTERN = re.compile(
        r'ISBN[:\s-]*((?:97[89][- ]?)?(?:\d[- ]?){9}[\dXx])',
        re.IGNORECASE
    )
    
    # APA: Author, A. A. (Year). Title. Journal, Vol(Issue), Pages.
    # Simplified pattern: Name (Year). Title.
    APA_PATTERN = re.compile(
        r'([A-Z][a-z]+(?:,\s*[A-Z]\.?\s*[A-Z]?\.?)?(?:\s*(?:,|&)\s*[A-Z][a-z]+(?:,\s*[A-Z]\.?\s*[A-Z]?\.?)?)*)\s*\((\d{4})\)\.\s*([^.]+)\.',
        re.MULTILINE
    )
    
    # Year in parentheses: (Author, Year) or (Year)
    YEAR_PATTERN = re.compile(r'\((\d{4})\)')

    def parse(self, text: str) -> List[Citation]:
        """
        Parse text and extract all citations.
        
        Args:
            text: The input text containing citations.
            
        Returns:
            List of Citation objects.
        """
        citations: List[Citation] = []
        seen_ids = set()  # Track unique citations
        
        # Extract DOIs
        for match in self.DOI_PATTERN.finditer(text):
            doi = match.group(1).rstrip('.,;')
            if doi not in seen_ids:
                seen_ids.add(doi)
                citations.append(Citation(
                    id=str(uuid.uuid4())[:8],
                    type=CitationType.DOI,
                    raw_text=match.group(0),
                    doi=doi,
                    context=self._get_context(text, match.start(), match.end())
                ))
        
        # Extract URLs (excluding DOI URLs already captured)
        for match in self.URL_PATTERN.finditer(text):
            url = match.group(0).rstrip('.,;)')
            if 'doi.org' not in url and url not in seen_ids:
                seen_ids.add(url)
                citations.append(Citation(
                    id=str(uuid.uuid4())[:8],
                    type=CitationType.URL,
                    raw_text=match.group(0),
                    url=url,
                    context=self._get_context(text, match.start(), match.end())
                ))
        
        # Extract ISBNs
        for match in self.ISBN_PATTERN.finditer(text):
            isbn = match.group(1).replace('-', '').replace(' ', '')
            if isbn not in seen_ids:
                seen_ids.add(isbn)
                citations.append(Citation(
                    id=str(uuid.uuid4())[:8],
                    type=CitationType.ISBN,
                    raw_text=match.group(0),
                    isbn=isbn,
                    context=self._get_context(text, match.start(), match.end())
                ))
        
        # Extract APA-style citations
        for match in self.APA_PATTERN.finditer(text):
            raw = match.group(0)
            if raw not in seen_ids:
                seen_ids.add(raw)
                authors = self._parse_authors(match.group(1))
                year = int(match.group(2))
                title = match.group(3).strip()
                citations.append(Citation(
                    id=str(uuid.uuid4())[:8],
                    type=CitationType.PAPER,
                    raw_text=raw,
                    title=title,
                    authors=authors,
                    year=year,
                    context=self._get_context(text, match.start(), match.end())
                ))
        
        return citations

    def _get_context(self, text: str, start: int, end: int, window: int = 100) -> str:
        """Extract surrounding context for a citation."""
        ctx_start = max(0, start - window)
        ctx_end = min(len(text), end + window)
        return text[ctx_start:ctx_end].strip()

    def _parse_authors(self, author_str: str) -> List[str]:
        """Parse author string into list of names."""
        # Split on & or , and clean up
        authors = re.split(r'\s*[&,]\s*', author_str)
        return [a.strip() for a in authors if a.strip() and not re.match(r'^[A-Z]\.$', a.strip())]
