import argparse
import dataclasses
import logging
import os
import sys
import time
from pathlib import Path

import cocoon

from lxmimgproc.rawpyio import rawpy
from lxmimgproc.rawpyio import DebayeringOptionsType
from lxmimgproc.rawpyio import rawpyread_image
from lxmimgproc.rawpyio import rawpymeta_debayering
from lxmimgproc.oiioio import oiioconvert_array_to_image
from lxmimgproc.oiioio import oiiowrite_buf_to_disk
from lxmimgproc.oiioio import OiioTypes
from lxmimgproc.oiioio import OiioExrCompression
from lxmimgproc.exifio import exiftoolread_image_metadata
from lxmimgproc.oiioio import oiio

__VERSION__ = "2.0.0"
FILENAME = Path(__file__).stem
LOGGER = logging.getLogger(FILENAME)


@dataclasses.dataclass
class ConversionPreset:
    half_size: bool
    demosaic_algorithm: rawpy.DemosaicAlgorithm
    median_passes: int
    fbdd_noise_reduction: rawpy.FBDDNoiseReductionMode
    exr_bitdepth: OiioTypes
    exr_compression: OiioExrCompression | None
    exr_compression_amount: float | None = None


PRESETS = {
    "fastpreview": ConversionPreset(
        half_size=False,
        demosaic_algorithm=rawpy.DemosaicAlgorithm.DHT,
        median_passes=0,
        fbdd_noise_reduction=rawpy.FBDDNoiseReductionMode.Off,
        exr_bitdepth=OiioTypes.HALF,
        exr_compression=OiioExrCompression.dwaa,
        exr_compression_amount=45,
    ),
    "normal": ConversionPreset(
        half_size=False,
        demosaic_algorithm=rawpy.DemosaicAlgorithm.DHT,
        median_passes=0,
        fbdd_noise_reduction=rawpy.FBDDNoiseReductionMode.Off,
        exr_bitdepth=OiioTypes.HALF,
        exr_compression=OiioExrCompression.dwaa,
        exr_compression_amount=30,
    ),
    "hq": ConversionPreset(
        half_size=False,
        demosaic_algorithm=rawpy.DemosaicAlgorithm.DHT,
        median_passes=2,
        fbdd_noise_reduction=rawpy.FBDDNoiseReductionMode.Light,
        exr_bitdepth=OiioTypes.HALF,
        exr_compression=OiioExrCompression.dwaa,
        exr_compression_amount=15,
    ),
    "ultrahq": ConversionPreset(
        half_size=False,
        demosaic_algorithm=rawpy.DemosaicAlgorithm.DHT,
        median_passes=8,
        fbdd_noise_reduction=rawpy.FBDDNoiseReductionMode.Full,
        exr_bitdepth=OiioTypes.HALF,
        exr_compression=OiioExrCompression.zips,
    ),
    "scan": ConversionPreset(
        half_size=False,
        demosaic_algorithm=rawpy.DemosaicAlgorithm.DHT,
        median_passes=2,
        fbdd_noise_reduction=rawpy.FBDDNoiseReductionMode.Off,
        exr_bitdepth=OiioTypes.HALF,
        exr_compression=OiioExrCompression.dwaa,
        exr_compression_amount=15,
    ),
}


def convert_raw_to_exr(
    src_file_path: Path,
    dst_file_path: Path,
    exiftool_path: Path,
    debayering_options: DebayeringOptionsType,
    colorspace: cocoon.RgbColorspace | None,
    exr_bitdepth: OiioTypes,
    exr_compression: OiioExrCompression | None = None,
    exr_compression_amount: float | None = None,
    exposure_shift: float = 0.0,
):
    """

    Args:
        src_file_path: filesystem path to an existing raw file
        dst_file_path: filesystem path to an existing or writable file
        exiftool_path:
        colorspace: target colorspace with linear transfer-function
        debayering_options: rawpy options
        exr_bitdepth: bitdepth to save the EXR in
        exr_compression:
        exr_compression_amount: only for "dwaa" and "dwab" compression.
        exposure_shift: exposure shift in stops where 0.0 = no change.
    """
    # retrieve metadata
    exif_metadata = exiftoolread_image_metadata(
        image_path=src_file_path,
        exiftool_path=exiftool_path,
    )
    exif_metadata = exif_metadata["EXIF"]
    rawpy_metadata = rawpymeta_debayering(debayering_options)

    LOGGER.debug(f"rawpyread_image('{src_file_path}')")
    image_array = rawpyread_image(
        raw_path=src_file_path,
        options=debayering_options,
        bitdepth="float32",
    )

    chromaticities = None
    if colorspace is not None:
        chromaticities = cocoon.colorspace_to_exr_chromaticities(colorspace)
        # XXX: we force conversion to XYZ in the debayering_options
        LOGGER.debug(f"cocoon.XYZ_to_colorspace(..., {colorspace.name}, ...)")
        image_array = cocoon.XYZ_to_colorspace(
            image_array,
            colorspace,
            whitepoint_XYZ=colorspace.whitepoint,
            chromatic_adaptation_transform=cocoon.ChromaticAdaptationTransform.CAT02,
        )

    # convert in stops
    exposure_shift_ = 2.0**exposure_shift
    LOGGER.debug(f"image_array * {exposure_shift_}")
    image_array = image_array * exposure_shift_

    imagebuf = oiioconvert_array_to_image(image_array)

    exr_compression = exr_compression or OiioExrCompression.none
    exr_compression = exr_compression.get_oiio_value(exr_compression_amount)
    imagebuf.specmod().attribute("compression", exr_compression)

    # set arbitrary metadata
    imagebuf.specmod().attribute(f"raw-to-exr.py:version", __VERSION__)
    imagebuf.specmod().attribute(
        f"colorspace", colorspace.name if colorspace else ".native"
    )
    if chromaticities:
        imagebuf.specmod().attribute(
            "chromaticities", oiio.TypeDesc.TypeVector, chromaticities
        )

    for metadata_name, metadata_value in rawpy_metadata.items():
        imagebuf.specmod().attribute(f"libraw:{metadata_name}", metadata_value)
    for metadata_name, metadata_value in exif_metadata.items():
        imagebuf.specmod().attribute(f"Exif:{metadata_name}", metadata_value)

    LOGGER.debug(f"oiiowrite_buf_to_disk('{dst_file_path}')")
    oiiowrite_buf_to_disk(imagebuf, dst_file_path, exr_bitdepth)


_COLORSPACE_NATIVE = "@native"


def get_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=FILENAME,
        description="debayer a camera raw format to OpenEXR.",
    )
    parser.add_argument(
        "output_path",
        type=str,
        help=(
            "filesystem path to write the final exr to. \n"
            "THe path MUST have the .exr suffix. \n"
            "The path can include the following tokens: \n"
            "{input_filestem},{colorspace},{preset},{hdr},{whitebalance} \n"
            "which value are retrieved from the arguments provided."
        ),
    )
    parser.add_argument(
        "input_path",
        type=Path,
        help="filesystem path to a supported camera raw format (but recommended to be .DNG)",
    )
    parser.add_argument(
        "--exiftool",
        type=Path,
        help=(
            "filesystem path to the exiftool executable (https://exiftool.org/)."
            'if not provided the value is retrieved from an "EXIFTOOL" environment variable.'
            "Exiftool is used to copy camera metadata to the exr."
        ),
    )
    parser.add_argument(
        "--overwrite-existing",
        action="store_true",
        help="True to overwrite existing exr on disk if any. False will stop the script before any file is written.",
    )
    parser.add_argument(
        "--colorspace",
        choices=[_COLORSPACE_NATIVE] + cocoon.get_available_colorspaces_names(),
        default=cocoon.sRGB_LINEAR_COLORSPACE,
        help=(
            f"Which primaries + whitepoint to use for encoding the EXR. "
            f'The raw file is always debayered to an intermediate CIE XYZ encoding unless "{_COLORSPACE_NATIVE}" is specified.'
        ),
    )
    parser.add_argument(
        "--whitebalance",
        type=str,
        default=None,
        help=(
            "Whitebalance to use for debayering: \n"
            "- the daylight locus temperature in Kelvin, ending with a K. ex: 5600K \n"
            '- the term "auto" to let libraw guess it \n'
            "- not specifying it will use the default camera whitebalance \n"
        ),
    )
    parser.add_argument(
        "--preset",
        choices=list(PRESETS.keys()),
        default=PRESETS["normal"],
        help="Preset name that will determine the debayering options to use, mainly affecting quality.",
    )
    parser.add_argument(
        "--exposure-shift",
        type=float,
        default=2.6,
        help="Amount in stops to shift the OpenEXR by. 0.0 means no shift.",
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

    default_exiftool = os.getenv("EXIFTOOL")

    input_path: Path = parsed.input_path
    output_path: Path = parsed.output_path
    exiftool: Path = parsed.exiftool or (
        Path(default_exiftool) if default_exiftool else None
    )
    overwrite_existing: bool = parsed.overwrite_existing
    colorspace: str = parsed.colorspace
    whitebalance: str = parsed.whitebalance
    preset: str = parsed.preset
    exposure_shift: float = parsed.exposure_shift

    if colorspace == _COLORSPACE_NATIVE:
        output_color = rawpy.ColorSpace.raw
        colorspace: None = None
        colorspace_name = _COLORSPACE_NATIVE
    else:
        output_color = rawpy.ColorSpace.XYZ
        colorspace: cocoon.RgbColorspace = cocoon.get_colorspace(
            name=colorspace,
            force_linear=True,
        )
        colorspace_name = colorspace.name_simplified

    LOGGER.debug(f"colorspace={colorspace_name}")

    src_file_path = input_path
    dst_file_path = str(output_path).replace("{input_filestem}", input_path.stem)
    dst_file_path = dst_file_path.replace("{colorspace}", colorspace_name)
    dst_file_path = dst_file_path.replace("{preset}", preset)

    dst_file_path = dst_file_path.replace(
        "{whitebalance}", whitebalance if whitebalance else "camera"
    )
    dst_file_path = Path(dst_file_path)

    if dst_file_path.exists() and not overwrite_existing:
        raise FileExistsError(
            f"Destination file '{dst_file_path}' already exists and overwrite disabled."
        )

    preset: ConversionPreset = PRESETS[preset]

    if not whitebalance:
        whitebalance_kwargs = {"use_camera_wb": True}
    elif whitebalance == "auto":
        whitebalance_kwargs = {"use_camera_wb": False, "use_auto_wb": True}
    else:
        user_wb = []  # TODO
        whitebalance_kwargs = {
            "use_camera_wb": False,
            "use_auto_wb": False,
            "user_wb": user_wb,
        }
        raise NotImplementedError("Custom whitebalance not implemented")

    rawpy_kwargs = whitebalance_kwargs

    debayering_options = rawpy.Params(
        output_bps=16,
        output_color=output_color,
        no_auto_bright=True,
        gamma=(1.0, 1.0),
        demosaic_algorithm=preset.demosaic_algorithm,
        median_filter_passes=preset.median_passes,
        fbdd_noise_reduction=preset.fbdd_noise_reduction,
        half_size=preset.half_size,
        **rawpy_kwargs,
    )
    LOGGER.debug(f"{debayering_options}")

    start_time = time.time()
    LOGGER.info(f"processing '{input_path}' to '{dst_file_path}'")
    convert_raw_to_exr(
        src_file_path=src_file_path,
        dst_file_path=dst_file_path,
        exiftool_path=exiftool,
        debayering_options=debayering_options,
        colorspace=colorspace,
        exr_bitdepth=preset.exr_bitdepth,
        exr_compression=preset.exr_compression,
        exr_compression_amount=preset.exr_compression_amount,
        exposure_shift=exposure_shift,
    )
    LOGGER.info(f"generation took {time.time() - start_time:.2f}s")

    if not dst_file_path.exists():
        raise RuntimeError(
            f"Unexpected issue: output '{dst_file_path}' doesn't exist on disk."
        )
    return dst_file_path


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="{levelname: <7} | {asctime} [{name}] {message}",
        style="{",
        stream=sys.stdout,
    )
    execute()
