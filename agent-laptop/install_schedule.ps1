# Run in PowerShell. Creates 2-hour checks 7am-10pm ET.
$py = (Get-Command python).Source
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
foreach($t in @("07:00","09:00","11:00","13:00","15:00","17:00","19:00","21:00")){
  $name = "SJT Nextdoor Check " + $t.Replace(":","")
  schtasks /Create /TN $name /TR "`"$py`" `"$dir\agent.py`" --once" /SC DAILY /ST $t /F | Out-Host
}
Write-Host "Scheduled. Laptop must be ON, plugged in, and logged in for browser checks."
