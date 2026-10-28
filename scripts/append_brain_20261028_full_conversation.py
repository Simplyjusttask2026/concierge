"""Append the owner-authorized full transcript, preserving every prior BRAIN byte."""
from pathlib import Path
import hashlib
import os

brain = Path('BRAIN.md')
source = Path('BRAIN_UPDATES/2026-10-28-dell-concierge-full-conversation.md')
marker = b'<!-- BEGIN SJT FULL CONVERSATION 2026-10-28 DELL NEXTDOOR FIRST -->'
ending = b'<!-- END SJT FULL CONVERSATION 2026-10-28 DELL NEXTDOOR FIRST -->'
expected_prefix_size = 96976
expected_prefix_hash = 'c05305b863c74529434885c9643a9b5d7185647a35f4465b1c8ca2cc2afe5df9'
original = brain.read_bytes()
transcript = source.read_bytes()
assert transcript.count(marker) == 1 and transcript.count(ending) == 1
assert b'after i open the folder new bild then what do i do and go update brain' in transcript
assert b'## Continuation state and verified build record' in transcript
assert len(original) >= expected_prefix_size
assert hashlib.sha256(original[:expected_prefix_size]).hexdigest() == expected_prefix_hash, 'Historical BRAIN prefix changed; stop for manual review'
if marker in original:
    assert original.count(marker) == 1 and original.endswith(transcript), 'Partial or changed append; stop for review'
    print('Already appended exactly; no change')
else:
    updated = original + b'\n\n' + transcript
    assert updated[:len(original)] == original
    assert updated.endswith(transcript)
    temporary = brain.with_suffix('.append.tmp')
    temporary.write_bytes(updated)
    os.replace(temporary, brain)
    verified = brain.read_bytes()
    assert verified == updated
    print('Append verified:', len(original), '->', len(verified), 'bytes')
    print('Original prefix SHA256:', hashlib.sha256(verified[:expected_prefix_size]).hexdigest())
    print('Transcript SHA256:', hashlib.sha256(transcript).hexdigest())
