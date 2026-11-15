"""Remonta pacotes exportados do navegador (gzip + base64 em partes) e grava o JSON decodificado.

Os coletores (coletor_multas.js, coletor_tjba.js, coletor_lex.js) devolvem cada parte num "envelope":
    {"chave": "...", "parte": 0, "partes": 3, "n": 123, "dados": "<base64>", "pad": "####..."}
O enchimento (pad) faz o resultado do javascript_tool passar de 100 mil caracteres; assim ele é salvo
num arquivo (/tmp/claude-tool-results/.../mcp-remote-devices-Claude_Browser__javascript_tool-*.txt)
em vez de entrar na conversa. Este script lê esses arquivos, junta as partes de cada chave e decodifica.

Uso:
    python scripts/decodificar_partes.py SAIDA_DIR [arquivo1 arquivo2 ...] [--chave CHAVE]
Sem arquivos, procura em /tmp/claude-tool-results/**/ todos os resultados do javascript_tool.
Grava SAIDA_DIR/<chave>.json para cada chave completa e avisa as partes que faltam.
Também aceita o formato antigo ({"ano", "parte", "partes", "dados"} e {"tipo", "i", "dados"}).
"""
import base64, glob, gzip, json, os, sys
from collections import defaultdict


def ler_envelope(caminho):
    bruto = open(caminho, encoding='utf-8', errors='replace').read()
    try:
        blocos = json.loads(bruto)
        if isinstance(blocos, list):
            bruto = ''.join(b.get('text', '') for b in blocos if isinstance(b, dict))
        elif isinstance(blocos, dict) and 'dados' in blocos:
            return blocos
    except json.JSONDecodeError:
        pass
    ini = bruto.find('{')
    if ini < 0:
        return None
    try:
        obj, _ = json.JSONDecoder().raw_decode(bruto[ini:])
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) and 'dados' in obj else None


def main():
    args = [a for a in sys.argv[1:]]
    if not args:
        sys.exit(__doc__)
    filtro = None
    if '--chave' in args:
        k = args.index('--chave'); filtro = args[k + 1]; del args[k:k + 2]
    saida, arquivos = args[0], args[1:]
    if not arquivos:
        arquivos = glob.glob('/tmp/claude-tool-results/**/*javascript_tool*.txt', recursive=True)
    grupos = defaultdict(dict); total = {}; meta = {}
    for arq in sorted(arquivos, key=os.path.getmtime):
        env = ler_envelope(arq)
        if not env:
            continue
        if 'chave' in env:
            chave, parte, partes = env['chave'], env.get('parte', 0), env.get('partes', 1)
        elif 'ano' in env:
            chave, parte, partes = 'doe_enx_' + str(env['ano']), env['parte'], env['partes']
        else:
            chave, parte, partes = env.get('tipo', 'pacote'), env.get('i', 0), env.get('partes')
        if filtro and chave != filtro:
            continue
        grupos[chave][parte] = env['dados']          # o arquivo mais novo prevalece
        if partes:
            total[chave] = partes
        meta[chave] = {k: v for k, v in env.items() if k not in ('dados', 'pad')}
    if not grupos:
        sys.exit('nenhum envelope encontrado')
    os.makedirs(saida, exist_ok=True)
    ok = True
    for chave, partes in sorted(grupos.items()):
        n = total.get(chave) or (max(partes) + 1)
        faltam = [i for i in range(n) if i not in partes]
        if faltam:
            print(f'{chave}: FALTAM as partes {faltam} de {n}'); ok = False; continue
        dados = json.loads(gzip.decompress(base64.b64decode(''.join(partes[i] for i in range(n)))))
        esperado = meta[chave].get('n')
        if esperado is not None and isinstance(dados, list) and len(dados) != esperado:
            print(f'{chave}: AVISO {len(dados)} registros, esperado {esperado}')
        destino = os.path.join(saida, chave + '.json')
        json.dump(dados, open(destino, 'w', encoding='utf-8'), ensure_ascii=False)
        print(f'{chave}: {len(dados) if isinstance(dados, (list, dict)) else "?"} registros -> {destino}')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
