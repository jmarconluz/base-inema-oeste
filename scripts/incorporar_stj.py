"""Incorpora os acórdãos do STJ exportados pelo coletor/coletor_stj.js (STJ.preparar + STJ.parte) ao acervo
juridico/jurisprudencia/stj/stj_acordaos_ambientais.json (sem duplicar: chave = id do espelho) e grava os temas
repetitivos ambientais em juridico/jurisprudencia/stj/temas_repetitivos_ambientais.csv.

Fonte: Portal de Dados Abertos do STJ (https://dadosabertos.web.stj.jus.br/), conjuntos "Espelhos de Acórdãos"
e "Precedentes Qualificados". O termo de uso pede que a fonte seja indicada.

Uso:
    python scripts/incorporar_stj.py /tmp/pacotes/stj.json
"""
import collections, csv, io, json, os, re, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'scripts'))
from privacidade import mascara  # noqa: E402

PASTA = os.path.join(RAIZ, 'juridico', 'jurisprudencia', 'stj')
ACERVO = os.path.join(PASTA, 'stj_acordaos_ambientais.json')
TEMAS = os.path.join(PASTA, 'temas_repetitivos_ambientais.csv')
LINK = 'https://processo.stj.jus.br/processo/pesquisa/?tipoPesquisa=tipoPesquisaNumeroRegistro&termo='


AMB_TEMA = re.compile(r'ambient|florest|ibama|icmbio|desmat|reserva legal|preserva[çc][ãa]o permanente|unidade de conserva|'
                      r'recursos h[íi]dricos|fauna|flora|polui|9\.605|6\.938|12\.651|9\.873|6\.514|4\.771|LEI:009605|'
                      r'LEI:006938|LEI:012651|LEI:009873|LEI:004771', re.I)


# Filtro final (o do navegador é largo): fica o acórdão com assunto ambiental claro, ou o que aplica a
# Lei 9.873/1999 (prescrição da ação punitiva federal), útil por analogia para multas do IBAMA.
FORTE = re.compile(r'ambient|florest|ibama|icmbio|desmat|supressao de vegeta|reserva legal|preservacao permanente|'
                   r'unidade de conserva|fauna|flora|polui|recursos hidricos|agua subterranea|ecolog|mata atlantica|'
                   r'queimada|incendio florestal|garimp|minera', re.I)


def sem_acento(t):
    import unicodedata
    return unicodedata.normalize('NFD', t or '').encode('ascii', 'ignore').decode().lower()


def classifica(d):
    t = sem_acento(' '.join([d.get('ementa') or '', d.get('tese') or '', d.get('termos') or '']))
    if FORTE.search(t):
        return d.get('motivo') if d.get('motivo') != 'norma_ba' else 'ementa'
    if any('LEI:009873' in n for n in d.get('normas') or []):
        return 'lei_9873_analogia'
    return None


def temas_ambientais(texto):
    linhas = list(csv.DictReader(io.StringIO(texto)))
    campos = ['questaoSubmetidaAJulgamento', 'teseFirmada', 'referenciaLegislativa', 'informacoesComplementares']
    sel = [r for r in linhas if AMB_TEMA.search(' '.join(r.get(c) or '' for c in campos))]
    with open(TEMAS, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()) if linhas else [])
        w.writeheader(); w.writerows(sel)
    print(f'temas: {len(linhas)} no CSV oficial, {len(sel)} com assunto ambiental -> {os.path.relpath(TEMAS, RAIZ)}')


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    os.makedirs(PASTA, exist_ok=True)
    atual = json.load(open(ACERVO, encoding='utf-8')) if os.path.exists(ACERVO) else []
    idx = {d['id']: d for d in atual}
    novos = descartados = 0
    for arq in sys.argv[1:]:
        pac = json.load(open(arq, encoding='utf-8'))
        for d in pac.get('acordaos', []):
            for k in ('ementa', 'tese', 'termos', 'info', 'jurisprudencia_citada'):
                d[k] = mascara(d.get(k) or '')
            d['link_processo'] = LINK + str(d.get('registro') or '')
            d['motivo'] = classifica(d)
            if not d['motivo']:
                descartados += 1
                idx.pop(d['id'], None)
                continue
            if d['id'] not in idx:
                novos += 1
            idx[d['id']] = d
        if pac.get('temas_csv'):
            temas_ambientais(pac['temas_csv'])
    final = sorted(idx.values(), key=lambda d: d.get('data_decisao') or '', reverse=True)
    json.dump(final, open(ACERVO, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    por_orgao = collections.Counter(d.get('orgao') for d in final)
    por_motivo = collections.Counter(d.get('motivo') for d in final)
    anos = collections.Counter((d.get('data_decisao') or '????')[:4] for d in final)
    print(f'acervo: {len(atual)} -> {len(final)} acórdãos ({novos} novos; {descartados} descartados por não serem ambientais)')
    print('por órgão:', dict(por_orgao))
    print('por motivo:', dict(por_motivo))
    print('por ano:', dict(sorted(anos.items())))


if __name__ == '__main__':
    main()
