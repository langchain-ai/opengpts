"""Shallow tests that make sure we can at least import the code."""
import os

import pytest
from pytest import MonkeyPatch


def test_agent_executor() -> None:
    """Test agent executor."""
    # Shallow test to verify that teh code can be imported
    import agent_executor  # noqa: F401


@pytest.mark.skip(reason="No redis server yet during tests")
def test_gizmo_agent() -> None:
    """Test gizmo agent."""
    # Shallow test to verify that teh code can be imported
    with MonkeyPatch.context() as mp:
        mp.setenv("REDIS_URL", "redis://nosuchhost:0")
        mp.setenv("OPENAI_API_KEY", "no_such_key")
        import gizmo_agent  # noqa: F401


def test_import_app() -> None:
    """Test import app"""
    import app  # noqa: F401
