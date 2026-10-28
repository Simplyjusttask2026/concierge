import ast
import hashlib
from pathlib import Path
p=Path('concierge.py');raw=p.read_bytes()
if b'from zoho_route_policy import execute as _route_zoho' in raw:
    print('Routing repair already applied')
else:
    assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()=='09cf6f689dd38d902b8d0b13776a9ad64d00d8e9','Concurrent source change; refusing overwrite'
    s=raw.decode();t=ast.parse(s);fn=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='zoho_exec')
    replacement='''def zoho_exec(slug, args):
    from zoho_route_policy import execute as _route_zoho
    def bridge(tool_slug, arguments):
        try:
            return composio.tools.execute(slug=tool_slug, arguments=arguments, user_id=COMPOSIO_USER_ID, dangerously_skip_version_check=True)
        except TypeError as ex:
            text=str(ex)
            if 'unexpected keyword argument' not in text and 'positional-only' not in text:
                raise
            return composio.tools.execute(tool_slug, arguments, COMPOSIO_USER_ID)
    return _route_zoho(slug, args, _zoho_direct_exec, bridge, _zoho_direct_configured())
'''
    lines=s.splitlines(keepends=True);out=''.join(lines[:fn.lineno-1])+replacement+''.join(lines[fn.end_lineno:])
    ast.parse(out);p.write_text(out)
    print('Routing repaired without any account calls')
