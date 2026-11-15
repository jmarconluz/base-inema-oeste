"""Incorpora matérias novas do DOE-BA (exportadas com MUL.p({desde: ...})) aos arquivos brutos por ano.

Uso:
    python scripts/incorporar_doe.py /tmp/pacotes/doe_enx_tudo_desde_2026-11-08.json [outro.json ...]
Depois rode:
    python scripts/processar_multas.py && python scripts/gerar_precedentes_cepram.py

- Mascara CPFs (mesma regra do processar_multas.py) antes de gravar: nada de CPF aberto no repositório.
- Não duplica: a chave é o id da matéria (mid); se a matéria já existe, o texto é substituído.
- Só regrava os anos que mudaram.
"""
import gzip, importlib.util, json, os, sys
from collections import defaultdict

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRUTOS = os.path.join(RAIZ, 'multas', 'bahia_doe', 'brutos')
spec = importlib.util.spec_from_file_location('pm', os.path.join(RAIZ, 'scripts', 'processar_multas.py'))
pm = importlib.util.module_from_spec(spec); spec.loader.exec_module(pm)

CAMPOS = ['mid', 'edicao_id', 'data', 'pasta', 'titulo', 'texto', 'chars_original']


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    novas = []
    for arq in sys.argv[1:]:
        novas += json.load(open(arq, encoding='utf-8'))
    por_ano = defaultdict(list)
    for m in novas:
        m = {k: m.get(k) for k in CAMPOS}
        m['mid'] = str(m['mid']); m['edicao_id'] = str(m['edicao_id'])
        m['texto'] = pm.mascara(m['texto']); m['titulo'] = pm.mascara(m['titulo'])
        por_ano[m['data'][:4]].append(m)
    resumo = []
    for ano, lista in sorted(por_ano.items()):
        caminho = os.path.join(BRUTOS, f'doe_fiscalizacao_{ano}.json.gz')
        atuais = json.load(gzip.open(caminho, 'rt', encoding='utf-8')) if os.path.exists(caminho) else []
        idx = {str(m['mid']): m for m in atuais}
        add = mud = 0
        for m in lista:
            ant = idx.get(m['mid'])
            if ant is None:
                add += 1; idx[m['mid']] = m
            elif ant.get('texto') != m['texto']:
                mud += 1; idx[m['mid']] = m
        if add or mud:
            final = sorted(idx.values(), key=lambda r: (r['data'], r['mid']))
            with gzip.GzipFile(caminho, 'wb', mtime=0) as g:
                g.write(json.dumps(final, ensure_ascii=False).encode('utf-8'))
        datas = sorted({m['data'] for m in lista})
        resumo.append(f'{ano}: {len(lista)} matérias recebidas ({datas[0]} a {datas[-1]}), {add} novas, {mud} atualizadas')
    print('\n'.join(resumo) if resumo else 'nenhuma matéria no pacote')


if __name__ == '__main__':
    main()
