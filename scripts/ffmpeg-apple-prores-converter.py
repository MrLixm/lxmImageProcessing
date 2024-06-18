import logging
import sys
from pathlib import Path

import lxmimgproc.tools.ffmpeg_appleprores_converter
from lxmimgproc.ffmpeg import FFmpegProResDataRate

logging.basicConfig(
    level=logging.DEBUG,
    format="{levelname: <7} | {asctime} [{name}] {message}",
    style="{",
    stream=sys.stdout,
)

INPUT_PATH = Path(
    r"G:\personal\photo\workspace\dcim\2024\2024_04_13_salieres\P1000653.MOV"
)
DST_PATH = INPUT_PATH.with_stem(INPUT_PATH.stem + ".{datarate}.q{quality}")
DST_PATH = DST_PATH.with_suffix(".mov")

# uncomment this to check all the options
# lxmimgproc.tools.ffmpeg_appleprores_converter.execute(["--help"])

result = lxmimgproc.tools.ffmpeg_appleprores_converter.execute(
    [
        str(DST_PATH),
        str(INPUT_PATH),
        "--datarate",
        FFmpegProResDataRate.s422.name,
        "--quality",
        "10",
    ]
)
print(f"result at '{result}'")
