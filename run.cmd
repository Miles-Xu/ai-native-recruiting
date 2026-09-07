@echo off
setlocal
where uv >nul 2>nul
if errorlevel 1 (
    echo uv is required. See https://docs.astral.sh/uv/getting-started/installation/ 1>&2
    exit /b 127
)
set "UV_CACHE_DIR=%~dp0.cache\uv"
set "UV_PYTHON_INSTALL_DIR=%~dp0.cache\python"
set "PLAYWRIGHT_BROWSERS_PATH=%~dp0.cache\browsers"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
uv run --project "%~dp0." --locked python "%~dp0scripts\workflow.py" %*
exit /b %errorlevel%
