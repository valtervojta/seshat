import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import aiofiles
from fastapi import FastAPI, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from pydantic import UUID4
from sqlmodel import Session, select

from app.db import create_db_and_tables, engine
from app.models import Document, DocumentStatus, DocumentUnique
from app.settings import PAGES_PATH, UPLOADS_PATH, settings
from app.utils import get_file_hash
from app.worker import render_pdf_document

api_description = (
    "Seshat API swiftly ingests countless PDF documents and renders them as PNG images. "
    "\n## Documents\n\nYou can **upload** PDF files and **check** on their processing status.)"
    "\n## Document pages\nYou can get beautifully rendered pages of the documents you uploaded "
    "(you only need to wait seconds for processing)."
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Ensured to execute before application startup.
    See: https://fastapi.tiangolo.com/advanced/events/
    """
    create_db_and_tables()
    yield


app = FastAPI(
    title="Seshat API",
    lifespan=lifespan,
    summary="PDF ingest and rendering API",
    version="0.9.1",
    description=api_description,
    swagger_ui_parameters={"tryItOutEnabled": True, "defaultModelsExpandDepth": -1},
)

tags_metadata = [
    {
        "name": "core",
        "description": "Core endpoints defined in the assignment.",
    },
    {
        "name": "dev",
        "description": "Additional endpoints defined to showcase more functionality.",
    },
]


@app.post("/documents", status_code=status.HTTP_202_ACCEPTED, tags=["core"])
async def upload_document(pdf_file: UploadFile) -> Response:
    """
    The main ingestion endpoint, gets a multipart UploadFile, checks if it is a PDF,
    creates a database object for it, async saves it to storage and then offloads the render task to a worker.
    This allows users to later retrieve rendered pages of the uploaded document.

    Raises HTTPException 415 if the uploaded file does not have content type PDF.
    Does no deeper validation of the uploaded file.

    \f
    :param pdf_file: The uploaded PDF file.
    :return: JSON response with document ID that can be later used to look up processing status
    or request rendered pages.
    """
    UPLOADS_PATH.mkdir(parents=True, exist_ok=True)
    PAGES_PATH.mkdir(parents=True, exist_ok=True)

    # Save the uploaded pdf_file to disk, basic type check
    if pdf_file.content_type != "application/pdf":
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Invalid document type."
        )

    with Session(engine) as session:
        document = Document(
            original_filename=str(pdf_file.filename), status=DocumentStatus.PROCESSING
        )
        session.add(document)
        session.commit()
        session.refresh(document)

    storage_filepath = Path(UPLOADS_PATH / f"{str(document.id)}.pdf")
    async with aiofiles.open(storage_filepath, "wb") as f:
        print(f"Saving file to {storage_filepath}.")
        while chunk := await pdf_file.read(settings.UPLOAD_CHUNK_SIZE):
            await f.write(chunk)
        render_pdf_document.send(str(document.id))

    return JSONResponse(
        content={"id": str(document.id)}, status_code=status.HTTP_202_ACCEPTED
    )


@app.get("/documents/{document_id:uuid}", tags=["core"])
def get_document(document_id: UUID4) -> JSONResponse:
    """
    Gets a specific document (Document) by ID and returns its status and number of pages.
    Status can be processing, done or error. If document was not yet processed, number of pages will be 0.

    Raises HTTPException 404 if a document with this ID does not exist.

    \f
    :param document_id: UUID4 of the desired document (assumedly obtained through the /documents endpoint)
    :return: JSON response dictionary contaning the status of the document and number of its pages.
    """
    with Session(engine) as session:
        document = session.get(Document, document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with id {document_id} does not exist.",
            )
        return JSONResponse(
            content={"status": document.status, "n_pages": document.n_pages},
            status_code=200,
        )


@app.get(
    "/documents/{document_id:uuid}/pages/{page_number}",
    response_class=FileResponse,
    tags=["core"],
)
def get_document_page(document_id: UUID4, page_number: int):
    """
    Attempts to get a specific page of the document with the given ID.
    The document has to exists in the database, its processing has to be finished (status = done)
    and the page number has to be in range of the documents existing pages.

    Raises HTTPException 404 if any of the conditions above are not met or the file is not found in storage.

    \f
    :param document_id: UUID4 of the desired document.
    :param page_number: Page number of the desired page, indexing from 1.
    :return: A PNG file containing the rendered page of the document.
    """
    with Session(engine) as session:
        document = session.get(Document, document_id)

        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"Document with id {document_id} does not exist.",
            )

        if not document.status or document.status is not DocumentStatus.DONE:
            raise HTTPException(
                status_code=404,
                detail=f"Document with id {document_id} is not yet processed. Status: {document.status}",
            )

        if document.n_pages and page_number > document.n_pages:
            raise HTTPException(
                status_code=404,
                detail=f"Page {page_number} does not exist for document {document_id}.",
            )

        image_path = PAGES_PATH / f"{document_id}_{page_number}.png"

        if image_path.is_file():
            return FileResponse(
                path=image_path,
                status_code=200,
            )

        else:
            raise HTTPException(
                status_code=404,
                detail=f"Page {page_number} does not exist for document {document_id}.",
            )


# Additional / Extra endpoints
@app.get("/documents", tags=["dev"], include_in_schema=False)
def get_documents() -> list[Document]:
    """
    Gets all existing Documents in the database, all fields.
    Does not return other models, such as experimental DocumentUnique.

    \f
    :return: List of JSON dicts, one for each Document.
    """
    with Session(engine) as session:
        documents = session.exec(select(Document)).all()
        return list(documents)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


@app.post(
    "/documents_unique",
    status_code=status.HTTP_202_ACCEPTED,
    tags=["dev"],
    include_in_schema=False,
)
async def upload_document(pdf_file: UploadFile) -> Response:
    """
    A variant of the POST /documents endpoint that first computes a SHA256 hash of the
    uploaded file and only then creates a database object. This is intended to save space in case of duplicate
    uploads. If an object already exists, its ID is returned as normal (but no render task is sent).

    End users should not be aware that the document was already uploaded for security and privacy reasons.

    Raises HTTPException 415 if the uploaded file does not have content type PDF.
    Does no deeper validation of the uploaded file.

    \f
    :param pdf_file: The uploaded PDF file.
    :return: JSON response with document ID that can be later used to look up processing status
    or request rendered pages.
    """
    UPLOADS_PATH.mkdir(parents=True, exist_ok=True)
    PAGES_PATH.mkdir(parents=True, exist_ok=True)

    # Save the uploaded pdf_file to disk, basic type check
    if pdf_file.content_type != "application/pdf":
        raise HTTPException(400, detail="Invalid document type.")

    uploaded_file_uuid = uuid.uuid4
    storage_filepath = Path(UPLOADS_PATH / f"{str(uploaded_file_uuid)}.pdf")
    async with aiofiles.open(storage_filepath, "wb") as f:
        print(f"Saving file to {storage_filepath}.")
        while chunk := await pdf_file.read(settings.UPLOAD_CHUNK_SIZE):
            await f.write(chunk)

    file_hash = get_file_hash(storage_filepath)
    with Session(engine) as session:
        existing_document = session.get(DocumentUnique, file_hash)
        if not existing_document:
            document = DocumentUnique(
                id=file_hash,
                original_filename=str(pdf_file.filename),
                status=DocumentStatus.PROCESSING,
            )
            session.add(document)
            session.commit()
            session.refresh(document)
            # render_pdf_document.send(document.id) - would have to rewrite worker logic since it is model based
        else:
            return JSONResponse(
                content={"id": str(existing_document.id)}, status_code=200
            )
    return JSONResponse(content={"id": str(document.id)}, status_code=200)
