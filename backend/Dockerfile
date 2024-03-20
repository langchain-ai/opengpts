# Backend Dockerfile
FROM python:3.11

# Install system dependencies
RUN curl -s https://packagecloud.io/install/repositories/golang-migrate/migrate/script.deb.sh | bash
RUN apt-get update && apt-get install -y migrate libmagic1 && rm -rf /var/lib/apt/lists/*

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

ENTRYPOINT [ "uvicorn", "app.server:app", "--host", "0.0.0.0" ]
