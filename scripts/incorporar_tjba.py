"""Incorpora decisões do TJBA exportadas pelo coletor/coletor_tjba.js (TJ.preparar + TJ.parte) ao acervo
juridico/jurisprudencia/tjba/tjba_inema_multas.json, sem duplicar (chave = hash da decisão).

Uso:
    python scripts/incorporar_tjba.py /tmp/pacotes/tjba.json [outro.json ...]
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from privacidade import mascara

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACERVO = os.path.join(RAIZ, 'juridico', 'jurisprudencia', 'tjba', 'tjba_inema_multas.json')
LINK = 'https://jurisprudenciaws.tjba.jus.br/inteiroTeor/'


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    atual = json.load(open(ACERVO, encoding='utf-8'))
    idx = {d['hash']: d for d in atual}
    novos = 0; termos_novos = 0
    for arq in sys.argv[1:]:
        for d in json.load(open(arq, encoding='utf-8')):
            d['link_inteiro_teor'] = LINK + d['hash']
            for k in ('ementa', 'trechos'):
                d[k] = mascara(d.get(k) or '')
            ant = idx.get(d['hash'])
            if ant is None:
                idx[d['hash']] = d; novos += 1
            else:
                for t in d.get('termos', []):
                    if t not in ant.setdefault('termos', []):
                        ant['termos'].append(t); termos_novos += 1
    final = sorted(idx.values(), key=lambda d: (d.get('data') or ''), reverse=True)
    json.dump(final, open(ACERVO, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    datas = sorted(d['data'][:10] for d in final if d.get('data'))
    print(f'acervo: {len(atual)} -> {len(final)} decisões ({novos} novas; {termos_novos} termos acrescentados); '
          f'publicação de {datas[0]} a {datas[-1]}')


if __name__ == '__main__':
    main()
