"""Credential circuit breaker. No network or connections at import."""
import threading
import time

class DirectCircuit:
    def __init__(self,clock=time.monotonic):
        self.clock=clock;self.until=0;self.lock=threading.Lock()
    def allowed(self):
        with self.lock:return self.clock()>=self.until
    def failed(self,error):
        permanent=any(t in str(error).lower() for t in ('invalid_code','invalid_client','invalid_token','invalid_scope'))
        with self.lock:self.until=self.clock()+(3600 if permanent else 60)
    def healthy(self):
        with self.lock:self.until=0

CIRCUIT=DirectCircuit()

def plain(value):
    if isinstance(value,dict):return value
    for name in ('model_dump','dict'):
        method=getattr(value,name,None)
        if callable(method):
            result=method()
            if isinstance(result,dict):return result
    return {'error':'unrecognized provider response'}

def rejected(value):
    node=plain(value)
    for _ in range(6):
        if node.get('error') or node.get('successful') is False:return True
        status=node.get('status')
        if isinstance(status,dict) and isinstance(status.get('code'),int) and status['code']>=300:return True
        rows=node.get('data')
        if isinstance(rows,list):return any(isinstance(row,dict) and (row.get('status')=='error' or row.get('code') not in (None,'SUCCESS')) for row in rows)
        if not isinstance(rows,dict):return False
        node=rows
    return True

def safe_to_fallback(error):
    return any(t in str(error).lower() for t in ('invalid_code','invalid_client','invalid_token','invalid_scope','not configured','does not support slug','module_api_name missing','http 401','http 403'))

def execute(slug,args,direct,bridge,configured,circuit=CIRCUIT):
    crm=slug.startswith('ZOHO_') and 'MAIL' not in slug
    read=slug.startswith(('ZOHO_GET_','ZOHO_SEARCH_','ZOHO_LIST_','ZOHO_COUNT_'))
    if crm and configured and circuit.allowed():
        try:result=plain(direct(slug,args))
        except Exception as ex:result={'error':'uncertain direct response: '+type(ex).__name__}
        if not rejected(result):circuit.healthy();return result
        error=result.get('error','direct operation rejected');circuit.failed(error)
        if not read and not safe_to_fallback(error):
            return {'error':'direct CRM write unconfirmed; inspect CRM before retry','uncertain':True}
    try:return plain(bridge(slug,args))
    except Exception as ex:return {'error':'CRM bridge failed: '+type(ex).__name__,'uncertain':not read}
