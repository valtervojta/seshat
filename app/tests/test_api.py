from pathlib import Path
from time import sleep

from fastapi.testclient import TestClient

from app.tests.conftest import TEST_FILES_PATH

"""
    A few example test for the API endpoints themselves.
    Generally the assert count should be higher on each test.

    What tests should be added:
        all endpoints
            auth, rate limits etc
        upload_document
            empty file, non-PDF, corrupted file, locked file, connection loss during upload, PDF that cannot be parsed,
            PDF that is too big (if size limit is implemented)
        get_document
            wrong ID format, existing, non-existing object, object with processing/done/error status, various n_pages,
            if implemented, accessible/inaccessible document
        get_document_page
            wrong ID format, existing, non-existing object, object with processing/done/error status, proper page,
            out of bounds page, wrong page number format, negative, 0 etc, file not found, file unopenable?
            if implemented, accessible/inaccessible pages
            
    Also, in a separate test file, we could test app startup, database connection, message queue connection etc in 
    order to fail tests early and decisively if key things do not work.
"""


def test_upload_document(client: TestClient):
    _test_upload_file = Path(TEST_FILES_PATH, "valid_0.pdf")
    with open(_test_upload_file, "rb") as f:
        response = client.post(
            "/documents", files={"pdf_file": ("valid_0.pdf", f, "application/pdf")}
        )
        assert response.status_code == 202


def test_get_document_not_existing(client: TestClient):
    valid_document_id = "91db6a4d-9849-42d7-b3b7-5b352c706879"
    response = client.get(f"/documents/{valid_document_id}")
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Document with id 91db6a4d-9849-42d7-b3b7-5b352c706879 does not exist."
    }


def test_get_document_does_exist(client: TestClient):
    _test_upload_file = Path(TEST_FILES_PATH, "valid_0.pdf")
    with open(_test_upload_file, "rb") as f:
        response = client.post(
            "/documents", files={"pdf_file": ("valid_0.pdf", f, "application/pdf")}
        )
        valid_id = response.json()["id"]
    response = client.get(f"/documents/{valid_id}")
    assert response.status_code == 200
    assert response.json() == {"status": "processing", "n_pages": 0}


def test_get_document_page(client: TestClient):
    """
    A better image comparison should be included. For starters, we could use the same PDF engine that
    workers use and pre-generate the pages for this test and then compare them.
    """
    _test_upload_file = Path(TEST_FILES_PATH, "valid_0.pdf")
    with open(_test_upload_file, "rb") as f:
        response = client.post(
            "/documents", files={"pdf_file": ("valid_0.pdf", f, "application/pdf")}
        )
        valid_id = response.json()["id"]
    sleep(0.5)
    while True:
        response = client.get(f"/documents/{valid_id}")
        if response.json()["status"] == "done":
            break
        sleep(0.5)
    response = client.get(f"/documents/{valid_id}/pages/1")
    assert response.status_code == 200
    with open("./test.png", "wb") as f:
        f.write(response.content)
    from PIL import Image

    img = Image.open("./test.png")
    assert img.format == "PNG"
