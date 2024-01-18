import os

# Temporary handling of environment variables for testing
os.environ["REDIS_URL"] = "redis://localhost:6379/3"
os.environ["OPENAI_API_KEY"] = "test"
os.environ["YDC_API_KEY"] = "test"
os.environ["TAVILY_API_KEY"] = "test"
