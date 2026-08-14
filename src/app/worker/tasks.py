import uuid

from app.core import storage
from app.extraction.dispatcher import extract_text   # NEW import
from app.models.document import Document, DocumentStatus
from app.worker.celery_app import celery_app
from app.worker.db import SyncSessionLocal
from app.extraction.chunking import chunk_text                
from app.services.document import create_chunks_sync
from app.core.embeddings import embed_texts                 # NEW


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
            # 1) Fetch bytes and extract text (Phase 4).
            body = storage.download_fileobj(document.object_key)
            raw_bytes = body.read()
            text = extract_text(document.content_type, raw_bytes)

            # 2) Empty-text guard (scanned PDF etc.) -> FAILED, stop.
            if not text.strip():
                document.status = DocumentStatus.FAILED
                document.extracted_text = "[no extractable text — possibly a scanned/image PDF]"
                db.commit()
                return

            document.extracted_text = text

            # 3) Chunk the text (Phase 4c).
            pieces = chunk_text(text)

            # 4) NEW: embed all chunks in one batched OpenAI call.
            vectors = embed_texts(pieces)

            # 5) NEW: store chunks + their vectors together.
            create_chunks_sync(
                db,
                document_id=document.id,
                organization_id=document.organization_id,
                chunk_texts=pieces,
                embeddings=vectors,
            )

            # 6) Only NOW mark it processed — text extracted, chunked, embedded.
            document.status = DocumentStatus.PROCESSED
            db.commit()

        except Exception:
            document.status = DocumentStatus.FAILED
            db.commit()
            raise