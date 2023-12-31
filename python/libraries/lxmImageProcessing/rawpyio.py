import contextlib
import copy
import logging
import time
from pathlib import Path
from multiprocessing import Pool
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


def rawpyget_metadata(
    src_file_path: Path,
    debayering_options: DebayeringOptionsType,
) -> dict[str, str]:
    """
    Get raw file "metadata" as a dictionary.

    Args:
        src_file_path: filesystem path to an existing raw file
        debayering_options: rawpy debayering options used to debayer the src file path

    Returns:
        a dict of metadata formatted in a custom way.
        keys use camelCase convention for naming
    """
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

    # more details :
    #   matrices are expressed as "sRGB > specified colorspace"
    # https://github.com/LibRaw/LibRaw/blob/21368133a94fbc35f594112a737d36f7ce65c7c0/src/tables/colorconst.cpp
    # https://github.com/LibRaw/LibRaw/blob/21368133a94fbc35f594112a737d36f7ce65c7c0/src/postprocessing/postprocessing_utils_dcrdefs.cpp#L30
    colorspace_mapping = {
        rawpy.ColorSpace.raw: "raw",
        rawpy.ColorSpace.ACES: "ACES2065-1 linear",
        rawpy.ColorSpace.Adobe: "AdobeRGB(1998) linear",
        rawpy.ColorSpace.P3D65: "DCI-P3 linear D65",
        rawpy.ColorSpace.ProPhoto: "ProPhoto linear D65",
        rawpy.ColorSpace.Rec2020: "BT.2020 linear",
        rawpy.ColorSpace.sRGB: "sRGB linear",
        rawpy.ColorSpace.Wide: "WideGamut linear D65",
        rawpy.ColorSpace.XYZ: "CIE-XYZ linear D65",
    }
    colorspace = debayering_options.output_color
    colorspace = rawpy.ColorSpace(colorspace)
    colorspace = colorspace_mapping.get(colorspace, "unknown")

    demosaic_id = debayering_options.user_qual
    try:
        demosaic = rawpy.DemosaicAlgorithm(demosaic_id)
        demosaic = demosaic.name
    except:
        demosaic = "default"

    return {
        "colorspace": colorspace,
        "gamma": str(debayering_options.gamm),
        "cameraMatrix": camera_matrix,
        "cameraToXYZ": rgb2XYZ_matrix,
        "whiteBalanceDaylight": whitebalance_d_coeffs,
        "whiteBalance": whitebalance_coeffs,
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


def rawpyget_recommended_debayering_options() -> DebayeringOptionsType:
    """
    Get options recommened o use for debayering in the loog workflow.
    """
    return rawpy.Params(
        output_bps=16,
        use_camera_wb=True,
        output_color=rawpy.ColorSpace.raw,
        no_auto_bright=True,
        gamma=(1.0, 1.0),
    )


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


def _process_exposure(raw_path: Path, options, exposure: float) -> numpy.ndarray:
    LOGGER.debug(
        f".../{raw_path.parent.parent.name}/{raw_path.parent.name}/{raw_path.name}: "
        f"about to process exposure {exposure}"
    )
    exposure_options = copy.copy(options)
    exposure_options.exp_shift = exposure
    exposure_array = rawpyread_image(
        raw_path,
        options=exposure_options,
        bitdepth="float32",
    )
    return exposure_array


def rawpyread_image_mergehdr(
    raw_path: Path,
    options: DebayeringOptionsType,
    # min value mentioned in the doc
    exposure_start=0.25,
    # must be lower than exposure_start + exposure_step * exposure_stack_n
    exposure_step=1.25,
    # arbitrary value
    exposure_stack_n=6,
) -> numpy.ndarray:
    """
    Convert a raw camera file to an R-G-B numpy array

    Try to expand the dynamic range by merging multiple brackets retrieved from
    scaling exposure before demosaicing.
    Brackets are calculated as [(exposure_start + exposure_step) * exposure_stack_n]

    Args:
        raw_path: path to an existing dng file
        options: demosaicing options
        exposure_start: minimal exposure value to start bracketing from. minimum is 0.25
        exposure_step: amount of exposure to add at each bracket
        exposure_stack_n: number of exposures to demosaic using the

     Returns:
         RGB image encoded in float32
    """

    exposures = [exposure_start + exposure_step * n for n in range(exposure_stack_n)]

    args_mapping = [(raw_path, options, exposure) for exposure in exposures]

    # threading provides a minimal performance boost.
    # it was initially for testing but was left for that small boost.
    with ThreadPoolExecutor() as pool:
        exposure_arrays = pool.map(
            lambda p: _process_exposure(*p),
            args_mapping,
            # not sure if this makes a noticeable difference
            chunksize=2,
        )

    exposure_arrays = list(exposure_arrays)

    combined_array: numpy.ndarray = exposure_arrays.pop(0)
    for array in exposure_arrays:
        combined_array += array

    return combined_array
