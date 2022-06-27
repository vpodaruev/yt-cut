@echo off

set DIST=dist

pyinstaller --onefile --windowed download_youtube.py
copy /b ffmpeg.exe %DIST%
copy /b youtube-dl.exe %DIST%
copy /b cs-logo.jpg %DIST%
copy /b download.png %DIST%
copy /b go-next.png %DIST%
copy /b go-prev.png %DIST%
copy /b saveAs.png %DIST%
