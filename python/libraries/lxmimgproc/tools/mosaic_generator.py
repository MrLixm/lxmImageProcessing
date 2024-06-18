import argparse
import logging
import math
import os
import subprocess
import sys
import time
from pathlib import Path

FILENAME = Path(__file__).stem
LOGGER = logging.getLogger(FILENAME)


def generate_image_mosaic(
    src_paths: list[Path],
    dst_path: Path,
    oiiotool_path: Path,
    mosaic_columns: int,
    mosaic_gap_size: int,
    tile_size: tuple[float, float],
) -> Path:
    """
    Use oiiotool to generate a mosaic of images with the given charcteristics.

    It is recommended all the sources image provided have the same dimensions.

    Mosaic is read from top-left to bottom right.

    Args:
        oiiotool_path: filesystem path to the oiiotool executable.
        src_paths: list of filesystem paths to existing image files readable by oiiotool
        dst_path: filesystem to a file that may or may not exist.
        mosaic_columns: maximum number of tile per row
        mosaic_gap_size: space between tiles in pixels
        tile_size:
            scale factor in percent for tile to avoid a gigantic output mosaic.
            100 means unscaled. Values <=100 are recommended.

    Returns:
        filesystem path to the mosaic created (dst_file)
    """
    # used to copy metadata
    ref_file = src_paths[0]

    if len(src_paths) <= mosaic_columns:
        tiles_w, tiles_h = (len(src_paths), 1)
    else:
        tiles_w = mosaic_columns
        tiles_h = math.ceil(len(src_paths) / mosaic_columns)

    command: list[str] = [str(oiiotool_path)]
    for src_file in src_paths:
        command += [
            "-i",
            str(src_file),
            "--resize",
            f"{tile_size[0]}%x{tile_size[1]}%",
            # bottom-left text with 30px margin
            "--text:x=30:y={TOP.height-30}:shadow=3",
            f"{src_file.stem}",
        ]
    # https://openimageio.readthedocs.io/en/latest/oiiotool.html#cmdoption-mosaic
    # XXX: needed so hack explained under works
    command += ["--metamerge"]

    command += [f"--mosaic:pad={mosaic_gap_size}", f"{tiles_w}x{tiles_h}"]
    # XXX: hack to preserve metadata that is lost with the mosaic operation
    command += ["-i", str(ref_file), "--chappend"]

    command += ["-o", str(dst_path)]

    LOGGER.debug(f"subprocess.check_call({command})")
    try:
        subprocess.check_call(command)
    except subprocess.CalledProcessError as error:
        LOGGER.error(f"stderr={error.stderr}\nstdout={error.stdout}")
        raise
    return dst_path


def get_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=FILENAME,
        description="generate a mosaic of photo took during a session. each photo is labeled with its name.",
    )
    parser.add_argument(
        "mosaic_path",
        type=str,
        help="filesystem path to write the final mosaic to.",
    )
    parser.add_argument(
        "input_path",
        type=Path,
        nargs="+",
        help=(
            "filesystem path to multiple file or directory.\n"
            "- recommended files are jpg/tif\n"
            "- directories are shallow parsed for any image type\n"
            "- mosaic is built from top-left to bottom right with the order of path specified respected.\n"
            "- if a directory include the mosaic_path it will be excluded.\n"
        ),
    )
    parser.add_argument(
        "--oiiotool",
        type=Path,
        default=Path(os.getenv("OIIOTOOL")),
        help=(
            "filesystem path to the oiiotool executable."
            'if not provided the value is retrieved from an "OIIOTOOL" environment variable.'
            "Note oiiotool version must be compiled with text rendering support."
        ),
    )
    parser.add_argument(
        "--image-extensions",
        type=str,
        default="jpg",
        help="comma-separated list of image extensions to use when parsing directories. ex: jpg,png,tif",
    )
    parser.add_argument(
        "--anamorphic-desqueeze",
        type=float,
        default=1.0,
        help="horizontal stretch factor for anamorphic optic desqueeze",
    )
    parser.add_argument(
        "--columns",
        type=int,
        default=6,
        help="number of columns for the mosaic.",
    )
    parser.add_argument(
        "--gap",
        type=int,
        default=15,
        help="space between mosaic tiles in pixels.",
    )
    parser.add_argument(
        "--resize",
        type=float,
        default=25.0,
        help=(
            "resize factor for each image tile, in percent."
            "lower value will avoid the final mosaic to have a gigantic dimensions."
            "value must be lower or equal to 100."
        ),
    )
    return parser


def execute(argv: list[str] = None) -> Path:
    """
    Args:
        argv: list of command line argument for the CLI

    Returns:
        filesystem path to the mosaic file on disk
    """
    cli = get_cli()
    argv = argv or sys.argv[1:]
    parsed = cli.parse_args(argv)

    input_paths: list[Path] = parsed.input_path
    image_extensions = parsed.image_extensions.split(",")
    src_paths = []

    for input_path in input_paths:
        if input_path.is_dir():
            for image_extention in image_extensions:
                children = input_path.glob(f"*.{image_extention}")
                src_paths.extend(children)
        else:
            src_paths.append(input_path)

    dst_path = Path(parsed.mosaic_path)

    if dst_path in src_paths:
        src_paths.remove(dst_path)

    oiiotool: Path = parsed.oiiotool
    anamorphic_desqueeze: float = parsed.anamorphic_desqueeze
    columns: int = parsed.columns
    gap: int = parsed.gap
    resize: float = parsed.resize
    tile_size = (resize * anamorphic_desqueeze, resize)

    start_time = time.time()
    LOGGER.info(f"processing {len(src_paths)} files to '{dst_path}'")
    generate_image_mosaic(
        src_paths=src_paths,
        dst_path=dst_path,
        oiiotool_path=oiiotool,
        mosaic_columns=columns,
        mosaic_gap_size=gap,
        tile_size=tile_size,
    )
    LOGGER.info(f"generation took {time.time() - start_time:.2f}s")

    if not dst_path.exists():
        raise RuntimeError(
            f"Unexpected issue: mosaic '{dst_path}' doesn't exist on disk."
        )
    return dst_path


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="{levelname: <7} | {asctime} [{name}] {message}",
        style="{",
        stream=sys.stdout,
    )
    execute()
