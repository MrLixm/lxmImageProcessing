:: intended to be readable in Foundry's Nuke
set "SOURCE_PATH=G:\personal\photo\workspace\dcim\2023\2023_12_27_tarentaise\P1000344.MOV"
set "TARGET_PATH=G:\personal\photo\workspace\dcim\2023\2023_12_27_tarentaise\P1000344.prores-full.MOV"
:: argument provided from https://academysoftwarefoundation.github.io/EncodingGuidelines/EncodeProres.html
:: -color_range: 2=standard-4:2:2, 3=hq-4:2:2, 4=4:4:4:4
%FFMPEG% -i %SOURCE_PATH% -c:v prores_ks -profile:v 3 -vendor apl0 -qscale:v 10 -color_range 2 -colorspace bt709 -color_primaries bt709 -color_trc iec61966-2-1 %TARGET_PATH%