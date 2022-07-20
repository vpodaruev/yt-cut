@echo off

set DIST=yt-cut

rem Python script to executable
pyinstaller --distpath %DIST% --onefile --windowed ytcut.py

rem copy icons
robocopy /E icons %DIST%/icons

rem copy tools
copy /b yt-dlp.exe %DIST%
copy /b ffmpeg.exe %DIST%
