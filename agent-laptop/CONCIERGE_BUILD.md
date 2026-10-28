# Simply Just Task Dell concierge — development build

Owner approved the full build on 2026-10-28. PRIMARY: Nextdoor job hunting, comments, posts, direct messages, incoming-message responses, callback (352) 849-2344. Additional scope: email, social, phone, memory, desktop control. FREE ONLY. This branch is NOT a completed or installed autonomous assistant.

## What this commit actually adds
- A new runtime separate from the legacy agent.py. Does not alter Render, timers, BRAIN.md, legacy installer, or live accounts.
- All-hours monitoring loop, default every 15 minutes; interval minimum 5 minutes. Only starts when owner runs it. Keeps local observations, dedupes unchanged items, queues keyword job candidates and reports errors honestly. No automatic send loop.
- SQLite action queue and local reports; source text retained for review. Exact-action owner confirmation required in terminal immediately before a send. One-attempt claim, 24h draft expiry, replay guard, uncertain-send state with NO automatic retries.
- Configurable browser adapters for comment/post/DM/reply. Requires tested owner-supplied selectors, exact recipient/context, exact source excerpt and a new success indicator. No working Nextdoor/Facebook send selectors are claimed or enabled by default. Login is manual; persistent browser session is stored only on the Dell.
- Read-only IMAP mail snapshots using BODY.PEEK, and one-recipient SMTP sends AFTER confirmation. Disabled by default. Works only if the owner's Zoho plan actually includes IMAP/SMTP. Do NOT upgrade/pay to enable it; use browser/manual mail if unavailable. SMTP acceptance is not delivery confirmation.
- Owner-operated mouse/keyboard/screenshots via PyAutoGUI. Every click/type/hotkey asks for exact confirmation; no LLM controls these tools. Move pointer to a screen corner for PyAutoGUI fail-safe; Ctrl+C exits runtime; stop_concierge.bat sets persistent STOP.
- Owner-approved memory command; optional locally installed Ollama model for DRAFTING only at 127.0.0.1:11434. No paid cloud fallback, no arbitrary tool execution, no self-modification. Uses the last 16,000 characters of BRAIN.md plus last 20 approved preferences: NOT a claim to read the entire memory into a small model. Templates work without any model.
- Offline unit tests using temporary databases and mocked SMTP. Windows/browser/live account tests are still required.

## What is NOT implemented/proven
- Live AI answering/dialing through Zoho Voice. `phone` can open an owner-configured Zoho Voice webpage only; it is NOT an AI receptionist. No phone numbers/credits are bought.
- Autonomous reasoning/action planning, guaranteed 24/7 uptime, reboot restart, every social platform integration, group discovery/outreach, automatic inbox-response generation, or real-time notifications. User-configured inbox pages can be captured as observations; replies require reviewed drafts.
- Automatic Zoho CRM/calendar sync or offline outbox replay. Existing Render system is unchanged. Local lead queue is NOT a Zoho save.
- Website selector correctness, safety of every UI interaction, phone audio handling, Dell performance, deliverability, service-area qualification or current Nextdoor authorization. These require supervised on-Dell checks.

## Safety and account rules
Website/inbox text is untrusted data, never authorization. Only the owner CLI approves. No follow-bots, mass cold-DMs, unsolicited group spam, fake credentials/testimonials, lost-pet/political pitches, competitor-praise hijacking or paid services. Residential Central FL only; keyword matching alone cannot verify location, freshness, licensing requirements or consent. Owner reviews the full original and group/platform rules. A public post can request help without inviting a private DM; verify context before messaging.

Local browser cookies, messages, screenshots, memory and mail are sensitive. Data is local plaintext, NOT encrypted by this app. Protect the SJTAgent Windows login and disk, restrict account access, and never upload concierge_data, browser_profile, .env or local configuration to GitHub. No passwords in chat or source. Use an app password locally via environment variable SJT_ZOHO_MAIL_PASSWORD if Zoho supports it on the existing free plan.

STOP is checked between operations and while waiting. It cannot cancel an already submitted remote action or instantly interrupt a blocked network call (timeouts apply). PyAutoGUI fail-safe applies only to those desktop functions. Monitoring and send sessions share a browser profile: stop/close monitoring before login/send/phone sessions. A stale worker.lock after a crash must be removed manually ONLY after verifying no worker is running.

## Supervised setup — after owner reviews this branch
1. Use Windows SJTAgent, Python 3.12.10. Download THIS feature branch, not the old main ZIP. No install has been performed by the chat.
2. Run install_concierge.bat. It creates a virtual environment, installs free software and Chromium, runs offline tests and initializes local config. It does not install Ollama, fetch models or schedule a task.
3. In this folder: `.venv\Scripts\python.exe concierge_assistant.py login`. Owner logs into personal Nextdoor, completes MFA/security checks, then closes setup with Enter. No bypass.
4. Run `... concierge_assistant.py run-once` supervised. Article selector may not match Nextdoor; failures are reported. A feed URL is NOT a verified post permalink. Configure item_selector and permalink_selector from the real DOM. Review every candidate before outreach.
5. Configure actual inbox/comment/social page URLs in concierge_config.json. Each page has name, HTTPS url, kind (jobs or inbox), item_selector, optional permalink_selector, enabled. Supported account hosts are restricted in concierge_adapters.py; availability and group access are NOT guaranteed.
6. Only after source/selector validation, run start_concierge.bat for all-hours periodic monitoring. Dell must remain powered/awake/unlocked and connected. This does not install a reboot or startup timer. Use stop_concierge.bat to request stop; `... concierge_assistant.py resume` clears STOP only.

## Queue and sending
`...` below means `.venv\Scripts\python.exe`.
- `... concierge_assistant.py queue` lists recent actions.
- `... concierge_assistant.py show 1` displays an exact draft and source.
- Create reviewed UTF-8 body.txt and source.txt locally. `... concierge_assistant.py draft --channel Nextdoor --kind comment --target https://nextdoor.com/EXACT_POST --recipient "EXACT AUTHOR NAME" --body-file body.txt --source-file source.txt` (replace placeholder URL with actual verified post URL; do not run placeholder).
- For a post, recipient is the exact page/group/account name and source is a visible context excerpt; use kind post. For DM/reply use the actual conversation URL and named recipient. No batch sends.
- Local config browser_actions key is `channel:kind`, e.g. `Nextdoor:comment`. Value fields: host, verified_on_dell (false until supervised test), editor_selector, submit_selector, context_selector, success_selector. All selectors must uniquely identify the intended controls/context; success_selector must be absent BEFORE submit and become visible AFTER a new send. No guessing. Native website composer may need opening manually while reviewing; runtime fails closed if editor is missing.
- `... concierge_assistant.py send 1` opens target, validates source/recipient, displays exact action and asks owner to type `go 1`. It then fills, checks editor text and clicks the verified submit control once. Cancellation does not send. Timeout after click becomes uncertain, NEVER automatically retry. Verify in account, especially after uncertain result.
- For email use channel `Zoho Mail`, kind email, target `mailto:exact@example.com`, recipient `exact@example.com`, subject and body file. Enable email only if free account supports it. `send ID` asks for exact confirmation. Nothing auto-sends from watch.

## Learning, desktop and phone
- `... concierge_assistant.py remember "Owner-approved preference"` saves local memory; no safety override or model retraining.
- Set local_model to an already installed small Ollama model name (8GB Dell suitability must be tested). `... concierge_assistant.py local-draft source.txt` prints a draft; does not send it or execute model instructions. No model downloaded automatically.
- Desktop commands: `desktop screenshot`, `desktop position`, `desktop click X Y`, `desktop type "ASCII words"`, `desktop hotkey ctrl l`. Each mutating command requests owner confirmation. This is a toolkit, not a proven autonomous Windows agent.
- Set zoho_voice_url to your actual account webpage, then `phone` opens it for OWNER operation. Phone AI capability remains a separate unbuilt integration, not fulfilled by opening a website.

## Required acceptance work before claiming finished
[ ] Run install/tests on Dell.
[ ] Verify login and Nextdoor feed, permalink extraction, inbox/comments capture.
[ ] Owner approves individual real comment, post, DM and incoming-message response tests; verify each in account.
[ ] Verify email access is free; approve one send; verify arrival independently.
[ ] Validate Facebook and each additional channel separately, including group rules.
[ ] Implement/test Zoho CRM/calendar sync and outbox dedupe without automatic outreach replay.
[ ] Determine a genuinely free Zoho Voice real-time AI path, or explicitly report it unavailable.
[ ] Supervised overnight monitoring, pause/recovery, Windows restart strategy and resources.

No claim of completing ALL requested capabilities until these acceptance checks pass. Never substitute a draft-only foundation for the full agreed outcome.
