@echo off
REM Simply Just Task - Laptop Agent install (Anthony: double-click this)
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m playwright install chromium
echo.
echo DONE. Next: run login_nextdoor.bat and log into Nextdoor YOURSELF. AI never sees your password.
pause
