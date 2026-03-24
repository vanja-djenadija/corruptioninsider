"""
Shared path resolution utilities for the data pipeline.
"""

from pathlib import Path

# Resolve data-pipeline root directory once
_util_dir = Path(__file__).resolve().parent  # util/
_app_dir = _util_dir.parent  # app/
DATA_PIPELINE_ROOT = _app_dir.parent  # data-pipeline/


def resolve_path(path_str: str) -> Path:
    """
    Resolve a path string relative to data-pipeline root.

    Args:
        path_str: Path string (absolute or relative)

    Returns:
        Absolute Path object
    """
    path = Path(path_str)
    if path.is_absolute():
        return path
    return (DATA_PIPELINE_ROOT / path).resolve()
