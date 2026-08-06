import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import settings
from app.core import storage
from app.db.session import get_db
from app.models.users import User
from app.schemas.document import DocumentRead
from app.services import document as document_service
from app.worker.tasks import process_document

router = APIRouter(prefix="/documents", tags=["documents"])

# The file types we accept for now. Rejecting anything else up front is a
# security and sanity measure — we don't want arbitrary executables, etc.
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # .pptx
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    "text/plain",
}


@router.post("", response_model=DocumentRead, status_code=201)
async def upload_document(
    # UploadFile is FastAPI's type for a multipart file upload. It streams the
    # file (doesn't load it fully into RAM) and exposes .filename, .content_type,
    # and a .file stream. This is the "special mechanism" I mentioned.
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),   # must be logged in to upload
):
    # 1) VALIDATE TYPE — reject anything not in our allowlist.
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}",
        )

    # 2) VALIDATE SIZE — read the stream to its end to measure it, guarding
    # against files bigger than our cap. We seek back to 0 afterward so the
    # upload re-reads from the start. (A more advanced version enforces this
    # while streaming; measuring first is clearer for now.)
    contents = await file.read()
    size_bytes = len(contents)
    if size_bytes > settings.max_upload_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds the maximum allowed size",
        )
    file.file.seek(0)

    # 3) BUILD A SAFE OBJECT KEY. We do NOT trust the user's filename for the
    # storage path (it could contain "../" or collide with another file).
    # Instead we generate a fresh uuid and keep the real extension for clarity,
    # and prefix with the org id so each tenant's blobs are grouped.
    suffix = ""
    if "." in file.filename:
        suffix = "." + file.filename.rsplit(".", 1)[1].lower()
    object_key = f"{current_user.organization_id}/{uuid.uuid4()}{suffix}"

    # 4) STORE THE BYTES in MinIO first. If this fails, we never write a DB row
    # pointing at a blob that doesn't exist.
    storage.upload_fileobj(file.file, object_key, file.content_type)

    # 5) RECORD METADATA in Postgres, pointing at the stored blob. The org id
    # comes from the authenticated user — same isolation principle as everywhere.
    document = await document_service.create_document(
        db,
        organization_id=current_user.organization_id,
        uploaded_by=current_user.id,
        filename=file.filename,      # keep original name for DISPLAY only
        content_type=file.content_type,
        size_bytes=size_bytes,
        object_key=object_key,
    )
    # HAND OFF THE SLOW WORK. .delay(...) pushes a job onto the Redis queue and
    # returns instantly — it does NOT wait for the task to finish. The worker
    # picks it up moments later in its own process. This one line is the whole
    # point of 3b: the response returns now; processing happens out of band.
    process_document.delay(str(document.id))
    return document