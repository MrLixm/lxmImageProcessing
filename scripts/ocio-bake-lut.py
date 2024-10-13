import logging
import sys
from pathlib import Path
from typing import Callable

import colour
import PyOpenColorIO as ocio
import numpy

LOGGER = logging.getLogger(__name__)


OCIO_CONFIG = Path(r"G:\temp\2499DRT\config.ocio")
INPUT_COLORSPACE = "V-Log V-Gamut"
OUTPUT_COLORSPACE = "2499DRT Base"
LUT_TARGET_PATH = Path(r"G:\temp\2499DRT\vlog-vgamut_2499DRT_sRGB.cube")
LUT_COMMENT = (
    "authored by liam collod\n"
    "using https://github.com/JuanPabloZambrano/DCTL/blob/e6fb981cc95af0544a3a24a659ccaad3fce73ed7/2499_DRT/JP-2499DRT%20OCIO/config.ocio"
)
# Lumix S5IIx documentation mentions "33 points" as maximum
RESOLUTION = 33


def create_lut(
    processor: Callable[[numpy.ndarray], numpy.ndarray],
    resolution: int,
    name: str,
    comment: str = "",
) -> colour.LUT3D:
    domain = numpy.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]], dtype=numpy.float32)
    domain_str = str(domain).replace("\n", "")
    lut = colour.LUT3D.linear_table(resolution, domain)
    lut = lut.astype(dtype=numpy.float32)
    lut = processor(lut)
    comment = comment + "\n" if comment else ""
    comments = (
        comment + f"LUT resolution = {resolution}\n" + f"LUT domain = {domain_str}"
    )
    return colour.LUT3D(
        table=lut,
        name=name,
        size=resolution,
        domain=domain,
        comments=comments.split("\n"),
    )


def main(
    ocio_config_path: Path,
    lut_dst_path: Path,
    input_colorspace: str,
    output_colorspace: str,
    lut_comment: str,
    lut_resolution: int,
):
    LOGGER.info(f"reading config '{ocio_config_path}'")
    config: ocio.Config = ocio.Config.CreateFromFile(str(ocio_config_path))
    config.validate()
    processor = config.getProcessor(input_colorspace, output_colorspace)
    cpu: ocio.CPUProcessor = processor.getDefaultCPUProcessor()

    def processor_call(image: numpy.ndarray) -> numpy.ndarray:
        buf = image.copy()
        cpu.applyRGB(buf)
        return buf

    LOGGER.info("creating lut")
    lut = create_lut(
        processor=processor_call,
        resolution=lut_resolution,
        name=lut_dst_path.stem,
        comment=lut_comment,
    )

    LOGGER.info(f"writing lut to '{lut_dst_path}'")
    colour.write_LUT(lut, str(lut_dst_path))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="{levelname: <7} | {asctime} [{name}] {message}",
        style="{",
        stream=sys.stdout,
    )
    main(
        ocio_config_path=OCIO_CONFIG,
        lut_dst_path=LUT_TARGET_PATH,
        input_colorspace=INPUT_COLORSPACE,
        output_colorspace=OUTPUT_COLORSPACE,
        lut_comment=LUT_COMMENT,
        lut_resolution=RESOLUTION,
    )
