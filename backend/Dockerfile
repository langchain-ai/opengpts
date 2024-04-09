# Backend Dockerfile
FROM python:3.11

ARG TARGETOS
ARG TARGETARCH
ARG TARGETVARIANT

# Install system dependencies
RUN apt-get update && apt-get install -y libmagic1 && rm -rf /var/lib/apt/lists/*
RUN wget -O golang-migrate.deb https://github.com/golang-migrate/migrate/releases/download/v4.17.0/migrate.${TARGETOS}-${TARGETARCH}${TARGETVARIANT}.deb \
    && dpkg -i golang-migrate.deb \
    && rm golang-migrate.deb

# Install Poetry
RUN pip install poetry

# Set the working directory
WORKDIR /backend

# Copy only dependencies
COPY pyproject.toml poetry.lock* ./

# Install all dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Copy the rest of application code
COPY . .

# --start-interval is unsupported and removed since 4.21.1
# see https://github.com/docker/for-mac/issues/6938,
# see https://github.com/docker/cli/issues/4486
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD [ "curl", "-f", "http://localhost:8000/health" ]

ENTRYPOINT [ "uvicorn", "app.server:app", "--host", "0.0.0.0" ]
