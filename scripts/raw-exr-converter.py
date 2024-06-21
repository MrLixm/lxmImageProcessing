import logging
import sys
from pathlib import Path

import lxmimgproc.tools.raw_exr_converter
from lxmimgproc.browse import get_dir_content

logging.basicConfig(
    level=logging.DEBUG,
    format="{levelname: <7} | {asctime} [{name}] {message}",
    style="{",
    stream=sys.stdout,
)

INPUT_PATHS = get_dir_content(
    Path(r"G:\personal\photo\workspace\dcim\2024\2024_06_20_mshootsweat"),
    file_extensions=[".dng"],
)
print(f"processing {len(INPUT_PATHS)} files")

for index, INPUT_PATH in enumerate(INPUT_PATHS):
    print(f"{index+1}/{len(INPUT_PATHS)} ...")
    DST_PATH = INPUT_PATH.with_stem("{input_filestem}.{preset}.{colorspace}")
    DST_PATH = DST_PATH.with_suffix(".exr")
    lxmimgproc.tools.raw_exr_converter.execute(
        [
            str(DST_PATH),
            str(INPUT_PATH),
            "--colorspace",
            "@native",
            "--preset",
            "normal",
            "--overwrite-existing",
            "--exiftool",
            r"F:\softwares\apps\exiftool\build\12.70\exiftool.exe",
        ]
    )
