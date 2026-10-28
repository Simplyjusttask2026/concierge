@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
 echo The new concierge build is not installed. Run install_concierge.bat after review.
 pause
 exit /b 1
)
.venv\Scripts\python.exe concierge_panel.py
if errorlevel 1 pause
