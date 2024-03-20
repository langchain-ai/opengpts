# Backend Dockerfile
FROM python:3.11

# Install system dependencies
RUN apt-get update && apt-get install -y libmagic1 && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Set the working directory
WORKDIR /backend

# Copy only dependencies
COPY pyproject.toml poetry.lock* ./

# Install dependencies
# --only main: Skip installing packages listed in the [tool.poetry.dev-dependencies] section
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --only main

# Copy the rest of application code
COPY . .

ENTRYPOINT [ "uvicorn", "app.server:app", "--host", "0.0.0.0" ]
