from datetime import datetime
from pathlib import Path

import dramatiq
import pypdfium2 as pdfium
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from dramatiq.brokers.stub import StubBroker
from PIL import Image
from pydantic import UUID4
from pypdfium2 import PdfiumError
from sqlmodel import Session

from app.db import engine
from app.models import Document, DocumentStatus
from app.settings import settings

if settings.UNIT_TESTING:
    broker = StubBroker()
    broker.emit_after("process_boot")
else:
    broker = RabbitmqBroker(
        url=f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}@{settings.RABBITMQ_HOST}:5672"
    )

dramatiq.set_broker(broker)


class IDNotFoundError(Exception):
    """Exception raised when the document ID is not found in the database."""

    pass


# If PdfiumError or IDNotFoundError are thrown, task will not be retried.
@dramatiq.actor(
    max_retries=5,
    max_age=settings.MESSAGE_MAX_AGE_MS,
    throws=(PdfiumError, IDNotFoundError),
)
def render_pdf_document(document_id: str):
    with Session(engine) as session:
        document = session.get(Document, document_id)
        if not document or document.status is not DocumentStatus.PROCESSING:
            error = IDNotFoundError(
                f"DocumentInput for id {document_id} with status {DocumentStatus.PROCESSING} "
                f"was not found."
            )
            raise error

        try:
            num_pages = render_and_save_pages(document_id)
        except PdfiumError as error:
            update_with_error(session, document, error)

        document.status = DocumentStatus.DONE
        document.n_pages = num_pages
        document.updated_at = datetime.utcnow()
        session.add(document)
        session.commit()
        session.refresh(document)


def update_with_error(session: Session, document: Document, error: Exception):
    document.status = DocumentStatus.ERROR
    document.n_pages = 0
    document.updated_at = datetime.utcnow()
    session.add(document)
    session.commit()
    session.refresh(document)

    raise error


def render_and_save_pages(document_id: UUID4) -> int:
    document_path = Path(settings.UPLOADS_PATH / f"{str(document_id)}.pdf")
    pdf_document = pdfium.PdfDocument(document_path)

    num_pages = len(pdf_document)

    for page_number in range(1, num_pages + 1):
        print(f"Processing page {page_number} of document at {document_path}.")
        page = pdf_document[page_number - 1]
        pil_image = page.render(
            scale=1,
            rotation=0,
            crop=(0, 0, 0, 0),
            draw_annots=True,
        ).to_pil()

        width, height = pil_image.size
        if width > 1200 or height > 1600:
            aspect_ratio = width / height

            new_width = min(width, 1200)
            new_height = int(new_width / aspect_ratio)

            if new_height > 1600:
                new_height = 1600
                new_width = int(new_height * aspect_ratio)

            pil_image = pil_image.resize(
                (new_width, new_height), Image.Resampling.LANCZOS
            )
        pil_image.save(settings.PAGES_PATH / f"{document_id}_{page_number}.png")
    return num_pages
