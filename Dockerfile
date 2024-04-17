FROM python:3.10-slim as base

LABEL version="0.9"

RUN apt-get update && apt-get install -y procps && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

FROM base as api

WORKDIR /code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./app ./app
EXPOSE 8000

FROM api as dev

COPY ./developer/dev-requirements.txt .
RUN pip install --no-cache-dir -r dev-requirements.txt
COPY ./developer .

FROM dev as dev-loadtest
EXPOSE 8089