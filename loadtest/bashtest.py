#!/bin/bash

# Set the directory containing PDF files
pdf_dir="./pdfs"

# Infinite loop to continuously pick a random PDF file every 2 seconds
while true; do
    random_pdf=$(ls "$pdf_dir"/*.pdf | shuf -n 1)
    echo "\n\nSelected PDF file: $random_pdf"

    curl -X 'POST' 'http://127.0.0.1:8000/documents' -H 'accept: application/json' -H 'Content-Type: multipart/form-data' -F "pdf_file=@$random_pdf;type=application/pdf"

done

