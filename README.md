# Seshat API
## Setup

```bash
docker compose up -d
```

Launch time without build should be under a minute.

Seshat API has auto-generated documentation and if it runs, you can access it at:
* http://localhost:8000 (redirects to /docs)
* http://localhost:8000/docs (Swagger)
* http://localhost:8000/redoc (ReDoc)


## Run a PDF to PNG pages conversion
### Use example.sh script
You can use a packaged **example.sh** script to upload document and gets its first page rendered as PNG.
```bash
sh ./example.sh some.pdf output_page.png
```

### Curl
Assuming your PDF file is named **example.pdf**.

#### Upload document
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/documents' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'pdf_file=@example.pdf;type=application/pdf'

# You should get a response like this
{"id":"9c795aca-a026-431d-891b-985233b873b8"}
```
#### Check the document's status
Assuming **document_id** is the document id retrieved in the previous step.

```bash
curl -X 'GET' "http://127.0.0.1:8000/documents/<document_id>"
```

You should get a response with a dictionary like this:

Depending on the size and validity of the uploaded PDF you will get one of these responses:
```json
{"status":"processing","n_pages":5}
```

Where **status** can be either processing, done or error and **n_pages** is an integer (0 in case of processing/error).

#### Get the pages as PNGs
Assuming **document_id** is a valid ID of a processed document and **page_number** is between 1 and the amount of pages the document has.

```bash
curl -X 'GET' "http://127.0.0.1:8000/documents/<document_id>/pages/<page_number>" \
  --output page.png
```

You should now see the page downloaded as **_page.png_** in the current directory.

## Logs
```bash
docker compose logs api         # API logs
docker compose logs workers     # workers logs
docker compose logs db          # database logs
docker compose logs rabbitmq    # message queue logs
```