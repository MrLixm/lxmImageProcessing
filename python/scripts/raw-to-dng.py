"""
Convert all RAW file formats known in the given directory, to DNG.

Ignore files which are already converted to DNG.
"""
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

LOGGER = logging.getLogger(Path(__file__).stem)

INPUT_DIR = Path(
    r"F:\assets\data\imgstock\librairy\cameraraws",
)
# https://helpx.adobe.com/camera-raw/digital-negative.html#downloads
ADOBE_DNG_EXE = os.getenv("ADOBEDNGTOOL") or Path(
    r"C:\Program Files\Adobe\Adobe DNG Converter\Adobe DNG Converter.exe",
)
ADOBE_DNG_ARGS = [
    "-u",  # uncompressed
    "-mp",  # multi-processing (parallel)
]
RAW_EXTENSIONS = [
    ".NEF",
    ".CR2",
    ".ORF",
    ".RW2",
    ".RAF",
    ".ARW",
]


def convert_raw_to_dng(
    raw_paths: list[Path],
    adobe_dng_path: Path,
    adobe_dng_args: list[str],
):
    cmd = [str(adobe_dng_path)]
    cmd += adobe_dng_args
    cmd += [str(input_file) for input_file in raw_paths]

    LOGGER.debug(f"calling AdobeDNGConverter with {cmd} ...")

    process_out = subprocess.check_output(cmd)
    process_out = process_out.decode("utf-8")
    LOGGER.debug(process_out)


def find_raw_files(src_dir: Path, raw_extensions: list[str]):
    input_files = list(src_dir.rglob("*"))
    input_files = [
        file
        for file in input_files
        if file.suffix.upper() in raw_extensions
        and not file.with_suffix(".DNG").exists()
    ]
    input_files.sort()
    return input_files


def main():
    input_files = find_raw_files(INPUT_DIR, RAW_EXTENSIONS)
    if not input_files:
        LOGGER.warning("no file found, returning ...")
        return

    start_time = time.time()

    LOGGER.info(f"started processing {len(input_files)} files to dng")
    convert_raw_to_dng(input_files, ADOBE_DNG_EXE, ADOBE_DNG_ARGS)
    LOGGER.info(f"finished in {time.time() - start_time:.2f}s")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="{levelname: <7} | {asctime} [{name}] {message}",
        style="{",
        stream=sys.stdout,
    )
    main()
