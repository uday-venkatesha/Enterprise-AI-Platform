def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> list[str]:
    if not text:
        return []

    chunks: list[str] = []
    start = 0
    text_length = len(text)

    while start < text_length:
        # The end of this chunk (Python slicing safely handles going past the end).
        end = start + chunk_size
        # Slice out this window and trim whitespace at its edges.
        chunk = text[start:end].strip()
        # Skip windows that were only whitespace.
        if chunk:
            chunks.append(chunk)

        # THE KEY LINE: advance by (chunk_size - overlap), NOT chunk_size. Moving
        # forward less than a full chunk is exactly what makes consecutive chunks
        # overlap. With size=800, overlap=150, we advance 650 chars each step, so
        # the last 150 chars of one chunk reappear at the start of the next.
        start += chunk_size - overlap

    return chunks