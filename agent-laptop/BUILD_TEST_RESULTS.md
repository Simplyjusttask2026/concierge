# Dell concierge development test record

2026-10-28: Downloaded the exact committed Python files from commit 181f423f3b7ecf9734a0126efa5a06f80c7d8b83 and compiled them in the remote Linux sandbox. All 18 offline unit tests passed.

Covered: candidate keyword matching, sensitive/commercial skips, truthful callback template, observation dedupe, exact owner confirmation, draft expiry, STOP, replay prevention, edit-after-attempt rejection, worker lock, account host restrictions, missing browser adapters failing closed, disabled email, missing local model, mocked SMTP success, mocked SMTP uncertainty, and bulk-recipient rejection.

SMTP was mocked: ZERO real messages sent. No Nextdoor/Facebook posts/comments/DMs, calls, paid services or Dell installation performed. Tests are not proof of Windows runtime, Playwright selectors, real account access, delivered email, local model quality, 24/7 uptime or Zoho Voice answering.

The local Tk control panel is a new interface for the same queue and adapters. Its real Windows UI must be checked on the Dell. New code does not change the unimplemented capabilities listed in CONCIERGE_BUILD.md.
