from pathlib import Path
from typing import List

HERE = Path(__file__).parent

# PUBLIC API


def list_fixtures() -> List[Path]:
    """List all fixtures."""
    return list(HERE.glob("sample.*"))
