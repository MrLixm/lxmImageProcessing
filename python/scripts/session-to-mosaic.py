"""
Merge all images provided to a single big mosaic of images using oiiotool.
"""
import logging
import math
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable

LOGGER = logging.getLogger(Path(__file__).stem)

# https://www.patreon.com/posts/openimageio-oiio-63609827
OIIOTOOL: Path = os.getenv("OIIOTOOL") or Path(
    r"F:\softwares\apps\oiio\build\2.3.10\oiiotool.exe",
)
assert OIIOTOOL.exists()

INPUT_DIR: Path = Path(
    r"G:\personal\photo\workspace\dcim\2023\2023_12_27_tarentaise",
)
OUTPUT_MOSAIC_PATH: Path = INPUT_DIR / "mosaic.jpg"

# number of tiles per row
MOSAIC_COLUMN_NUMBER: int = 6
# space between tiles in pixels
MOSAIC_GAP: int = 15
# scale factor for each image "converted" to a tile
TILE_RESIZE: float = 0.25
# 1.0 means no desqueeze
ANAMORPHIC_DESQUEEZE: float = 1.8


def get_session_jpgs() -> list[Path]:
    return sorted(list(INPUT_DIR.glob("*.jpg")))


FILES_GETTER_CALLABLE: Callable[[], list[Path]] = get_session_jpgs


def generate_image_mosaic(
    src_files: list[Path],
    dst_file: Path,
    mosaic_columns: int,
    mosaic_gap_size: int,
    tile_size: tuple[float, float],
) -> Path:
    """
    Use oiiotool to generate a mosaic of images with the given charcteristics.

    It is recommended all the sources image provided have the same dimensions.

    Mosaic is read from top-left to bottom right.

    Args:
        src_files: list of filesystem paths to existing image files readable by oiiotool
        dst_file: filesystem to a file that may or may not exist.
        mosaic_columns: maximum number of tile per row
        mosaic_gap_size: space between tiles in pixels
        tile_size:
            scale factor for tile to avoid a gigantic output mosaic.
            1.0 means unscaled. Values <1 are recommended.

    Returns:
        filesystem path to the mosaic created (dst_file)
    """
    # used to copy metadata
    ref_file = src_files[0]

    if len(src_files) <= mosaic_columns:
        tiles_w, tiles_h = (len(src_files), 1)
    else:
        tiles_w = mosaic_columns
        tiles_h = math.ceil(len(src_files) / mosaic_columns)

    command: list[str] = [str(OIIOTOOL)]
    for src_file in src_files:
        command += [
            "-i",
            str(src_file),
            "--resize",
            f"{tile_size[0] * 100}%x{tile_size[1] * 100}%",
            # bottom-left text with 30px margin
            "--text:x=30:y={TOP.height-30}:shadow=2",
            f"{src_file.stem}",
        ]
    # https://openimageio.readthedocs.io/en/latest/oiiotool.html#cmdoption-mosaic
    # XXX: needed so hack explained under works
    command += ["--metamerge"]

    command += [f"--mosaic:pad={mosaic_gap_size}", f"{tiles_w}x{tiles_h}"]
    # XXX: hack to preserve metadata that is lost with the mosaic operation
    command += ["-i", str(ref_file), "--chappend"]

    command += ["-o", str(dst_file)]

    LOGGER.info(f"about to call oiiotool with {command}")
    try:
        subprocess.check_call(command)
    except subprocess.CalledProcessError as error:
        LOGGER.error(f"stderr={error.stderr}\nstdout={error.stdout}")
        raise

    if not dst_file.exists():
        raise RuntimeError(
            f"Unexpected issue: combined file doesn't exist on disk at <{dst_file}>"
        )

    return dst_file


def main():
    src_files = FILES_GETTER_CALLABLE()
    start_time = time.time()

    LOGGER.info(f"started processing {len(src_files)} files")
    generate_image_mosaic(
        src_files=src_files,
        dst_file=OUTPUT_MOSAIC_PATH,
        mosaic_columns=MOSAIC_COLUMN_NUMBER,
        mosaic_gap_size=MOSAIC_GAP,
        tile_size=(TILE_RESIZE * ANAMORPHIC_DESQUEEZE, TILE_RESIZE),
    )
    LOGGER.info(f"finished in {time.time() - start_time:.2f}s")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="{levelname: <7} | {asctime} [{name}] {message}",
        style="{",
        stream=sys.stdout,
    )
    main()
