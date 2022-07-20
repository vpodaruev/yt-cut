@echo off

set DIST=yt-cut

rem Python script to executable
pyinstaller --distpath %DIST% --onefile --windowed ytcut.py

rem copy icons
robocopy /E icons %DIST%/icons

rem copy tools
robocopy /E tools %DIST%/tools
