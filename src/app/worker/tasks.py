import uuid

from app.core import storage
from app.models.document import Document, DocumentStatus
from app.worker.celery_app import celery_app
from app.worker.db import SyncSessionLocal


# @celery_app.task turns this ordinary function into a Celery task — something
# the API can enqueue and the worker will later run. The string name is how the
# task is referenced across processes.
@celery_app.task(name="process_document")
def process_document(document_id: str) -> None:
    # Note: we pass the document's ID (a string), NOT the Document object. Jobs
    # travel through Redis as simple serialized data, so you send an identifier
    # and re-load the row inside the worker. Never try to send ORM objects.
    doc_uuid = uuid.UUID(document_id)

    # Open a SYNC session for this task. "with" ensures it's closed afterward.
    with SyncSessionLocal() as db:
        document = db.get(Document, doc_uuid)
        if document is None:
            return  # row was deleted before we got to it — nothing to do

        # Mark it PROCESSING so anyone watching sees work has begun.
        document.status = DocumentStatus.PROCESSING
        db.commit()

        try:
            # Pull the file's bytes back out of MinIO using the stored key.
            body = storage.download_fileobj(document.object_key)
            raw_bytes = body.read()

            # For 3b we do the SIMPLEST possible "extraction": decode text files,
            # and for now just record the byte count for binary types. REAL
            # per-format extraction (PDF/DOCX/PPTX/XLSX) is Phase 4 — here we're
            # only proving the async pipeline works end to end.
            if document.content_type == "text/plain":
                document.extracted_text = raw_bytes.decode("utf-8", errors="ignore")
            else:
                document.extracted_text = f"[binary file: {len(raw_bytes)} bytes, extraction in Phase 4]"

            # Success — flip to PROCESSED.
            document.status = DocumentStatus.PROCESSED
            db.commit()

        except Exception:
            # ANY failure: mark FAILED and re-raise so Celery logs it. Never
            # leave a document stuck in PROCESSING forever.
            document.status = DocumentStatus.FAILED
            db.commit()
            raise