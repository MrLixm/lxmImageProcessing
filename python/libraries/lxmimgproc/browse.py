import logging
import os
from pathlib import Path

LOGGER = logging.getLogger(__name__)


def get_dir_content(
    src_dir: Path,
    recursive=True,
    file_extensions: list[str] = None,
) -> list[Path]:
    """
    Return a list of paths this directory contains.

    Return the whole files and directory tree if recursive=True.
    Be aware that recursive parsing can take some time for big file trees.

    Args:
        src_dir: filesystem path to an existing directory
        recursive: True to recursively process subdirectories
        file_extensions:
            list of file extension with the dot.
            if provided only file mathcing those extensiosn are returned.
            else all files and directories are returned.

    Returns:
        list of absolute existing paths to file and directories
    """
    file_extensions = file_extensions or []

    children = os.scandir(src_dir)

    recursive_children = []

    for child_entry in children:
        child_path = Path(child_entry.path)

        if (
            child_path.is_file()
            and file_extensions
            and child_path.suffix not in file_extensions
        ):
            continue

        if not (file_extensions and child_path.is_dir()):
            recursive_children.append(child_path)

        if child_entry.is_dir() and recursive:
            recursive_children += get_dir_content(
                child_path,
                recursive=True,
                file_extensions=file_extensions,
            )

    return recursive_children
