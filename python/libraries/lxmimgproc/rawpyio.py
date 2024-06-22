import contextlib
import copy
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Literal
from typing import Optional

import numpy
import rawpy._rawpy as rawpy
from colour.io import convert_bit_depth


LOGGER = logging.getLogger(__name__)

""" ____________________________________________________________________________________
UTILITY
"""

DebayeringOptionsType = rawpy.Params


@contextlib.contextmanager
def rawpyread(file_path: Path) -> rawpy.RawPy:
    """
    Context to read a raw file with rawpy that handle opening and closing.

    Args:
        file_path: path to an existing raw file supported by rawpy

    Returns:
        RawPy instance of the opened raw file.
    """
    processor = rawpy.RawPy()
    processor.open_file(str(file_path))
    try:
        yield processor
    finally:
        processor.close()


""" ____________________________________________________________________________________
METADATA
"""


def get_camera_matrix(raw_path: Path) -> numpy.ndarray:
    """
    Extract the camera matrix from the given raw file.

    TO VERIFY:
    matrices are expressed as "sRGB > specified colorspace"
    https://github.com/LibRaw/LibRaw/blob/21368133a94fbc35f594112a737d36f7ce65c7c0/src/tables/colorconst.cpp
    https://github.com/LibRaw/LibRaw/blob/21368133a94fbc35f594112a737d36f7ce65c7c0/src/postprocessing/postprocessing_utils_dcrdefs.cpp#L30

    Args:
        raw_path: existing path to the camera raw file to extract the matrix from

    Returns:
        3x3 color matrix as numpy ndarray
    """
    with rawpyread(raw_path) as raw_file:
        color_matrix = raw_file.color_matrix

    # convert 3x4 matrix to 3x3
    color_matrix = color_matrix[:, :3]
    return color_matrix


def get_rgb_to_XYZ_matrix(raw_path: Path) -> numpy.ndarray:
    """
    Extract the camera matrix from the given raw file.

    Args:
        raw_path: existing path to the camera raw file to extract the matrix from

    Returns:
        3x3 color matrix as numpy ndarray
    """
    with rawpyread(raw_path) as raw_file:
        color_matrix = raw_file.rgb_xyz_matrix

    # convert 3x4 matrix to 3x3
    color_matrix = color_matrix[:, :3]
    return color_matrix


def get_camera_whitebalance(
    raw_path: Path,
    daylight: bool = True,
) -> tuple[float, float, float]:
    """
    Return the whitebalance coefficient used for the image as R-G-B.
    """
    with rawpyread(raw_path) as raw_file:
        if daylight:
            whitebalance = raw_file.daylight_whitebalance
        else:
            whitebalance = raw_file.camera_whitebalance
    return tuple(whitebalance[:3])


def rawpymeta_file(
    src_file_path: Path,
) -> dict[str, str]:
    cm = get_camera_matrix(src_file_path)
    camera_matrix = f"{cm[0][0]}, {cm[1][0]}, {cm[2][0]}, "
    camera_matrix += f"{cm[1][0]}, {cm[1][1]}, {cm[1][2]}, "
    camera_matrix += f"{cm[2][0]}, {cm[2][1]}, {cm[2][2]}"

    cm = get_rgb_to_XYZ_matrix(src_file_path)
    rgb2XYZ_matrix = f"{cm[0][0]}, {cm[1][0]}, {cm[2][0]}, "
    rgb2XYZ_matrix += f"{cm[1][0]}, {cm[1][1]}, {cm[1][2]}, "
    rgb2XYZ_matrix += f"{cm[2][0]}, {cm[2][1]}, {cm[2][2]}"

    wc = get_camera_whitebalance(src_file_path, daylight=True)
    whitebalance_d_coeffs = f"{wc[0]}, {wc[1]}, {wc[2]}"

    wc = get_camera_whitebalance(src_file_path, daylight=False)
    whitebalance_coeffs = f"{wc[0]}, {wc[1]}, {wc[2]}"
    return {
        "cameraMatrix": camera_matrix,
        "cameraToXYZ": rgb2XYZ_matrix,
        "whiteBalanceDaylight": whitebalance_d_coeffs,
        "whiteBalance": whitebalance_coeffs,
    }


def rawpymeta_debayering(
    debayering_options: DebayeringOptionsType,
) -> dict[str, str]:
    """
    Convert the given debayering options a pontetial metadata specified as key/value pair.

    Args:
        src_file_path: filesystem path to an existing raw file
        debayering_options: rawpy debayering options used to debayer the src file path

    Returns:
        a dict of metadata formatted in a custom way.
        keys use camelCase convention for naming
    """
    colorspace = debayering_options.output_color
    colorspace = rawpy.ColorSpace(colorspace)
    colorspace = colorspace.name

    demosaic_id = debayering_options.user_qual
    try:
        demosaic = rawpy.DemosaicAlgorithm(demosaic_id)
        demosaic = demosaic.name
    except:
        demosaic = "default"

    return {
        "colorspace": colorspace,
        "gamma": str(debayering_options.gamm),
        "useCameraWhiteBalance": debayering_options.use_camera_wb,
        "demosaicAlgorithm": f"{demosaic_id} ({demosaic})",
        "medianPasses": debayering_options.med_passes,
        "fbddNoiseReduction": debayering_options.fbdd_noiserd,
        "noiseThreshold": debayering_options.threshold,
        "fourColorRGB": debayering_options.four_color_rgb,
        "exposureShift": debayering_options.exp_shift,
        "exposureCorrection": debayering_options.exp_correc,
        "exposurePreservation": debayering_options.exp_preser,
        "highlightMode": debayering_options.highlight,
    }


""" ____________________________________________________________________________________
DEBAYERING
"""


def rawpyread_image(
    raw_path: Path,
    options: DebayeringOptionsType,
    bitdepth: Optional[
        Literal["uint8", "uint16", "float16", "float32", "float64", "float128"]
    ] = None,
) -> numpy.ndarray:
    """
    Convert a raw camera file to an R-G-B numpy array

    Args:
        raw_path: path to an existing dng file
        options: demosaicing options
        bitdepth: optional conversion to the given bitdepth

    Returns:
        RGB image usually encoded in uint16 or uint8
    """
    with rawpyread(raw_path) as raw_file:
        rgb: numpy.ndarray = raw_file.postprocess(params=options)

    if bitdepth:
        rgb = convert_bit_depth(rgb, bitdepth)

    return rgb
