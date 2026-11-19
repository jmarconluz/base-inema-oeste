"""Busca na BASE AMBIENTAL UNIFICADA (monte antes com scripts/montar_conglomerado.py).

Uso:
    python scripts/buscar.py "prescrição intercorrente" [--fonte stj,tema] [--n 10] [--completo]
    python scripts/buscar.py '"intimação por edital" alegações'      (aspas = expressão exata)
    python scripts/buscar.py 2019-012345/TEC/AIMU                   (número de processo: busca literal)
Fontes: lei, stf, stj, tema, tjba, cepram, tc, doe, guia.  Sem --fonte, busca em todas e mostra as melhores de cada uma.
"""
import os, re, sqlite3, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(RAIZ, 'base', 'conglomerado.sqlite')
FONTES = ['tema', 'stf', 'lei', 'stj', 'tjba', 'cepram', 'tc', 'guia', 'doe']


def consulta_fts(q):
    if re.search(r'\d{4}-\d{4,6}/|/TEC/|\d{7}-\d{2}\.\d{4}', q):        # número de processo
        return '"' + q.replace('"', '') + '"'
    if '"' in q or re.search(r'\b(AND|OR|NOT|NEAR)\b', q):
        return q
    termos = [t for t in re.findall(r'\w[\w.\-/]*', q, re.U) if len(t) > 1]
    return ' '.join(f'"{t}"' if re.search(r'[.\-/]', t) else t + '*' for t in termos)


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    fontes, n, completo = None, 6, False
    if '--fonte' in args:
        i = args.index('--fonte'); fontes = args[i + 1].split(','); del args[i:i + 2]
    if '--n' in args:
        i = args.index('--n'); n = int(args[i + 1]); del args[i:i + 2]
    if '--completo' in args:
        args.remove('--completo'); completo = True
    if not os.path.exists(DB):
        sys.exit('Base não montada: rode python scripts/montar_conglomerado.py')
    q = consulta_fts(' '.join(args))
    db = sqlite3.connect(DB)
    for f in (fontes or FONTES):
        rows = db.execute("""SELECT titulo, ref, link, data, snippet(docs, 2, '[', ']', ' … ', 40), texto
                             FROM docs WHERE docs MATCH ? AND fonte = ? ORDER BY bm25(docs, 0, 3, 1) LIMIT ?""",
                          (q, f, n)).fetchall()
        total = db.execute('SELECT count(*) FROM docs WHERE docs MATCH ? AND fonte = ?', (q, f)).fetchone()[0]
        if not rows:
            continue
        print(f'\n=== {f.upper()} — {total} resultado(s) ===')
        for tit, ref, link, data, trecho, texto in rows:
            print(f'- {tit}' + (f' [{data}]' if data else ''))
            print('  ' + (texto[:4000] if completo else trecho).replace('\n', ' '))
            if link:
                print('  ' + link)


if __name__ == '__main__':
    main()
