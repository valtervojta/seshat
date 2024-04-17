import random
import time
from pathlib import Path

from locust import HttpUser, between, task

PDF_FILES_PATH = Path("loadtest/pdfs")


def get_random_pdf():
    files = PDF_FILES_PATH.iterdir()
    pdf_files = [f for f in files if f.is_file() and f.suffix == ".pdf"]
    return random.choice(pdf_files)


class HelloWorldUser(HttpUser):
    pdf_doc_id = None

    @task
    def get_docs(self):
        self.client.get(f"/documents/{self.pdf_doc_id}/pages/1")

    wait_time = between(2, 3)

    def on_start(self):
        random_pdf = get_random_pdf()
        with open(random_pdf, "rb") as f:
            response = self.client.post(
                "/documents",
                files={"pdf_file": (random_pdf.name, f, "application/pdf")},
            )
            self.pdf_doc_id = response.json()["id"]
        time.sleep(5)
