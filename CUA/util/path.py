from pathlib import Path


def project_root_path() -> Path:
    """Returns the root of the project, where the `pyproject.toml` lives

    Returns:
        Path: Project root path
    """
    current_file = Path(__file__)  # util.py
    return current_file.parent.parent.parent  # top-module -> root


def module_root_path() -> Path:
    """Returns the root of the module / python library.

    Returns:
        Path: Module root path
    """
    current_file = Path(__file__)  # util.py
    return current_file.parent.parent  # util.py -> top-module
