import logging
import sys
from pathlib import Path

import lxmimgproc.tools.mosaic_generator

logging.basicConfig(
    level=logging.DEBUG,
    format="{levelname: <7} | {asctime} [{name}] {message}",
    style="{",
    stream=sys.stdout,
)

INPUT_DIR = Path(r"G:\personal\photo\workspace\dcim\2023\2023_12_27_tarentaise")
DST_PATH = Path(r"Z:\packages-dev\lxmImageProcessing\tmp") / "mosaic2.jpg"

# uncomment this to check all the options
# lxmimgproc.tools.mosaic_generator.execute(["--help"])

lxmimgproc.tools.mosaic_generator.execute(
    [
        str(DST_PATH),
        str(INPUT_DIR),
        "--image-extensions",
        "jpg",
        "--oiiotool",
        r"F:\softwares\apps\oiio\build\2.3.10\oiiotool.exe",
        # "--anamorphic-desqueeze",
        # "1.8",
    ]
)
