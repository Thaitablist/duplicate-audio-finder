@echo off
REM =====================================================================
REM  Build the Windows app (.exe folder) and installer (.exe setup).
REM  Run this ON A WINDOWS MACHINE - PyInstaller cannot cross-compile.
REM
REM  Prerequisites (once):
REM    - Python 3.11+ installed and on PATH
REM    - Inno Setup 6 installed (ISCC.exe): https://jrsoftware.org/isdl.php
REM
REM  Usage: from the project root, run:  build\build_windows.bat
REM =====================================================================
setlocal
cd /d "%~dp0.."

echo [1/5] Creating virtual environment...
python -m venv .venv || goto :error

echo [2/5] Installing dependencies...
call .venv\Scripts\python -m pip install --upgrade pip || goto :error
call .venv\Scripts\python -m pip install -e ".[dev]" || goto :error

echo [3/5] Generating icons (.ico)...
call .venv\Scripts\python build\make_icons.py || goto :error

echo [4/5] Building the app with PyInstaller...
call .venv\Scripts\pyinstaller build\dupaudio.spec --distpath dist --workpath build\_work --noconfirm || goto :error

echo [5/5] Building the installer with Inno Setup...
where ISCC >nul 2>nul
if %errorlevel%==0 (
    ISCC build\installer.iss || goto :error
    echo Done. Installer is in dist\ ^(DuplicateAudioFinder-Setup.exe^).
) else (
    echo WARNING: ISCC.exe not found on PATH - skipped installer step.
    echo The runnable app folder is in dist\DuplicateAudioFinder\.
    echo Install Inno Setup and re-run, or run: ISCC build\installer.iss
)

echo.
echo BUILD COMPLETE.
goto :eof

:error
echo.
echo BUILD FAILED (exit code %errorlevel%).
exit /b %errorlevel%
