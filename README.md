# lxmImageProcessing

Personal resources for image-processing which include topics like :
* photography
* cinematography
* vfx

The package is not fully designed for public consumptions so use at your own risks.

# content


| tool                                                                             | description                                                 | type    | tag                                                  |
|----------------------------------------------------------------------------------|-------------------------------------------------------------|---------|------------------------------------------------------|
| [raw-to-dng.py](python/scripts/raw-to-dng.py)                                    | batch converting raw files to dng                           | script  | ![photo](https://img.shields.io/badge/photo-43896b)  |
| [raw-to-exr.py](python/scripts/raw-to-exr.py)                                    | batch converting raw files to OpenEXR, including debayering | script  | ![photo](https://img.shields.io/badge/photo-43896b)  |
| [rw2-to-dng.py](python/scripts/rw2-to-dng.py)                                    | batch converting panasonic raw file to dng (personal use)   | script  | ![photo](https://img.shields.io/badge/photo-43896b)  |
| [session-to-mosaic.py](python/scripts/session-to-mosaic.py)                      | combine multiple image to a single big mosaic of image      | script  | ![photo](https://img.shields.io/badge/photo-43896b)  |
| [ffmpeg-video-to-appleprores.bat](batch/scripts/ffmpeg-video-to-appleprores.bat) | encode to apple prores using ffmpeg                         | script  | ![video](https://img.shields.io/badge/video-4c78a6)  |
| [lxmImageProcessing](python/libraries/lxmImageProcessing)                        | python wrapper to interract with i-o libraries              | library | ![photo](https://img.shields.io/badge/photo-43896b)  |


# installation

Project is managed through [poetry](https://python-poetry.org/).

```shell
cd somewhere
git clone https://github.com/MrLixm/lxmImageProcessing
cd lxmImageProcessing
```

Next before installing dependencies you need to download some of them :

* OpenImageIO in [OpenImageIO](vendor/OpenImageIO) as python wheel, 
the initial wheel I was using are not available anymore so try to use instead:
  * https://github.com/ArchPlatform/oiio-python/releases 
  * https://github.com/cgohlke/win_arm64-wheels/releases/tag/v2023.9.30

Update the [pyproject.toml](pyproject.toml) file according to where you downloaded
those wheels.

then :

```shell
poetry shell
poetry install
```

some of the tools assume you have specific software available on your system :

| FFMPEG    | https://ffmpeg.org                                                                    |
|-----------|---------------------------------------------------------------------------------------|
| download  | https://ffmpeg.org/download.html                                                      |
| configure | expected to have the path to the executable set in the `FFMPEG` environment variable  |


| OIIOTOOL   | https://openimageio.readthedocs.io/en/latest/oiiotool.html                             |
|------------|----------------------------------------------------------------------------------------|
| download   | https://www.patreon.com/posts/openimageio-oiio-63609827                                |
| configure  | expected to have the path to the executable set in the `OIIOTOOL` environment variable |



| EXIFTOOL  | https://exiftool.org/                                                                  |
|-----------|----------------------------------------------------------------------------------------|
| download  | https://exiftool.org/                                                                  |
| configure | expected to have the path to the executable set in the `EXIFTOOL` environment variable |


| Adobe DNG converter | https://helpx.adobe.com/camera-raw/digital-negative.html                                   |
|---------------------|--------------------------------------------------------------------------------------------|
| download            | https://helpx.adobe.com/camera-raw/digital-negative.html#downloads                         |
| configure           | expected to have the path to the executable set in the `ADOBEDNGTOOL` environment variable |
