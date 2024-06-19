import asyncio
import os

import pytest

from app.auth.settings import AuthType
from app.auth.settings import settings as auth_settings

auth_settings.auth_type = AuthType.NOOP

# Temporary handling of environment variables for testing
os.environ["OPENAI_API_KEY"] = "test"


@pytest.fixture(scope="session")
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
