@echo off

set DIST=yt-cut

rem Python script to executable
pyinstaller --distpath %DIST% --onefile --windowed ytcut.py

rem copy icons
copy /b cs-logo.jpg %DIST%
copy /b go-next.png %DIST%
copy /b go-prev.png %DIST%
copy /b saveAs.png %DIST%
copy /b download.png %DIST%
copy /b cancel.png %DIST%

rem copy tools
copy /b youtube-dl.exe %DIST%
copy /b ffmpeg.exe %DIST%
