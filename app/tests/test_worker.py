from pathlib import Path

import pytest

from app.tests.conftest import TEST_FILES_PATH
from app.worker import render_and_save_pages, render_pdf_document


# Distributed test example, pseudocode
@pytest.mark.skip
def test_render_pdf_document(stub_broker, stub_worker):
    _test_file = Path(TEST_FILES_PATH, "valid_0.pdf")
    document_id = "some valid document id, set up before test"
    render_pdf_document.send(document_id)
    stub_broker.join(render_pdf_document.queue_name, fail_fast=True)
    stub_worker.join()


# Sync test example, pseudocode
@pytest.mark.skip
def test_render_and_save_pages_sync():
    _test_file = Path(TEST_FILES_PATH, "valid_0.pdf")
    document_id = "some valid document id, set up before test"
    render_and_save_pages(document_id)

    # look directly in file system and check those pages
