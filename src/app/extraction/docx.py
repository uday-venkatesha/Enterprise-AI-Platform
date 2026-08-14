import io

from docx import Document as DocxDocument   # renamed to avoid clashing with OUR Document model


def extract_text_from_docx(raw_bytes: bytes) -> str:
    # Same io.BytesIO trick as the PDF: wrap bytes as an in-memory file.
    doc = DocxDocument(io.BytesIO(raw_bytes))

    # A Word doc is fundamentally a list of paragraphs. We collect the text of
    # each one. (This gets the body prose; tables are a refinement we can add
    # later if needed — for most documents, paragraphs are the substance.)
    paragraphs = [para.text for para in doc.paragraphs]

    # Join with newlines, drop empty paragraphs' noise via strip at the end.
    return "\n".join(paragraphs).strip()