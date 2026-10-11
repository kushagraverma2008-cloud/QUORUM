import io
from pathlib import Path
from typing import Union, BinaryIO

class DocumentParser:
    """Parses pitch documents, PDF files, and Word documents into clean text."""
    
    @staticmethod
    def extract_text_from_txt(content: Union[str, bytes]) -> str:
        if isinstance(content, bytes):
            return content.decode("utf-8", errors="replace")
        return content

    @staticmethod
    def extract_text_from_pdf(file_bytes_or_path: Union[bytes, str, Path]) -> str:
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ImportError("pypdf is required for PDF parsing. Install with `pip install pypdf`")
            
        if isinstance(file_bytes_or_path, (str, Path)):
            reader = PdfReader(str(file_bytes_or_path))
        else:
            reader = PdfReader(io.BytesIO(file_bytes_or_path))
            
        text_parts = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text.strip())
        return "\n\n".join(text_parts)

    @staticmethod
    def extract_text_from_docx(file_bytes_or_path: Union[bytes, str, Path]) -> str:
        try:
            import docx
        except ImportError:
            raise ImportError("python-docx is required for DOCX parsing. Install with `pip install python-docx`")
            
        if isinstance(file_bytes_or_path, (str, Path)):
            doc = docx.Document(str(file_bytes_or_path))
        else:
            doc = docx.Document(io.BytesIO(file_bytes_or_path))
            
        text_parts = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(text_parts)

    @classmethod
    def parse_file(cls, filename: str, content: Union[bytes, str]) -> str:
        ext = Path(filename).suffix.lower()
        if ext in [".txt", ".md", ".json"]:
            return cls.extract_text_from_txt(content)
        elif ext == ".pdf":
            if isinstance(content, str):
                content = content.encode("utf-8")
            return cls.extract_text_from_pdf(content)
        elif ext in [".docx", ".doc"]:
            if isinstance(content, str):
                content = content.encode("utf-8")
            return cls.extract_text_from_docx(content)
        else:
            return cls.extract_text_from_txt(content)
