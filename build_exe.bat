@echo off
setlocal

set PROJECT_ROOT=%~dp0
pushd %PROJECT_ROOT%

if not exist .venv (
    python -m venv .venv
)

call .venv\Scripts\activate

python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install .[build]

pyinstaller --clean --noconfirm RMPrayer.spec
set EXIT_CODE=%errorlevel%

if %EXIT_CODE% neq 0 (
    echo PyInstaller build failed.
) else (
    echo.
    echo Build complete. The executable can be found at %PROJECT_ROOT%dist\RMPrayer.exe
    echo.
)

popd
endlocal & exit /b %EXIT_CODE%
