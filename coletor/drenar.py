#!/usr/bin/env python3
"""Leva os lotes de processos do SEIA (SEIA_lote_*.zip, baixados no C:) para E:\\Downloads\\processos\\<processo>\\.

  python3 drenar.py preparar '<json dos lotes>'   (lotes já copiados para /mnt/user-data/uploads)
      -> valida cada zip de processo dentro do lote, separa um zip por processo, registra a ficha em
         dados/seia/fichas_download.jsonl e grava em /tmp/gravar.json as chamadas de device_commit_files
         (E: + marcador que substitui o lote no C:); imprime, por lote, os itens confirmados e os bytes.
  python3 drenar.py limpar
"""
import json, os, re, shutil, sys, zipfile, io

BASE = os.path.dirname(os.path.abspath(__file__))
FICHAS = os.path.join(BASE, '..', 'dados', 'seia', 'fichas_download.jsonl')
UP = '/mnt/user-data/uploads/Usuario--Downloads'
OUT = '/mnt/user-data/outputs/d'
MARCA = '/mnt/user-data/outputs/marcador.txt'
C_DIR = 'C:\\Users\\Usuario\\Downloads\\'
E_DIR = 'E:\\Downloads\\processos\\'


LIM_ARQ = 2.3e7  # a cópia para o computador recusa arquivos acima de ~25 MB (22 MB passou, 31 MB falhou)


def gravar_dividido(dados, z, dest):
    """Grava o zip do processo. Acima de 23 MB, corta em volumes <dest>.001, .002... (o 7-Zip abre direto
    pelo .001; o Claude junta as partes quando precisar)."""
    if len(dados) <= LIM_ARQ:
        c = os.path.join(OUT, dest); open(c, 'wb').write(dados); return [c]
    saidas = []
    for i, k in enumerate(range(0, len(dados), int(LIM_ARQ)), 1):
        c = os.path.join(OUT, dest + '.%03d' % i); open(c, 'wb').write(dados[k:k + int(LIM_ARQ)]); saidas.append(c)
    return saidas


def preparar(lotes_js):
    lotes = json.loads(lotes_js)
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.dirname(FICHAS), exist_ok=True)
    open(MARCA, 'w', encoding='utf-8').write('Lote copiado para E:\\Downloads\\processos\\ (base INEMA Ecoplan).\n')
    grav, res = [], []
    for l in lotes:
        src = os.path.join(UP, l['nome'])
        r = {'lote': l['nome'], 'ok': [], 'bytes': 0, 'ruins': []}
        try:
            lz = zipfile.ZipFile(src)
        except Exception as ex:
            r['erro'] = 'lote ilegível: ' + str(ex)
            res.append(r)
            continue
        for info in lz.infolist():
            nome = info.filename
            try:
                dados = lz.read(info)
                z = zipfile.ZipFile(io.BytesIO(dados))
                if z.testzip() is not None:
                    raise ValueError('CRC')
                ficha, pasta = None, None
                for n in z.namelist():
                    if n.endswith('/processo.json'):
                        pasta = n.split('/')[0]
                        ficha = json.loads(z.read(n).decode('utf-8'))
                if not pasta:
                    pasta = z.namelist()[0].split('/')[0]
            except Exception as ex:
                r['ruins'].append(nome + ': ' + str(ex))
                continue
            parte = re.search(r'_parte\d+', nome)
            dest = pasta + (parte.group(0) if parte else '') + '.zip'
            for caminho in gravar_dividido(dados, z, dest):
                grav.append({'stagedPath': caminho, 'devicePath': E_DIR + pasta + '\\' + os.path.basename(caminho)})
            if ficha:
                docs = ficha.get('documentos', [])
                reg = {k: ficha.get(k) for k in ('processo', 'regiao', 'atos', 'baixado_em')}
                reg.update({'pasta_e': E_DIR + pasta, 'zip': dest, 'bytes': len(dados), 'n_docs': len(docs),
                            'n_erros': sum(1 for x in docs if x.get('erro')),
                            'documentos': [{k: x.get(k) for k in ('origem', 'descricao', 'arquivo', 'bytes', 'nome_local', 'erro')} for x in docs]})
                with open(FICHAS, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(reg, ensure_ascii=False) + '\n')
            r['ok'].append(nome)
            r['bytes'] += len(dados)
        grav.append({'stagedPath': MARCA, 'devicePath': C_DIR + l['nome']})
        res.append(r)
        try: os.remove(src)
        except OSError: pass
    # Ordem: 1) gravar no E: (até 50 arquivos por chamada, arquivos > 45 MB vão por SendUserFile);
    #        2) confirmar no navegador;  3) só então substituir os lotes no C: pelo marcador.
    normais = [g for g in grav if g['stagedPath'] != MARCA and os.path.getsize(g['stagedPath']) <= LIM_ARQ]
    grandes = [g for g in grav if g['stagedPath'] != MARCA and os.path.getsize(g['stagedPath']) > LIM_ARQ]
    marcadores = [g for g in grav if g['stagedPath'] == MARCA]
    chamadas = [normais[k:k + 50] for k in range(0, len(normais), 50)]
    json.dump({'e': chamadas, 'grandes': grandes, 'marcadores': marcadores}, open('/tmp/gravar.json', 'w'), ensure_ascii=False)
    print(json.dumps({'chamadas_e': len(chamadas), 'grandes': len(grandes), 'lotes': [{k: v for k, v in r.items() if k != 'ok'} | {'n_ok': len(r['ok'])} for r in res]}, ensure_ascii=False))
    json.dump(res, open('/tmp/lotes_res.json', 'w'), ensure_ascii=False)


def limpar():
    shutil.rmtree(OUT, ignore_errors=True)
    print('ok')


if __name__ == '__main__':
    {'preparar': lambda: preparar(sys.argv[2]), 'limpar': limpar}[sys.argv[1]]()
