"""
core/extractor.py
Handles document ingestion and text extraction from raw strings, PDF files, DOCX files, and plain text files.
"""

import os
import re
from typing import Dict, Any, Optional

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False


class DocumentExtractor:
    """Extracts and normalizes text from resumes and job descriptions."""

    @staticmethod
    def extract_from_file(file_path: str) -> str:
        """Extract plain text from a file based on its extension."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".docx":
            return DocumentExtractor._extract_from_docx(file_path)
        elif ext == ".pdf":
            return DocumentExtractor._extract_from_pdf(file_path)
        elif ext in [".txt", ".md", ".rtf", ""]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        else:
            raise ValueError(f"Unsupported file extension: {ext}. Supported formats: .txt, .docx, .pdf")

    @staticmethod
    def _extract_from_docx(file_path: str) -> str:
        if not DOCX_AVAILABLE:
            raise ImportError("python-docx is not installed. Run: pip install python-docx")
        
        doc = Document(file_path)
        text_parts = []
        for p in doc.paragraphs:
            if p.text.strip():
                text_parts.append(p.text.strip())
        
        # Also extract table text
        for table in doc.tables:
            for row in table.rows:
                row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_text:
                    text_parts.append(" | ".join(row_text))
                    
        return "\n".join(text_parts)

    @staticmethod
    def _extract_from_pdf(file_path: str) -> str:
        if not PYPDF_AVAILABLE:
            raise ImportError("pypdf is not installed. Run: pip install pypdf")

        reader = pypdf.PdfReader(file_path)
        pages_text = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                pages_text.append(t)
        return "\n".join(pages_text)

    @staticmethod
    def normalize_text(text: str) -> str:
        """Cleans excessive whitespace, non-standard hyphens, and formatting artifacts."""
        if not text:
            return ""
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Replace non-breaking spaces and fancy dashes
        text = text.replace("\xa0", " ").replace("–", "-").replace("—", "-")
        # Normalize multiple spaces (preserving newlines)
        text = re.sub(r"[ \t]+", " ", text)
        # Collapse 3+ newlines to 2
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @staticmethod
    def parse_sections(text: str) -> Dict[str, str]:
        """Heuristically segments resume text into common sections."""
        normalized = DocumentExtractor.normalize_text(text)
        sections = {
            "summary": "",
            "experience": "",
            "skills": "",
            "education": "",
            "projects": "",
            "other": ""
        }

        # Common headers
        section_patterns = {
            "summary": re.compile(r"^(?:professional\s+)?(?:summary|profile|about\s+me|objective)\b", re.I),
            "experience": re.compile(r"^(?:professional\s+|work\s+)?(?:experience|employment|work\s+history)\b", re.I),
            "skills": re.compile(r"^(?:technical\s+|core\s+)?(?:skills|competencies|technologies|tools)\b", re.I),
            "education": re.compile(r"^(?:education|academic\s+background|degrees|certifications?)\b", re.I),
            "projects": re.compile(r"^(?:key\s+|notable\s+)?(?:projects|portfolio)\b", re.I),
        }

        lines = normalized.split("\n")
        current_section = "other"
        section_lines: Dict[str, list] = {k: [] for k in sections}

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            matched_header = None
            # Check if this line looks like a header (short, matches pattern)
            if len(line_str) < 45:
                # Strip leading/trailing punctuation or bullet symbols
                clean_header = re.sub(r"^[\W_]+|[\W_]+$", "", line_str)
                for sec_name, pattern in section_patterns.items():
                    if pattern.search(clean_header):
                        matched_header = sec_name
                        break

            if matched_header:
                current_section = matched_header
            else:
                section_lines[current_section].append(line_str)

        for sec in sections:
            sections[sec] = "\n".join(section_lines[sec])

        return sections
