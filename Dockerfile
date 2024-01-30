FROM node:18 AS builder

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

# Set the working directory
WORKDIR /backend

COPY ./backend .

RUN rm poetry.lock

RUN pip install .

# Copy the frontend build
COPY --from=builder /frontend/dist ./ui

ENTRYPOINT [ "uvicorn", "app.server:app", "--host", "0.0.0.0" ]
