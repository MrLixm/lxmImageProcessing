import enum
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

LOGGER = logging.getLogger(__name__)


class ProResDataRate(enum.Enum):
    proxy422 = 0  # 45Mbs
    lt422 = 1  # 102Mbps
    s422 = 2  # 147Mbps
    hq422 = 3  # 220Mbps
    s4444 = 4  # 300Mbps


FFMPEG = Path(os.environ["FFMPEG"])
# list of filesystem paths to an existing .mov file or directory.
# directories are shallow parsed for .mov files.
INPUT_PATHS = [
    r"G:\personal\photo\workspace\dcim\2024\2024_04_13_salieres\P1000653.MOV",
]

QUALITY = ProResDataRate.s422


def convert_to_prores(
    ffmpeg_path: Path,
    input_path: Path,
    output_path: Path,
    prores_quality: ProResDataRate,
):
    # argument provided from https://academysoftwarefoundation.github.io/EncodingGuidelines/EncodeProres.html
    command = [
        str(ffmpeg_path),
        "-i",
        str(input_path),
        "-c:v",
        "prores_ks",
        "-profile:v",
        "3",
        "-vendor",
        "apl0",
        "-qscale:v",
        "10",
        "-color_range",
        str(prores_quality.value),
        "-colorspace",
        "bt709",
        "-color_primaries",
        "bt709",
        "-color_trc",
        "iec61966-2-1",
        str(output_path),
    ]
    subprocess.run(command)


def main():
    input_paths: list[Path] = []

    for path in INPUT_PATHS:
        path = Path(path)
        if path.is_dir():
            input_paths += list(path.glob("*.mov"))
        elif path.is_file():
            input_paths += [path]
        else:
            LOGGER.error(f"invalid path {path}")

    LOGGER.info(f"processing {len(input_paths)} files")

    stime = time.time()

    for index, input_path in enumerate(input_paths):
        output_path = input_path.with_suffix(f".prores-{QUALITY.name}.mov")

        LOGGER.info(f"[{index+1}/{len(input_paths)}] converting {input_path} ...")
        convert_to_prores(
            ffmpeg_path=FFMPEG,
            input_path=input_path,
            output_path=output_path,
            prores_quality=QUALITY,
        )

    LOGGER.info(f"finished in {time.time() - stime}s")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="{levelname: <7} | {asctime} [{name}:{funcName}] {message}",
        style="{",
        stream=sys.stdout,
    )
    main()
