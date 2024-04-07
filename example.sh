#!/bin/bash

filename=$1
output_filename=$2

if [ $# -eq 0 ]; then
    echo "Takes a PDF file as input parameter, uploads it, waits for processing, gets first page as PNG and saves it.
    Usage: $0 <input_filename> <output_filename>"
    exit 1
fi

check_document_status() {
    local doc_id=$1
    echo "Checking status of document $doc_id"
    while true; do
        response=$(curl -X 'GET' "http://127.0.0.1:8000/documents/$doc_id")
        status=$(echo "$response" | jq -r '.status')
        if [ "$status" = "done" ]; then
            echo "Document status is now processed."
            break
        else
            echo "Document status is: $status"
        fi
        sleep 2
    done
}

echo "Upload request"
upload_response=$(curl -X 'POST' \
'http://127.0.0.1:8000/documents' \
-H 'accept: application/json' \
-H 'Content-Type: multipart/form-data' \
-F "pdf_file=@$filename;type=application/pdf")

document_id=$(echo "$upload_response" | jq -r '.id')
echo "Extracted document id: $document_id"

check_document_status "$document_id"

echo "Downloading page 1 of the document $document_id and saving it to $output_filename"
curl -X 'GET' "http://127.0.0.1:8000/documents/$document_id/pages/1" \
  --output "$output_filename"