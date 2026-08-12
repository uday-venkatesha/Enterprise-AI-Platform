from app.extraction.pdf import extract_text_from_pdf


# We'll grow this as we add formats in 4b. Mapping content-type -> the function
# that handles it keeps the routing logic in ONE obvious place.
def extract_text(content_type: str, raw_bytes: bytes) -> str:
    if content_type == "application/pdf":
        return extract_text_from_pdf(raw_bytes)

    if content_type == "text/plain":
        # Plain text is already text — just decode. errors="ignore" skips any
        # stray bytes that aren't valid UTF-8 instead of crashing.
        return raw_bytes.decode("utf-8", errors="ignore")

    # A type we don't have an extractor for yet. Raising a clear error is better
    # than silently returning nothing — the caller will mark the doc FAILED and
    # we'll know exactly why.
    raise ValueError(f"No extractor available for content type: {content_type}")