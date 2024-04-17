FROM python:3.10-slim

RUN apt-get update && apt-get install -y procps && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["locust", "--host", "http://api:8000", "-f", "main.py"]

