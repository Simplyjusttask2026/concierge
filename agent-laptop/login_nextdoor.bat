@echo off
REM Opens the agent browser so YOU can log into Nextdoor once
python -c "from playwright.sync_api import sync_playwright; import pathlib; p=sync_playwright().start(); ctx=p.chromium.launch_persistent_context(str(pathlib.Path('browser_profile').resolve()), headless=False); pg=ctx.pages[0] if ctx.pages else ctx.new_page(); pg.goto('https://nextdoor.com/news_feed/'); input('Log in, then press Enter here...'); ctx.close(); p.stop()"
echo Saved. Now run run_once.bat to test.
pause
