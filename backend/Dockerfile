FROM python:3.11-slim-bookworm

RUN apt-get update && \
    apt-get install -y libmagic1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN adduser --uid 1000 --disabled-password --gecos '' appuser
USER 1000

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/appuser/.local/bin:$PATH"

RUN pip install --user --no-cache-dir --upgrade pip && \
    pip install --user --no-cache-dir poetry

COPY . /home/appuser/backend/
WORKDIR /home/appuser/backend
RUN poetry install --no-interaction --no-root
