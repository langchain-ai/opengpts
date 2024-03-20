FROM node:20 AS builder

WORKDIR /frontend

COPY ./frontend/package.json ./frontend/yarn.lock ./

RUN yarn --network-timeout 600000 --frozen-lockfile

COPY ./frontend ./

RUN rm -rf .env

RUN yarn build

# Backend Dockerfile
FROM python:3.11

# Install system dependencies
RUN apt-get update && apt-get install -y libmagic1 && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Set the working directory
WORKDIR /backend

# Copy only dependencies
COPY ./backend/pyproject.toml ./backend/poetry.lock* ./

# Install dependencies
# --only main: Skip installing packages listed in the [tool.poetry.dev-dependencies] section
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --only main

# Copy the rest of backend
COPY ./backend .

# Copy the frontend build
COPY --from=builder /frontend/dist ./ui

ENTRYPOINT [ "uvicorn", "app.server:app", "--host", "0.0.0.0" ]
