# Backend Dockerfile
FROM python:3.11

# Set the working directory
WORKDIR /backend

# Copy the application
COPY . .

# Install all dependencies
RUN pip install -e .

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --start-interval=1s --retries=3 CMD [ "curl", "-f", "http://localhost:8000/ok" ]

ENTRYPOINT [ "uvicorn", "app.server:app", "--host", "0.0.0.0", "--log-config", "log_config.json" ]
