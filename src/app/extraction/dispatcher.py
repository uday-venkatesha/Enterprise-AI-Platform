from app.extraction.pdf import extract_text_from_pdf
from app.extraction.docx import extract_text_from_docx     # NEW
from app.extraction.pptx import extract_text_from_pptx     # NEW
from app.extraction.xlsx import extract_text_from_xlsx     # NEW


def extract_text(content_type: str, raw_bytes: bytes) -> str:
    if content_type == "application/pdf":
        return extract_text_from_pdf(raw_bytes)

    # The long content-type strings are the official MIME types for the modern
    # Office formats — the same ones already in your upload ALLOWED_CONTENT_TYPES.
    if content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_text_from_docx(raw_bytes)

    if content_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
        return extract_text_from_pptx(raw_bytes)

    if content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        return extract_text_from_xlsx(raw_bytes)

    if content_type == "text/plain":
        return raw_bytes.decode("utf-8", errors="ignore")

    raise ValueError(f"No extractor available for content type: {content_type}")