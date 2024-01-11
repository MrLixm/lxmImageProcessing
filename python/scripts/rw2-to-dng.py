"""
Convert Panasonic .RW2 raw files to a DNG that can be read by Foundry's Nuke.
"""
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

LOGGER = logging.getLogger(Path(__file__).stem)

INPUT_DIR = Path(
    r"G:\personal\photo\workspace\dcim\2024\2024_01_11_negscan",
)
OUTPUT_DIR = INPUT_DIR / "dng"
# https://helpx.adobe.com/camera-raw/digital-negative.html#downloads
ADOBE_DNG_EXE = os.getenv("ADOBEDNGTOOL") or Path(
    r"C:\Program Files\Adobe\Adobe DNG Converter\Adobe DNG Converter.exe",
)

OVERWRITE_EXISTING = False


def convert_rw2_to_dng(
    rw2_paths: list[Path],
    target_dir: Path,
    adobe_dng_path: Path,
):
    cmd = [
        str(adobe_dng_path),
        "-u",  # uncompressed (important for Nuke)
        "-mp",  # multi-processing (parallel)
        "-d",  # output directory
        str(target_dir),
    ]
    cmd += [str(input_file) for input_file in rw2_paths]

    LOGGER.debug(f"calling AdobeDNGConverter with {cmd} ...")

    process_out = subprocess.check_output(cmd)
    process_out = process_out.decode("utf-8")
    LOGGER.debug(process_out)
    return target_dir


def main():
    output_dir = OUTPUT_DIR
    input_files = list(INPUT_DIR.glob("*.RW2"))
    if not input_files:
        LOGGER.warning("no file found, returning ...")
        return

    for input_file in list(input_files):
        if (
            output_dir / input_file.with_suffix(".dng").name
        ).exists() and not OVERWRITE_EXISTING:
            LOGGER.info(f"skipping {input_file}, output already exists")
            input_files.remove(input_file)

    if not output_dir.exists():
        output_dir.mkdir()

    start_time = time.time()

    LOGGER.info(f"started processing {len(input_files)} files to dng")
    convert_rw2_to_dng(input_files, output_dir, ADOBE_DNG_EXE)
    LOGGER.info(f"finished in {time.time() - start_time:.2f}s")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="{levelname: <7} | {asctime} [{name}] {message}",
        style="{",
        stream=sys.stdout,
    )
    main()
