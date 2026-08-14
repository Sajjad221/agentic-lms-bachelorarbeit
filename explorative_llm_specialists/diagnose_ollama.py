from __future__ import annotations
import json, time, urllib.request

BASE='http://localhost:11434'
MODEL='qwen3:14b'

def req(path, payload=None, timeout=60):
    data=None if payload is None else json.dumps(payload).encode('utf-8')
    r=urllib.request.Request(BASE+path, data=data, headers={'Content-Type':'application/json'}, method='GET' if data is None else 'POST')
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8'))

print('1) API erreichbar ...')
print(req('/api/version'))
print('2) Modelle ...')
models=req('/api/tags').get('models',[])
print([m.get('name') for m in models])
print('3) Minimaler Qwen3-Chat (think=false, num_predict=32) ...')
start=time.perf_counter()
out=req('/api/chat', {
    'model': MODEL,
    'messages':[{'role':'user','content':'Antworte exakt mit OK.'}],
    'stream': False,
    'think': False,
    'keep_alive':'10m',
    'options':{'temperature':0,'seed':42,'num_ctx':4096,'num_predict':32},
}, timeout=90)
print('Antwort:', out.get('message',{}).get('content'))
print('Dauer_s:', round(time.perf_counter()-start,2))
print('prompt_eval_count:', out.get('prompt_eval_count'), 'eval_count:', out.get('eval_count'))
print('Diagnose erfolgreich.')
