"""Grava os CSVs de multas/ibama a partir dos pacotes exportados pelo coletor/coletor_ibama.js (PK.parte).

Os envelopes do IBAMA têm o formato antigo {"tipo": "pk", "nome", "i", "partes", "dados"}; este script junta as
partes por nome, decodifica (gzip + base64), mascara CPF e grava os quatro arquivos no mesmo formato de antes
(CSV com ';', UTF-8 com BOM, fim de linha CRLF; os .csv.gz com mtime fixo para não mudar à toa).

Uso:
    python scripts/ibama_csv.py arquivo1.txt arquivo2.txt ...   # resultados salvos do javascript_tool
"""
import base64, csv, gzip, io, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from decodificar_partes import ler_envelope

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, 'multas', 'ibama')


def gravar(nome, cab, linhas, gz):
    buf = io.StringIO(); w = csv.writer(buf, delimiter=';'); w.writerow(cab); w.writerows(linhas)
    dados = ('﻿' + buf.getvalue()).encode('utf-8')
    caminho = os.path.join(PASTA, nome)
    if gz:
        with gzip.GzipFile(caminho, 'wb', mtime=0) as f:
            f.write(dados)
    else:
        open(caminho, 'wb').write(dados)
    print(f'{nome}: {len(linhas)} linhas')


def mascarar(linhas, i):
    n = 0
    for l in linhas:
        v = l[i] if len(l) > i else ''
        if re.match(r'^\d{3}\.\d{3}\.\d{3}-\d{2}$', v or ''):
            l[i] = '***.***.***-**'; n += 1
        elif re.match(r'^\d{11}$', v or ''):
            l[i] = '***********'; n += 1
    return n


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    grupos, total = {}, {}
    for arq in sys.argv[1:]:
        env = ler_envelope(arq)
        if env and env.get('tipo') == 'pk':
            grupos.setdefault(env['nome'], {})[env['i']] = env['dados']; total[env['nome']] = env['partes']
    pac = {}
    for nome, partes in grupos.items():
        faltam = [i for i in range(total[nome]) if i not in partes]
        if faltam:
            sys.exit(f'{nome}: faltam as partes {faltam}')
        pac[nome] = json.loads(gzip.decompress(base64.b64decode(''.join(partes[i] for i in range(total[nome])))))
    if 'ibama_autos_ba' in pac:
        a = pac['ibama_autos_ba']; mascarar(a['linhas'], a['cab'].index('CPF_CNPJ_INFRATOR'))
        gravar('autos_infracao_ibama_BA.csv.gz', a['cab'], a['linhas'], True)
    if 'ibama_embargos_ba' in pac:
        e = pac['ibama_embargos_ba']; mascarar(e['linhas'], e['cab'].index('CPF_CNPJ_EMBARGADO'))
        gravar('termos_embargo_ibama_BA.csv.gz', e['cab'], e['linhas'], True)
    if 'ibama_agg' in pac:
        ag = pac['ibama_agg']['agg']
        gravar('autos_ibama_brasil_resumo.csv',
               ['uf', 'ano', 'status_formulario', 'sit_cancelado', 'tipo_infracao', 'qtd_autos', 'valor_total_rs'],
               [k.split('|') + [v[0], '%.2f' % v[1]] for k, v in sorted(ag.items())], False)
    if 'ibama_embargos_agg' in pac:
        eg = pac['ibama_embargos_agg']['agg']
        gravar('embargos_ibama_brasil_resumo.csv',
               ['uf', 'ano', 'status_formulario', 'sit_desembargo', 'qtd_termos', 'area_total_ha'],
               [k.split('|') + [v[0], '%.2f' % v[1]] for k, v in sorted(eg.items())], False)


if __name__ == '__main__':
    main()
