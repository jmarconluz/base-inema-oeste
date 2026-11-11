#!/bin/bash
# Um ciclo de drenagem depois que os lotes foram copiados para /mnt/user-data/uploads.
# Uso: bash ciclo.sh '<json dos lotes [{"nome":..., "arquivo":...}]>'
# Imprime: (1) listas para device_commit_files no E:, (2) grandes, (3) JS de confirmação, (4) marcadores do C:.
set -e
cd "$(dirname "$0")"
sleep 5
python3 drenar.py preparar "$1" >/tmp/prep.txt
cat /tmp/prep.txt | python3 -c "import sys,json;d=json.load(sys.stdin);print('RESUMO', json.dumps(d['lotes'],ensure_ascii=False))"
python3 - <<'EOF'
import json
g = json.load(open('/tmp/gravar.json'))
r = json.load(open('/tmp/lotes_res.json'))
for i, c in enumerate(g['e']):
    print('=== E', i); print(json.dumps(c, ensure_ascii=False))
print('=== GRANDES'); print(json.dumps(g['grandes'], ensure_ascii=False))
print('=== JS')
print('const R=' + json.dumps([[x['lote'], x['ok'], x['bytes']] for x in r], ensure_ascii=False) + '; for(const [l,ok,b] of R) await BOMBA.confirmar(l,ok,b); JSON.stringify(await BOMBA.status())')
print('=== MARCADORES'); print(json.dumps(g['marcadores'], ensure_ascii=False))
EOF
