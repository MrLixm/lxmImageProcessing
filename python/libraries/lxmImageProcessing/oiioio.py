import enum
import logging
from pathlib import Path

import numpy
import numpy.typing
import OpenImageIO as oiio

LOGGER = logging.getLogger(__name__)


class OiioTypes(enum.Enum):
    UINT8 = oiio.UINT8
    UINT16 = oiio.UINT16
    UINT32 = oiio.UINT32
    INT8 = oiio.INT8
    INT16 = oiio.INT16
    HALF = oiio.HALF
    FLOAT = oiio.FLOAT
    DOUBLE = oiio.DOUBLE


_DTYPE_MAPPING: dict[numpy.typing.DTypeLike, oiio.TypeDesc] = {
    numpy.dtype(numpy.uint8): oiio.UINT8,
    numpy.dtype(numpy.uint16): oiio.UINT16,
    numpy.dtype(numpy.uint32): oiio.UINT32,
    numpy.dtype(numpy.int8): oiio.INT8,
    numpy.dtype(numpy.int16): oiio.INT16,
    numpy.dtype(numpy.float16): oiio.HALF,
    numpy.dtype(numpy.float32): oiio.FLOAT,
    numpy.dtype(numpy.float64): oiio.DOUBLE,
}
"""
Map numpy dtype to OIIO TypeDesc
"""


def _convert_dtype_to_typedesc(numpy_dtype: numpy.typing.DTypeLike) -> oiio.TypeDesc:
    """
    Convert a numpy dtype to an OIIO type desc.
    """
    _numpy_dtype = numpy.dtype(numpy_dtype)
    return _DTYPE_MAPPING[_numpy_dtype]


def oiioconvert_array_to_image(array: numpy.ndarray) -> oiio.ImageBuf:
    """
    Convert a numpy array to an OIIO ImageBuf.
    """
    typedesc = _convert_dtype_to_typedesc(array.dtype)
    image_spec = oiio.ImageSpec(
        array.shape[1],
        array.shape[0],
        array.shape[2],
        typedesc,
    )
    image_buf = oiio.ImageBuf(image_spec)
    image_buf.set_pixels(oiio.ROI(), array)
    return image_buf


def oiiowrite_buf_to_disk(
    image_buf: oiio.ImageBuf,
    target_path: Path,
    target_type: OiioTypes,
):
    """
    Export the given array to a disk file in the image format implied by the extension
    of the target path.

    Args:
        image_buf: image buf to write to disk
        target_path: full path to the image file. might already exist.
        target_type: bitdepth of the exported file. Must be a valid bitdepth depending on the file format.
    """
    if image_buf.has_error:
        raise RuntimeError(f"Provided ImageBuf has errors: {image_buf.geterror()}")
    if not target_path.parent.exists():
        raise FileNotFoundError(
            f"Parent directory of target path doesn't exists on disk: {target_path}"
        )

    image_buf.write(str(target_path), target_type.value)
    return


def oiiowrite_array_to_disk(
    array: numpy.ndarray,
    target_path: Path,
    target_type: OiioTypes,
):
    """
    Export the given array to a disk file in the image format implied by the extension
    of the target path.

    Args:
        array: array that can be converted to an image
        target_path: full path to the image file. might already exist.
        target_type: bitdepth of the exported file. Must be a valid bitdepth depending on the file format.
    """
    image_buf = oiioconvert_array_to_image(array)
    image_buf.write(str(target_path), target_type.value)
    return
