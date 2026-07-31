@echo off
setlocal
cd /d "%~dp0"
py -3.12 --version >nul 2>nul
if not errorlevel 1 (
  py -3.12 -m uvicorn main:app --host 127.0.0.1 --port 8000
  goto :end
)

set "CODEX_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not exist "%CODEX_PYTHON%" (
  echo Python 3.12 is required. Install it, then run this launcher again.
  exit /b 1
)
set "PYTHONPATH=%CD%\venv\Lib\site-packages"
"%CODEX_PYTHON%" -m uvicorn main:app --host 127.0.0.1 --port 8000

:end
endlocal
