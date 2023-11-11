"""Shallow tests that make sure we can at least import the code."""

import os

from pytest import MonkeyPatch


def test_redis_url_set() -> None:
    """Verify that the redis URL is set."""
    if "REDIS_URL" not in os.environ:
        raise AssertionError(
            "REDIS_URL not set in environment. "
            "You can run docker-compose from the root directory to get redis up and "
            # Simplify the instructions for running the tests
            "running. Then run the tests with `REDIS_URL=... make test`."
        )
    # Use database 3 for unit tests
    # Poorman's convention for accidentally wiping out an actual database
    # Should change ports in a bit and add a fake test password
    assert os.environ["REDIS_URL"].endswith("/3")


def test_agent_executor() -> None:
    """Test agent executor."""
    # Shallow test to verify that teh code can be imported
    import agent_executor  # noqa: F401


def test_gizmo_agent() -> None:
    """Test gizmo agent."""
    # Shallow test to verify that teh code can be imported
    with MonkeyPatch.context() as mp:
        mp.setenv("OPENAI_API_KEY", "no_such_key")
        import gizmo_agent  # noqa: F401


def test_import_app() -> None:
    """Test import app"""
    import app  # noqa: F401
