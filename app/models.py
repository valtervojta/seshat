import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import UUID4
from sqlmodel import Field, SQLModel


class DocumentStatus(str, Enum):
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


class Document(SQLModel, table=True):
    id: UUID4 = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    original_filename: Optional[str] = Field(default=None)
    status: DocumentStatus = DocumentStatus.PROCESSING
    n_pages: Optional[int] = Field(ge=0, default=0)


class DocumentUnique(SQLModel, table=True):
    id: str = Field(primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    original_filename: Optional[str] = Field(default=None)
    status: DocumentStatus = DocumentStatus.PROCESSING
    n_pages: Optional[int] = Field(ge=0, default=0)
