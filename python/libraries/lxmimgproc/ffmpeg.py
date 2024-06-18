import enum
import logging

LOGGER = logging.getLogger(__name__)


class FfmpegCctf(enum.Enum):
    """
    To use with ``--color_trc``

    References:
        - [1] https://github.com/FFmpeg/FFmpeg/blob/90579fbb907fbfda18b7cdac44c08aaf09c6ca09/libavutil/pixdesc.c#L2819
        - [2] https://github.com/FFmpeg/FFmpeg/blob/90579fbb907fbfda18b7cdac44c08aaf09c6ca09/libavutil/pixfmt.h#L580
    """

    unknown = "unknown"
    BT_709 = "bt709"  # gamma 2.4
    BT_470m = "bt470m"  # gamma 2.2
    BT_470bg = "bt470bg"  # gamma 2.8
    SMPTE_170m = "smpte170m"  # also ITU-R BT601-6 525 or 625 / ITU-R BT1358 525 or 625 / ITU-R BT1700 NTSC
    SMPTE_240m = "smpte240m"
    linear = "linear"  # Linear transfer characteristics
    log100 = "log100"  # Logarithmic transfer characteristic (100:1 range)
    log316 = "log316"  # Logarithmic transfer characteristic (100 * Sqrt(10) : 1 range)
    BT_1361e = "bt1361e"  # ITU-R BT1361 Extended Colour Gamut (1998)
    IEC_61966_2_4 = "iec61966-2-4"  # IEC 61966-2-4
    IEC_61966_2_1 = "iec61966-2-1"  # IEC 61966-2-1 (sRGB or sYCC)
    BT_2020_10bit = "bt2020-10"  # ITU-R BT2020 for 10-bit system
    BT_2020_12bit = "bt2020-12"  # ITU-R BT2020 for 12-bit system
    SMPTE_2084 = "smpte2084"  # SMPTE ST 2084 for 10-, 12-, 14- and 16-bit systems
    SMPTE_428 = "smpte428"  # SMPTE ST 428-1
    arib_std_b67 = "arib-std-b67"  # ARIB STD-B67, known as "Hybrid log-gamma"


class FfmpegColorPrimaries(enum.Enum):
    """
    To use with ``--color_primariese``

    References:
        - [1] https://github.com/FFmpeg/FFmpeg/blob/90579fbb907fbfda18b7cdac44c08aaf09c6ca09/libavutil/pixdesc.c#L2819
        - [2] https://github.com/FFmpeg/FFmpeg/blob/90579fbb907fbfda18b7cdac44c08aaf09c6ca09/libavutil/pixfmt.h#L580
    """

    unknown = "unknown"
    BT_709 = "bt709"
    BT_470m = "bt470m"  # also FCC Title 47 Code of Federal Regulations 73.682 (a)(20)
    BT_470bg = "bt470bg"  # also ITU-R BT601-6 625 / ITU-R BT1358 625 / ITU-R BT1700 625 PAL & SECAM
    BT_2020 = "bt2020"
    CIE_XYZ = "smpte428"
    DCI_P3 = "smpte431"
    P3_D65 = "smpte432"  # also Display P3
    SMPTE_170m = "smpte170m"  # colorspace used by NTSC and PAL and by SDTV in general
    SMPTE_240m = "smpte240m"  # interim standard used during the early days of HDTV
    film = "film"  # colour filters using Illuminant C
    ebu3213 = "ebu3213"


class FfmpegColorspace(enum.Enum):
    """
    To use with ``--color_space``

    References:
        - [1] https://github.com/FFmpeg/FFmpeg/blob/90579fbb907fbfda18b7cdac44c08aaf09c6ca09/libavutil/pixdesc.c#L2841
        - [2] https://github.com/FFmpeg/FFmpeg/blob/90579fbb907fbfda18b7cdac44c08aaf09c6ca09/libavutil/pixfmt.h#L609
    """

    unknown = "unknown"
    gbr = "gbr"  # GBR, also IEC 61966-2-1 (sRGB), YZX and ST 428-1
    BT_709 = "bt709"
    BT_470bg = "bt470bg"
    BT_2020_nonconst = "bt2020nc"
    BT_2020_const = "bt2020c"
    fcc = "fcc"
    SMPTE_170m = "smpte170m"
    SMPTE_240m = "smpte240m"
    SMPTE_2085 = "smpte2085"
    chroma_derived_nonconst = "chroma-derived-nc"
    chroma_derived_const = "chroma-derived-c"
    ICtCp = "ictcp"  # ITU-R BT.2100-0, ICtCp
    IPT_C2 = "ipt-c2"  # SMPTE ST 2128
    YCgCo = "ycgco"  # used by Dirac / VC-2 and H.264 FRext, see ITU-T SG16
    YCgCo_even = "ycgco-re"
    YCgCo_odd = "ycgco-ro"


class FfmpegColorRange(enum.Enum):
    """
    To use with ``--color_range``

    References:
        - [2] https://github.com/FFmpeg/FFmpeg/blob/90579fbb907fbfda18b7cdac44c08aaf09c6ca09/libavutil/pixdesc.c#L2796
        - [1] https://github.com/FFmpeg/FFmpeg/blob/90579fbb907fbfda18b7cdac44c08aaf09c6ca09/libavutil/pixfmt.h#L651
    """

    unknown = "unknown"
    tv = "tv"  # also referred as MPEG, ex. the range of 16-235 for 8 bits
    full = "pc"  # also referred as JPEG, ex. the range of 0-255 for 8 bits


def get_ffmpeg_sRGB_encoding_args() -> list[str]:
    """
    Get the ffmpeg args to tag a media as sRGB encoded.

    References:
        - [1] https://academysoftwarefoundation.github.io/EncodingGuidelines/WebColorPreservation.html
    """
    return [
        "-colorspace",
        FfmpegColorspace.BT_709.value,
        "-color_primaries",
        FfmpegColorPrimaries.BT_709.value,
        "-color_trc",
        FfmpegCctf.IEC_61966_2_1.value,
    ]


def get_ffmpeg_BT709_encoding_args() -> list[str]:
    """
    Get the ffmpeg args to tag a media as BT.709 encoded.

    References:
        - [1] https://academysoftwarefoundation.github.io/EncodingGuidelines/WebColorPreservation.html
    """
    return [
        "-colorspace",
        FfmpegColorspace.BT_709.value,
        "-color_primaries",
        FfmpegColorPrimaries.BT_709.value,
        "-color_trc",
        FfmpegCctf.BT_709.value,
    ]


class FFmpegProResDataRate(enum.Enum):
    """
    proxy422 = 45Mbs,
    lt422 = 102Mbps,
    s422 = 147Mbps,
    hq422 = 220Mbps,
    s4444 = 300Mbps,
    """

    proxy422 = 0
    lt422 = 1
    s422 = 2
    hq422 = 3
    s4444 = 4
