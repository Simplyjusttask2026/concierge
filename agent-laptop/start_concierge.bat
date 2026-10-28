@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
 echo Run install_concierge.bat first, only after reviewing CONCIERGE_BUILD.md.
 pause
 exit /b 1
)
.venv\Scripts\python.exe concierge_assistant.py watch
pause
