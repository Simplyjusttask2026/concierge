import pathlib, ast
block = pathlib.Path('scripts/crewai_bridge_block.txt').read_text()
p = pathlib.Path('concierge.py')
t = p.read_text()
anchor = '@app.route("/run-social", methods=["GET", "POST"])'
if '/ingest-crewai-leads' not in t:
    assert t.count(anchor) == 1, 'anchor missing'
    t = t.replace(anchor, block.rstrip() + chr(10)*3 + anchor, 1)
    ast.parse(t)
    p.write_text(t)
    print('concierge.py bridge inserted, syntax OK, chars', len(t))
else:
    print('concierge.py bridge already present')
yml = pathlib.Path('.github/workflows/daily-9am.yml')
y = yml.read_text()
if 'MACHINE_TOKEN:' not in y:
    old = '          CREWAI_BEARER_TOKEN: ${{ secrets.CREWAI_BEARER_TOKEN }}' + chr(10)
    assert y.count(old) == 1, 'yml anchor missing'
    y = y.replace(old, old + '          MACHINE_TOKEN: ${{ secrets.MACHINE_TOKEN }}' + chr(10), 1)
    yml.write_text(y)
    print('daily-9am.yml MACHINE_TOKEN added')
else:
    print('daily-9am.yml already has MACHINE_TOKEN')
c = pathlib.Path('concierge.py').read_text()
assert '/ingest-crewai-leads' in c and 'simplybook' in c and '15min' not in c
print('BRIDGE APPLY OK')
