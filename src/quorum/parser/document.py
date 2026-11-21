import io
from pathlib import Path
from typing import Union

MAX_PDF_PAGES = 30
MAX_EXTRACTED_CHARS = 50000


class DocumentParser:
    """Secure in-memory document parser with magic-byte and page-limit validation."""

    @staticmethod
    def extract_text_from_txt(content: Union[str, bytes]) -> str:
        if isinstance(content, bytes):
            return content.decode("utf-8", errors="replace")[:MAX_EXTRACTED_CHARS]
        return content[:MAX_EXTRACTED_CHARS]

    @staticmethod
    def extract_text_from_pdf(content: bytes) -> str:
        # Magic bytes check: PDF header
        if not content.startswith(b"%PDF-"):
            raise ValueError("Invalid PDF file structure. Missing standard %PDF- header.")

        try:
            from pypdf import PdfReader
        except ImportError:
            raise RuntimeError("pypdf library is required for PDF parsing.")

        try:
            reader = PdfReader(io.BytesIO(content))
        except Exception as e:
            raise ValueError(f"Corrupted or password-protected PDF document: {e}")

        if len(reader.pages) > MAX_PDF_PAGES:
            raise ValueError(
                f"PDF exceeds the maximum allowed limit of {MAX_PDF_PAGES} pages (found {len(reader.pages)})."
            )

        text_parts = []
        for i, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text.strip())
            except Exception:
                continue

        full_text = "\n\n".join(text_parts).strip()
        if len(full_text) > MAX_EXTRACTED_CHARS:
            return full_text[:MAX_EXTRACTED_CHARS] + "\n\n[Content truncated to 50,000 characters]"
        return full_text

    @staticmethod
    def extract_text_from_docx(content: bytes) -> str:
        # Magic bytes check: ZIP header for DOCX
        if not content.startswith(b"PK\x03\x04"):
            raise ValueError(
                "Invalid DOCX file structure. Document does not conform to Office Open XML format."
            )

        try:
            import docx
        except ImportError:
            raise RuntimeError("python-docx library is required for DOCX parsing.")

        try:
            doc = docx.Document(io.BytesIO(content))
        except Exception as e:
            raise ValueError(f"Corrupted DOCX document: {e}")

        text_parts = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        full_text = "\n\n".join(text_parts).strip()
        if len(full_text) > MAX_EXTRACTED_CHARS:
            return full_text[:MAX_EXTRACTED_CHARS] + "\n\n[Content truncated to 50,000 characters]"
        return full_text

    @classmethod
    def parse_file(cls, filename: str, content: Union[bytes, str]) -> str:
        ext = Path(filename).suffix.lower()
        raw_bytes = content.encode("utf-8") if isinstance(content, str) else content

        if ext in [".txt", ".md"]:
            return cls.extract_text_from_txt(raw_bytes)
        elif ext == ".pdf":
            return cls.extract_text_from_pdf(raw_bytes)
        elif ext == ".docx":
            return cls.extract_text_from_docx(raw_bytes)
        else:
            raise ValueError(
                f"Unsupported file format '{ext}'. Only .pdf, .docx, .txt, and .md files are supported."
            )
