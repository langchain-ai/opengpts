from pathlib import Path
from typing import List

HERE = Path(__file__).parent

# PUBLIC API


def get_sample_paths() -> List[Path]:
    """List all fixtures."""
    return list(HERE.glob("sample.*"))
