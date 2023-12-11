# Backend Dockerfile
FROM python:3.11

# Install system dependencies
RUN apt-get update && apt-get install -y libmagic1 && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /backend

COPY . .

RUN rm poetry.lock

RUN pip install .

CMD exec uvicorn app.server:app --host 0.0.0.0 --port $PORT
