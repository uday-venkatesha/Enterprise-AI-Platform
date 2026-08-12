import io

from pypdf import PdfReader


def extract_text_from_pdf(raw_bytes: bytes) -> str:
    # pypdf needs a file-like object, not raw bytes. io.BytesIO wraps our bytes
    # in memory so PdfReader can read them as if they were an opened file —
    # no temp file on disk needed.
    reader = PdfReader(io.BytesIO(raw_bytes))

    # A PDF is a list of pages; text lives per-page. We pull each page's text
    # and collect them.
    pages_text: list[str] = []
    for page in reader.pages:
        # extract_text() returns the page's text, or None if the page has none
        # (e.g. a scanned image page). "or ''" turns that None into an empty
        # string so the join below never crashes.
        page_text = page.extract_text() or ""
        pages_text.append(page_text)

    # Join pages with a blank line between them, so page boundaries are visible
    # in the combined text. .strip() trims leading/trailing whitespace.
    return "\n\n".join(pages_text).strip()