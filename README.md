# lxmImageProcessing

Personal resources for image-processing which include topics like :
* photography
* cinematography
* vfx

The package is not fully designed for public consumptions so use at your own risks.

# content

todo

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
