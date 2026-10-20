# BRAIN UPDATE - 2026-10-20 convo - BASE44 BOOKS VIA WEBSITE /book-a-consultation + BOOKING LINK RULE
Owner statement this convo: Base44 is an app to book appointments. Owner wants to use the link of the website to gain exposure: https://www.simplyjusttask.com/book-a-consultation - the link takes you to the page with the Cal.com on there. Upload convo to brain file.

## OWNER RULE - BASE44 BOOKING (LOCKED)
Use website booking page for exposure: https://www.simplyjusttask.com/book-a-consultation . Do NOT send customers from Base44 (or ads/social meant for public exposure) straight to raw cal.com link when owner wants website exposure. Flow: Base44 app button/link -> simplyjusttask.com/book-a-consultation -> Cal.com embedded on page -> booking. Zoho remains lead vault, Cal remains booking machine, Base44 remains front door only.

## VERIFIED LIVE 2026-10-20 ~02:32 UTC (1 page scrape, $0.0038)
URL https://www.simplyjusttask.com/book-a-consultation status 200. Page title area: Book an Appointment. Embedded Cal shows Simply Just Task / Simply Stress-Free Booking / Book a consultation, service, or follow-up appointment in just a few clicks. One Less Thing To Worry About. Durations shown: 30m, 45m, 1h, 2h. Links on page include https://cal.com/simply-justtask?redirect=false and https://go.cal.com/booking (Cal embed) - matches Event 7325379 slug simplybook, direct link https://cal.com/simply-justtask/simplybook. Calendar showed October 2026 with Available times for Tuesday, October 20, 2026 e.g. 2:00pm-8:30pm. Squarespace site, owner site for exposure/SEO. Page also has Simply Just Task Concierge chat widget text present.
Note: scrape markdown contained Something went wrong line near top - possible widget artifact in scraper render, Cal embed itself rendered fully with times. Do not claim site broken from that alone; verify in browser if owner reports issue.

## HOW TO LINK BASE44 (owner does in Base44, no code yet)
1. In Base44 app: add Book Appointment / Book a Consultation button.
2. Set its link to exactly https://www.simplyjusttask.com/book-a-consultation
3. Same link for WhatsApp reply button, social bio CTA, ads landing (except Ads Team rule: ads use phones Anthony 352-849-2344 / Michael Sabo 321-745-5894 per convo11-12, do not override ads rule without owner go).
4. For internal/direct AI outreach where website exposure not needed (existing concierge.py /run-daily email), Cal direct link remains https://cal.com/simply-justtask/simplybook. Do NOT change concierge CAL_LINK to website page without owner code go + test that embed loads via email client click.
5. Future automated Base44->Zoho: Base44 webhook -> Render /ingest-base44-leads (to build) or API poll -> Zoho Lead_Source Base44 (needs Zoho picklist add; until then Web Research + Description Source: Base44). Needs Fix #3 default connections first. No native Composio Base44 toolkit.

## STANDING LOCKS (unchanged)
Render production config FROZEN - do not change env, do not set COMPOSIO_USER_ID. Original Composio user login tasksupport@simplyjusttask.com. Fix #3 correct path = connect zoho/zoho_mail/facebook/instagram/twitter for user default, owner must say connect default. No /run-daily, /run-social, CrewAI run, email/text/post/call started in this convo. Upload only.
Prior notes: BRAIN_UPDATES/2026-10-20-convo-daily-schedule-checklist.md b13d089, 2026-10-20-convo-frankenstein-fix3.md 7cbd98b, 2026-10-20-convo-fix3-no-render-change.md a9930de. This note adds booking-link-for-exposure rule on top.
