# Frankenstein reliability repair — NOT DEPLOYED

User approved repair work in chat on 2026-10-28. This is code-only on a separate branch; main, Render, credentials and live accounts are untouched.

Implemented: oldest-eligible CRM paging including the 103 older waiting-lead regression; exclusion of already-reviewed queued leads; dated recycle eligibility; opt-out checks; fail-closed management authentication; POST-only job triggers; tracked completion; atomic day claims; exact-body owner confirmation; one-attempt send controls; provider acceptance before CRM contact status; global per-day approved-email/social caps in shared state; website history; recent Cal pagination; no paid image fallback; CrewAI quota stop.

51 offline tests passed locally, including selected actual pipeline functions with mocked CRM/LLM. No live sends or account integration tests. Large business prompt constants were preserved.

Processing prepares reviewed actions, not automatic outreach. Protected owner-drafts returns exact recipient/body/asset/fingerprint. The send route requires `go send <draft-id> <full-fingerprint>` for that exact action. Ambiguous errors become uncertain; no automatic retry. Provider acceptance is not independent delivery proof.

Activation requires owner authorization, matching MACHINE_TOKEN configuration, SJT_AUTOMATION_ENABLED=true on server/scheduler, an absolute SJT_STATE_PATH backed by durable private storage, and SJT_STATE_PERSISTENT_CONFIRMED=true ONLY after genuinely verifying persistence. Never acknowledge persistence on ephemeral Render storage. Render Free may not supply a durable mount. Do not buy an upgrade; a free durable hosting/state strategy remains an activation blocker.

Instagram requires an owner-approved real direct JPEG URL in SJT_SOCIAL_REAL_PHOTO_URL, from the approved website/photo hosts. Fingerprint includes the asset URL. No generated/paid-image fallback or wrong-account X posting. Copy uses the existing contact compliance helper. Broad autonomous comment/DM handling is not implemented by this patch.

Legacy overlapping schedules are manual-only on this branch. Replacement scheduler checks hourly, catches up in daylight, and waits for observable completion; disabled by default. Nextdoor is labelled self-test-only. CrewAI stays paused pending verified free allowance, without quota bypass or upgrades.

Remaining blockers: Render connector/server account health; genuinely durable free storage; live account/delivery tests; WhatsApp API/template/consent; intended X identity; wider social integrations; actual Dell installation/login/selectors/overnight operation; AI phone answering; mailbox rules; review of CRM duplicates/sample records. No records were deleted/contacted.

Do not merge/deploy or call the business machine fully working based on offline tests. Require owner-approved deployment and supervised exact-action acceptance checks.
