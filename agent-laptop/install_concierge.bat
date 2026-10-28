@echo off
cd /d "%~dp0"
python -m venv .venv
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install -r requirements-concierge.txt
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m playwright install chromium
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m unittest -v test_concierge.py
if errorlevel 1 goto fail
.venv\Scripts\python.exe concierge_assistant.py init
if errorlevel 1 goto fail
echo Setup complete. No timer or account connection installed. Read CONCIERGE_BUILD.md.
pause
exit /b 0
:fail
echo Setup FAILED. Stop here and share the error, never credentials.
pause
exit /b 1
