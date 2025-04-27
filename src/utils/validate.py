from pathlib import Path
from typing import List


def validate_files(file_paths: List[str]) -> List[Path]:
    """
    Validate input file paths and return existing regular files as Path objects.

    Raises:
        FileNotFoundError: If a file does not exist or is not a regular file.
    """
    valid_files = []

    for path_str in file_paths:
        path = Path(path_str)
        if not path.is_file():
            raise FileNotFoundError(f"Invalid file: {path}")
        valid_files.append(path)

    return valid_files
