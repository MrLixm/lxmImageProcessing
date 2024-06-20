import argparse
import logging
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

from lxmimgproc.ffmpeg import FFmpegProResDataRate

FILENAME = Path(__file__).stem
LOGGER = logging.getLogger(FILENAME)


def convert_to_prores(
    ffmpeg_path: Path,
    input_path: Path,
    output_path: Path,
    prores_data_rate: FFmpegProResDataRate,
    prores_quality: int,
    *args,
):
    # recommendations from https://academysoftwarefoundation.github.io/EncodingGuidelines/EncodeProres.html
    encoder = "prores_videotoolbox"
    if platform.system() != "Darwin":
        encoder = "prores_ks"
        LOGGER.warning("prores output bitdepth limited to 10 bits on this platform !")
    command = [
        str(ffmpeg_path),
        "-i",
        str(input_path),
        "-c:v",
        encoder,
        "-profile:v",
        str(prores_data_rate.value),
        "-vendor",
        "apl0",
        "-qscale:v",
        f"{prores_quality}",
    ]
    command += args
    command += [
        str(output_path),
    ]
    LOGGER.debug(f"subprocess.run({command})")
    subprocess.run(command, check=True)


def get_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=FILENAME,
        description=(
            "Convert any ffmpeg supported format to Apple ProRes."
            "The output is tagged as sRGB for viewing (no data change)."
        ),
    )
    parser.add_argument(
        "output_path",
        type=str,
        help=(
            "filesystem path to write the final prores video to."
            "the path can include the following tokens: \n"
            "{input_filestem},{datarate},{quality} \n"
            "which value are retrieved from the arguments provided."
        ),
    )
    parser.add_argument(
        "input_path",
        type=Path,
        help="filesystem path to a file in an ffmpeg supported format",
    )
    parser.add_argument(
        "--ffmpeg",
        type=Path,
        default=Path(os.getenv("FFMPEG")),
        help=(
            "filesystem path to the ffmpeg executable."
            'if not provided the value is retrieved from an "FFMPEG" environment variable.'
            "Note ffmpeg version must be compiled with prores codecs."
        ),
    )
    parser.add_argument(
        "--datarate",
        type=str,
        choices=[v.name for v in FFmpegProResDataRate],
        default=FFmpegProResDataRate.s422.name,
        help='"Flavor" of prores influencing the quality of the data stored: '
        + FFmpegProResDataRate.__doc__,
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=10,
        help="general quality of the prores: values between 9 - 13 give a good result, 0 being best.",
    )
    parser.add_argument(
        "--extra",
        help="extra arguments passed to ffmpeg",
        nargs="*",
        default=[],
    )
    return parser


def execute(argv: list[str] = None) -> Path:
    """
    Args:
        argv: list of command line argument for the CLI

    Returns:
        filesystem path to the prores file on disk
    """
    cli = get_cli()
    argv = argv or sys.argv[1:]
    parsed = cli.parse_args(argv)

    input_path: Path = parsed.input_path
    output_path: str = str(parsed.output_path)

    ffmpeg: Path = parsed.ffmpeg
    datarate: str = parsed.datarate
    datarate: FFmpegProResDataRate = getattr(FFmpegProResDataRate, datarate)
    quality: int = parsed.quality
    extra_args = parsed.extra
    # replace tokens
    dst_path: str = output_path.replace("{input_filestem}", input_path.stem)
    dst_path: str = dst_path.replace("{datarate}", datarate.name)
    dst_path: str = dst_path.replace("{quality}", str(quality))
    dst_path: Path = Path(dst_path)

    start_time = time.time()
    LOGGER.info(f"converting '{input_path}' to '{output_path}'")
    convert_to_prores(
        ffmpeg_path=ffmpeg,
        input_path=input_path,
        output_path=dst_path,
        prores_data_rate=datarate,
        prores_quality=quality,
        *extra_args,
    )
    LOGGER.info(f"conversion took {time.time() - start_time:.2f}s")

    if not dst_path.exists():
        raise RuntimeError(
            f"Unexpected issue: mosaic '{dst_path}' doesn't exist on disk."
        )
    return dst_path


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="{levelname: <7} | {asctime} [{name}:{funcName}] {message}",
        style="{",
        stream=sys.stdout,
    )
    execute()
