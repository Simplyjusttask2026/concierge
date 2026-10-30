# Dell / Frankenstein recovery plan — 2026-10-30

Status: source snapshot and documentation backup; NOT a complete disaster-recovery solution.

## Baselines
- Main source commit: 20dce38a8dd004f34585b60022047b67df0815b4.
- Dell feature source commit: 35e8749575bc39bc9159e5c7a1211f79d7ebaeaa (feature/dell-concierge-nextdoor-first).
- Documentation branch: docs/frankenstein-dell-safe-2026-10-30.
- Backup location: new OneDrive folder Simply Just Task AI Safe. Do not enable public sharing.

## Included / excluded
Source ZIPs contain files tracked at each commit, including their historical brain and documentation. ZIPs do not contain Git history, repository secrets, Render environment values, Windows credentials, Dell-only configuration, local database/leads/browser sessions, live CRM/calendar contents or the full OneDrive master library. This is not a full Dell image and is not a newly encrypted vault.

## Safe restoration procedure (not yet executed)
1. Retrieve the appropriate archive and its checksum manifest. Verify SHA-256 and ZIP integrity before use.
2. Extract to a NEW test folder or replacement computer, not over an existing working installation.
3. Read the version's setup documentation and inspect scripts. Install compatible Python/dependencies in an isolated environment only after owner confirmation. Dependency availability may change; a source ZIP alone does not guarantee an offline reinstall.
4. Restore non-secret configuration from a separately verified backup when available. Recover credentials from the owner's password manager/provider flow; do not put them in chat or GitHub. Reauthenticate browser/mail connections locally.
5. Restore Dell database/leads from an application-consistent backup when one exists; do not overwrite a newer database. Keep live cloud integrations disabled during the restore test.
6. Run offline/unit tests, then supervised read-only checks. Revalidate recipients, business contacts and calendar connections. Do not send messages, enable jobs or replace production until separately approved.
7. Record exact version, date, test results and rollback path. Only then label restoration proven.

## Remaining backup work
- Determine actual Dell install/data paths and exact installed version.
- Stop application writers before an application-consistent local database copy; include SQLite journal/WAL files as appropriate or use SQLite backup support. Do not copy a changing DB blindly.
- Make a separate private backup of approved business knowledge and source inventory after privacy review.
- Protect secrets/session material separately with encryption and owner-controlled recovery; never put unencrypted cookies in public source backups.
- Keep an encrypted offline/external copy in addition to cloud storage. Cloud sync and Git branches alone are not independent, immutable backups.
- Agree retention, frequency and recovery targets. Do not delete old versions or configure recurring jobs under this documentation-only authorization.

## Non-interference
No edits to application code, workflows, Render settings, website, CRM data, calendar data, live Dell configuration, schedules or outbound communications. No merge/deploy or paid service authorized. Existing historical records remain historical, not newly verified.
