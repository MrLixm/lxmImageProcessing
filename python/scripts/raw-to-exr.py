import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

from lxmimgproc.rawpyio import rawpy
from lxmimgproc.rawpyio import DebayeringOptionsType
from lxmimgproc.rawpyio import rawpyread_image_mergehdr
from lxmimgproc.rawpyio import rawpyread_image
from lxmimgproc.rawpyio import rawpyget_metadata
from lxmimgproc.oiioio import oiioconvert_array_to_image
from lxmimgproc.oiioio import oiiowrite_buf_to_disk
from lxmimgproc.oiioio import OiioTypes
from lxmimgproc.exifio import exiftoolread_image_metadata

__VERSION__ = "1.0.0"
LOGGER = logging.getLogger(Path(__file__).stem)

# // PATHS
# a raw file path or a directory path
INPUT_PATH = Path(
    r"G:\personal\photo\workspace\dcim\2023\2023_12_24_tarentaise\dng\P1000279.dng"
)
# https://exiftool.org/
EXIFTOOL_PATH = os.getenv("EXIFTOOL") or Path(
    r"F:\softwares\apps\exiftool\build\12.70\exiftool.exe",
)
os.environ["EXIFTOOL"] = str(EXIFTOOL_PATH)
DEBUG_WRITE = True
INPUT_DIR_RECURSIVE = True
OVERWRITE_EXISTING = False

# // DEBAYERING options

# choose between "fastpreview", "normal", "hq", "uhq", "custom"
PRESET = "normal"

if PRESET == "fastpreview":
    HALF_SIZE = True
    DEMOSAIC_ALGORITHM = rawpy.DemosaicAlgorithm.AHD
    MEDIAN_PASSES: int = 0
    FBDD_NOISE_REDUCTION = rawpy.FBDDNoiseReductionMode.Off
    EXPOSURE_HDR_MERGE = False
    # to adjust depending on raw
    EXPOSURE_SHIFT: Optional[float] = +2.0
    EXR_BITDEPTH = OiioTypes.HALF
    EXR_COMPRESSION: str = "dwaa:45"
elif PRESET == "normal":
    HALF_SIZE = False
    DEMOSAIC_ALGORITHM = rawpy.DemosaicAlgorithm.AHD
    MEDIAN_PASSES: int = 0
    FBDD_NOISE_REDUCTION = rawpy.FBDDNoiseReductionMode.Light
    EXPOSURE_HDR_MERGE = True
    EXPOSURE_SHIFT: Optional[float] = None
    # // WRITING
    EXR_BITDEPTH = OiioTypes.HALF
    EXR_COMPRESSION: str = "dwaa:30"
elif PRESET.endswith("hq"):
    HALF_SIZE = False
    DEMOSAIC_ALGORITHM = rawpy.DemosaicAlgorithm.AHD
    MEDIAN_PASSES: int = 8
    FBDD_NOISE_REDUCTION = rawpy.FBDDNoiseReductionMode.Light
    EXPOSURE_HDR_MERGE = True
    EXPOSURE_SHIFT: Optional[float] = None
    EXR_BITDEPTH = OiioTypes.HALF
    EXR_COMPRESSION: str = "dwaa:15"
    if PRESET == "uhq":
        MEDIAN_PASSES = 10
        BDD_NOISE_REDUCTION = rawpy.FBDDNoiseReductionMode.Full
        EXR_COMPRESSION = "zips"
else:
    HALF_SIZE = False
    DEMOSAIC_ALGORITHM = rawpy.DemosaicAlgorithm.AHD
    # higher is slower but less rgb pixel artefacts
    MEDIAN_PASSES: int = 4
    FBDD_NOISE_REDUCTION = rawpy.FBDDNoiseReductionMode.Light
    EXPOSURE_HDR_MERGE = True
    # not used if EXPOSURE_HDR_MERGE==True
    EXPOSURE_SHIFT: Optional[float] = None
    # // WRITING
    EXR_BITDEPTH = OiioTypes.HALF
    EXR_COMPRESSION: str = "zips"


def retrieve_output_path(src_path: Path) -> Path:
    if DEBUG_WRITE:
        name = (
            f"{src_path.name}"
            f".{'hdr' if EXPOSURE_HDR_MERGE else EXPOSURE_SHIFT}"
            f".d-{DEMOSAIC_ALGORITHM.name}"
            f".m{MEDIAN_PASSES}"
            f".fbdd{FBDD_NOISE_REDUCTION.value}"
            f".exr-{EXR_COMPRESSION.replace(':', '-')}"
            f".{'half' if HALF_SIZE else 'full'}"
            f".exr"
        )
        parent = Path(__file__).parent.parent.parent / "tmp"
        if not parent.exists():
            parent.mkdir()

        return parent / name

    return src_path.with_suffix(".exr")


OUTPUT_PATH_CALLABLE = retrieve_output_path


def convert_raw_to_exr(
    src_file_path: Path,
    dst_file_path: Path,
    debayering_options: DebayeringOptionsType,
    hdr_merge: bool,
    exr_bitdepth: OiioTypes,
    exr_compression: Optional[str] = None,
):
    """

    Args:
        src_file_path: filesystem path to an existing raw file
        dst_file_path: filesystem path to an existing or writable file
        debayering_options: rawpy options
        exr_bitdepth: bitdepth to save the EXR in
        exr_compression:
            one of: "none", "rle", "zip", "zips", "piz", "pxr24", "b44", "b44a", "dwaa", or "dwab"
            For "dwaa" and "dwab", the dwaCompressionLevel may be optionally appended
            to the compression name after a colon, like this: "dwaa:200"
        hdr_merge:
            True to debayer multiple exposure from the raw file and merge them together
            to retrive a higher dynamic range image.
    """
    LOGGER.info(f"reading {src_file_path} ...")

    exif_metadata = exiftoolread_image_metadata(src_file_path)
    exif_metadata = exif_metadata["EXIF"]

    # retrieve metadata
    rawpy_metadata = rawpyget_metadata(src_file_path, debayering_options)

    LOGGER.debug("reading raw image ...")
    if hdr_merge:
        image_array = rawpyread_image_mergehdr(
            raw_path=src_file_path,
            options=debayering_options,
        )
    else:
        image_array = rawpyread_image(
            raw_path=src_file_path,
            options=debayering_options,
            bitdepth="float32",
        )

    imagebuf = oiioconvert_array_to_image(image_array)

    imagebuf.specmod().attribute("compression", exr_compression)

    # set arbitrary metadata
    imagebuf.specmod().attribute(f"raw-to-exr.py:version", __VERSION__)
    imagebuf.specmod().attribute(f"colorspace", rawpy_metadata["colorspace"])
    for metadata_name, metadata_value in rawpy_metadata.items():
        imagebuf.specmod().attribute(f"libraw:{metadata_name}", metadata_value)
    for metadata_name, metadata_value in exif_metadata.items():
        imagebuf.specmod().attribute(f"Exif:{metadata_name}", metadata_value)

    LOGGER.info(f"writting {dst_file_path} ...")
    oiiowrite_buf_to_disk(imagebuf, dst_file_path, exr_bitdepth)


def main():
    debayering_options = rawpy.Params(
        output_bps=16,
        use_camera_wb=True,
        output_color=rawpy.ColorSpace.XYZ,
        no_auto_bright=True,
        gamma=(1.0, 1.0),
        demosaic_algorithm=DEMOSAIC_ALGORITHM,
        median_filter_passes=MEDIAN_PASSES,
        fbdd_noise_reduction=FBDD_NOISE_REDUCTION,
        exp_shift=None if EXPOSURE_HDR_MERGE else EXPOSURE_SHIFT,
        half_size=HALF_SIZE,
    )

    LOGGER.info(f"started, processing input {INPUT_PATH}")
    start_time = time.time()

    if INPUT_PATH.is_file():
        input_files = [INPUT_PATH]
    else:
        globfunc = INPUT_PATH.rglob if INPUT_DIR_RECURSIVE else INPUT_PATH.glob
        input_files: list[Path] = list(globfunc("*.DNG"))

    files_number = len(input_files)

    for index, input_file in enumerate(input_files):
        LOGGER.info(f"{index + 1}/{files_number} processing {input_file}")

        dst_path = OUTPUT_PATH_CALLABLE(input_file)
        if dst_path.exists() and not OVERWRITE_EXISTING:
            LOGGER.warning(f"Already existing target file {dst_path}")
            continue

        convert_raw_to_exr(
            src_file_path=input_file,
            dst_file_path=dst_path,
            debayering_options=debayering_options,
            hdr_merge=EXPOSURE_HDR_MERGE,
            exr_bitdepth=EXR_BITDEPTH,
            exr_compression=EXR_COMPRESSION,
        )

    end_time = time.time()
    LOGGER.info(f"finished in {end_time - start_time:.2f}s")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="{levelname: <7} | {asctime} [{name}:{funcName}] {message}",
        style="{",
        stream=sys.stdout,
    )
    main()
