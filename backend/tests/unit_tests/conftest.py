import os

# Temporary handling of environment variables for testing
os.environ["REDIS_URL"] = "redis://localhost:6379/3"
os.environ["OPENAI_API_KEY"] = "test"
