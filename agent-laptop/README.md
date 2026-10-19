# Simply Just Task - Laptop Agent
Your dedicated AI for this laptop. It hunts Nextdoor leads, saves them, emails you a report. Calls/texts are OFF until you turn them on (see comms.py).

## One-time setup (15 min, you click)
1. Download this folder: https://github.com/Simplyjusttask2026/concierge/tree/main/agent-laptop
2. Settings > Accounts > Other users > Add account > Nextdoor Agent. Sign in as that user.
   CORRECTION to old SOP: BRAIN (2026-10-19) says PERSONAL Nextdoor only for hunting. Log into PERSONAL here, not Business. Kernel is no longer MAIN - this laptop is the hunter.
3. Power: Screen off Never, Sleep Never (plugged in). Lid close = Do nothing when plugged in.
4. Double-click install.bat
5. Double-click login_nextdoor.bat - log into Nextdoor PERSONAL yourself - Enter. Never share password in chat.
6. Double-click run_once.bat - watch it scroll the feed (read-only). Check data/leads.csv + data/report_*.txt
7. Auto-run every 2h: right-click install_schedule.ps1 > Run with PowerShell.

## What it does every run
Reads feed, scores posts, >=80 = real lead, drafts a neighborly comment, saves to data/leads.csv, writes a report. NO post/comment/DM/call/text is sent. You approve each send: go comment <Name>

## Calls / Texts / Emails - honest truth
- Email: works via Zoho (concierge /run-daily, max 10/day + report to you).
- Calls: AI caller exists but has NO phone number. Cannot call/answer until a Retell number exists (costs money). FREE-ONLY: do NOT buy without you saying so.
- Texts: no texter wired. SMS needs paid balance. WhatsApp needs a numeric WABA ID.
Set env SJT_GO_EMAILS=1 / SJT_GO_CALLS=1 / SJT_GO_TEXTS=1 only after you approve that channel.

## Files
SOUL.md (brain) | agent.py (hunter) | comms.py (gates) | data/leads.csv + reports | browser_profile/ (your login, never share)
