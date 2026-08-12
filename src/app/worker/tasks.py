import uuid

from app.core import storage
from app.extraction.dispatcher import extract_text   # NEW import
from app.models.document import Document, DocumentStatus
from app.worker.celery_app import celery_app
from app.worker.db import SyncSessionLocal


@celery_app.task(name="process_document")
def process_document(document_id: str) -> None:
    doc_uuid = uuid.UUID(document_id)

    with SyncSessionLocal() as db:
        document = db.get(Document, doc_uuid)
        if document is None:
            return

        document.status = DocumentStatus.PROCESSING
        db.commit()

        try:
            body = storage.download_fileobj(document.object_key)
            raw_bytes = body.read()

            # --- THIS is the real change: dispatch to the right extractor ---
            text = extract_text(document.content_type, raw_bytes)

            # Guard against "extracted nothing useful." A scanned PDF returns an
            # empty string — that's not a crash, but it IS a document we can't
            # use downstream, so we flag it clearly instead of storing "".
            if not text.strip():
                document.status = DocumentStatus.FAILED
                document.extracted_text = "[no extractable text — possibly a scanned/image PDF]"
                db.commit()
                return

            document.extracted_text = text
            document.status = DocumentStatus.PROCESSED
            db.commit()

        except Exception:
            # Any unexpected failure (corrupt file, unknown type, library error)
            # -> mark FAILED and re-raise so Celery logs the traceback.
            document.status = DocumentStatus.FAILED
            db.commit()
            raise