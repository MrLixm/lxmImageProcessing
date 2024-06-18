import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Optional

LOGGER = logging.getLogger(__name__)


def _get_exiftool_executable(exe_path: Optional[Path] = None) -> Optional[Path]:
    """
    Get the path to a valid exiftool system executable.

    If no argument is provided the executable is attempted to be retrieved from:

    * ``EXIFTOOL`` environment variable

    Args:
        exe_path: optional fileystem path to a potential file

    Returns:
        optional fileystem path to an existing executable file
    """
    if exe_path and exe_path.exists():
        return exe_path

    exe_path = os.getenv("EXIFTOOL")
    if exe_path and Path(exe_path).exists():
        return exe_path

    return None


def exiftoolget_raw_output(
    src_path: Path,
    exiftool_path: Optional[Path] = None,
    exiftool_args: Optional[list[str]] = None,
) -> str:
    """
    Get the output of calling exiftool without additional formatting.

    Args:
        src_path: filesystem path to an existing camera file to extract the metadata from.
        exiftool_path: optional fileystem path to a potential exiftool executable
        exiftool_args: list of additional arguments to provide to exiftool

    Returns:
        stdout output of exiftool as decoded str
    """
    exiftool_path = _get_exiftool_executable(exiftool_path)
    if not exiftool_path:
        raise FileNotFoundError(
            "No exiftool executable was provided or able to be found."
        )

    exiftool_args = exiftool_args or []

    command = [str(exiftool_path)]
    command += exiftool_args
    command += [str(src_path)]

    LOGGER.debug(f"calling exiftool with command={command}")
    output = subprocess.check_output(command, cwd=src_path.parent)
    output = output.decode("utf-8", errors="ignore")
    return output


def exiftoolread_image_metadata(
    image_path: Path,
    exiftool_path: Optional[Path] = None,
    exiftool_args: Optional[list[str]] = None,
    extract_binary: bool = False,
) -> dict[str, dict[str, str]]:
    """
    Parse and return the metadata stored in the givne image using exiftools.

    The returned dict is formatted like ::

        {
            "File": {"FileName": "value", ...},
            "EXIF": {"Image Width": "value", ...},
            "XMP": {"Modify Date": "value", ...},
            "MakerNotes": {...},
            ...
        }

    Args:
        image_path: fileystem path to an existing camera file
        exiftool_path:
            optional fileystem path to a potential exiftool executable.
            Guessed if not provided.
        exiftool_args:
            list of additional arguments to provide to exiftool.
            Note if the argument change the formatting then it might break the parsing.
        extract_binary:
            True to extract binary metadata (slower and heavier).
            If False the binary metadata will be replaced with a warning message.

    Returns:
        exif metadata stored in the file as python dict object
        dict is structured with "tags groups" as root keys
    """
    exiftool_args = exiftool_args or []

    exiftool_args += [
        "-D",  # Show tag ID numbers in decimal
        "-G",  # Print group name for each tag
        "-a",  # Allow duplicate tags to be extracted
        "-u",  # Extract unknown tags
        "-n",  # No print conversion
        "-m",  # Ignore minor errors and warnings
        "-sep",  # Set separator character for arrays
        ",",
        "-s",  # Short output format (remove whitespace in tag name)
        "-sort",  # Sort output alphabetically
        "-json",  # Export tags in JSON format
    ]

    if extract_binary and "-b" not in exiftool_args:
        exiftool_args.append("-b")

    exiftool_output = exiftoolget_raw_output(image_path, exiftool_path, exiftool_args)

    exif_dict = json.loads(exiftool_output)[0]
    new_exif_dict = {}

    for exif_key, exif_value in exif_dict.items():
        if ":" in exif_key:
            exif_group, exif_name = exif_key.split(":", 1)
            new_exif_dict.setdefault(exif_group, {})[exif_name] = exif_value["val"]
        else:
            new_exif_dict[exif_key] = exif_value

    return new_exif_dict
