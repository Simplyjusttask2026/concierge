import pathlib, sys
p = pathlib.Path('scripts/zoho_direct_first_patch.py')
s = p.read_text()
bad1 = 'during CRM test' + chr(34) + ' ' + chr(34) * 3
good1 = 'during CRM test' + chr(92) + chr(34) * 4
bad2 = 'during refresh test' + chr(34) + ' ' + chr(34) * 3
good2 = 'during refresh test' + chr(92) + chr(34) * 4
if s.count(bad1) != 1:
    print('FAIL: bad1 count', s.count(bad1)); sys.exit(1)
if s.count(bad2) != 1:
    print('FAIL: bad2 count', s.count(bad2)); sys.exit(1)
s = s.replace(bad1, good1).replace(bad2, good2)
p.write_text(s)
print('Fixed helper anchors in zoho_direct_first_patch.py')
