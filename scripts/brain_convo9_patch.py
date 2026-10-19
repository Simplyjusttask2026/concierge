import pathlib
brain_path = pathlib.Path('BRAIN.md')
trail_path = pathlib.Path('BRAIN_UPDATES/2026-10-19-convo9-x-api-timers-ads.md')
brain = brain_path.read_text(encoding='utf-8')
if 'CONVO 9 ADDENDUM' in brain:
    print('CONVO 9 already in BRAIN.md - skipping')
    raise SystemExit(0)
trail = trail_path.read_text(encoding='utf-8')
marker = '## === CONVO 9 ADDENDUM'
idx = trail.find(marker)
if idx == -1:
    print('ERROR: marker not found in trail')
    raise SystemExit(1)
addendum = trail[idx:].strip()
new = brain.rstrip() + '\n\n' + addendum + '\n'
brain_path.write_text(new, encoding='utf-8')
print(f'BRAIN.md updated: {len(brain)} -> {len(new)} chars')
