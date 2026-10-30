# 2026-10-30 — Dell AI, Frankenstein integration and backup confirmation

Public-safe conversation summary, not a verbatim transcript. Historical notes do not prove present runtime health.

## Owner requirements and authorization
- Owner wants the complete Dell assistant capability list integrated into the existing Frankenstein project, not a competing standalone system.
- Preserve working website, CRM, booking, cloud deployment, schedules and local Dell installation. Do not duplicate production jobs or databases.
- Owner requested safe backups, recovery documentation, and saving this conversation to project memory.
- Owner confirmed documentation on a separate branch and a separate OneDrive backup. Authorization excludes deployment, live sending, live automation changes, purchases and destructive operations. Broader feature implementation remains planned, not completed by this update.
- Owner prefers individual email replies, composing on request, the correct sending mailbox, and an owner copy of every outgoing email. Owner requested sending without review; that is NOT implemented or enabled. Existing send-confirmation controls remain.
- Copy/BCC address is still unconfirmed. Never infer it from a connected-account address.

## What was observed
- Owner reported the control panel opens on the Dell. This is not proof of successful mailbox login, Nextdoor login, model setup, monitoring or sending.
- Prior source inspection found the panel, adapters, assistant and tests on feature/dell-concierge-nextdoor-first. Main and the Dell feature branch are different versions.
- Existing Dell source supports read mail, draft editing and explicitly confirmed email sends. Full reply threading and owner BCC were absent from the inspected implementation. AI drafting uses a local model when configured and historical BRAIN content; model operation was not verified on the Dell.
- Source contains residential-only/commercial exclusions while newer business documents mention commercial work. Resolve policy before changing behavior.
- OneDrive master folder and Microsoft Copilot Chat Files contain many more documents than the initial subset. Four initial master documents and seven selected Copilot-folder files received an initial review; the entire collection has NOT been fully reviewed or installed.

## Source-review findings
- Master AI file contains services, contacts, hours, pricing examples, travel and payment guidance. These remain document-sourced claims needing current-policy validation.
- Contact emails conflict across documents; confirm current sending/reply addresses and phone numbers.
- Customer estimate is one specific job with private customer data, not universal pricing. Keep identities and addresses out of general knowledge and public commits.
- Nextdoor playbook offers service keywords and lead qualification concepts, not authorization for mass outreach.
- Kickoff inputs and Undo are historical CrewAI/Excel/Zapier/n8n planning and troubleshooting transcripts; success claims are not live verification. Do not import sample leads as real customers.
- Brand-story draft includes personal narrative and stale relative dates; do not automatically insert private details into customer replies.
- Phone-training PDF is a directory index of recording filenames, not audio or conversation transcripts. No phone conversations were trained from it.

## Full target capabilities — all require implementation/verification as applicable
1. Clean business knowledge with source provenance, conflict flags and private-data separation.
2. Read and classify email; compose and draft individual replies; preserve thread headers; configurable owner CC/BCC; prevent duplicates/loops; verified recipient/account; confirmation before sending.
3. Permitted Nextdoor intake, source links, lead qualification, personalized response drafts and duplicate detection. No platform bypass or invented contact information.
4. Shared CRM lifecycle, follow-up dates, owner assignment, opt-outs and conversation history using existing Frankenstein infrastructure where verified.
5. Customer-service discovery, respectful sales support, estimates with nonbinding ranges, management escalation for uncertain quotes/discounts/contracts.
6. Real calendar availability, travel/buffers, proposed appointments, confirmations and job-status tracking; no unverified bookings.
7. Voice intake, summaries and handoff after provider/cost/consent verification; opening Zoho Voice is not AI answering.
8. Customer-photo review and clearly labeled generated marketing images using supported services; never portray generated examples as real completed work.
9. Scheduled checks, locking, error reporting, pause/stop, reboot recovery and repeat-send protection; do not enable untested 24-hour operation.
10. Versioned backups, checksums, recovery instructions and a restore exercise before declaring recovery proven.

## Backup scope and limits
- New separate OneDrive folder: Simply Just Task AI Safe. Initial permissions query returned the owner entry only; no anonymous sharing created.
- Baseline main source: 20dce38a8dd004f34585b60022047b67df0815b4.
- Baseline Dell source: 35e8749575bc39bc9159e5c7a1211f79d7ebaeaa.
- Source ZIP snapshots are not full Git history or a machine image. They do NOT include GitHub/Render secrets, Dell-only settings/data/browser profile, live CRM/calendar records, or all OneDrive business documents.
- No encrypted vault, recurring backup schedule, full-device backup or complete restore test has been established by this documentation task. Do not claim otherwise.
- Keep credentials out of GitHub and chat; plan an encrypted external/offline backup and owner-controlled credential recovery separately.

## Continuation
See FRANKENSTEIN_STATUS.md and SOPS/DELL_RECOVERY_PLAN.md on this documentation branch. No runtime code, live CRM, calendar, deployment, messages or scheduled automation changed. BRAIN.md itself is preserved; this entry uses the repository's existing BRAIN_UPDATES memory convention. Do not merge or deploy without a separate confirmation.
