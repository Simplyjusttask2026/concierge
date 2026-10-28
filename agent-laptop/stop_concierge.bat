@echo off
cd /d "%~dp0"
if not exist concierge_data mkdir concierge_data
type nul > concierge_data\STOP
echo STOP requested. Already submitted messages/calls cannot be recalled.
pause
