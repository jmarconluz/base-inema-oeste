"""Monta a BASE AMBIENTAL UNIFICADA (conglomerado) num único arquivo SQLite com busca de texto (FTS5).

Junta, com a fonte de cada trecho:
  lei      — leis e decretos (federais e da Bahia), um registro por artigo        juridico/legislacao/
  stj      — acórdãos ambientais do STJ (dados abertos)                           juridico/jurisprudencia/stj/
  tema     — temas repetitivos e precedentes qualificados ambientais do STJ
  stf      — teses de repercussão geral (todas) e ações de controle concentrado ambientais  juridico/jurisprudencia/stf/
  tjba     — decisões do TJBA                                                      juridico/jurisprudencia/tjba/
  cepram   — decisões do CEPRAM sobre recursos (DOE-BA)                            multas/bahia_doe/cepram_recursos.csv
  tc       — termos de compromisso e conversões de multa (DOE-BA)                  multas/bahia_doe/conversoes_tc.csv
  doe      — autuados em editais do INEMA (DOE-BA)                                 multas/bahia_doe/autos_editais.csv
  guia     — teses, checklist, modelos, guia de acesso e precedentes (seções)      juridico/*.md e índices da jurisprudência

O arquivo gerado (base/conglomerado.sqlite) não vai para o repositório: refaça quando quiser (leva segundos).
Uso:  python scripts/montar_conglomerado.py      depois   python scripts/buscar.py "prescrição intercorrente"
"""
import csv, glob, json, os, re, sqlite3, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = os.path.join(RAIZ, 'base', 'conglomerado.sqlite')
csv.field_size_limit(10 ** 8)


def limpa(t):
    return re.sub(r'[ \t]+', ' ', re.sub(r'\n{3,}', '\n\n', t or '')).strip()


def artigos(texto):
    """Quebra o texto da norma em artigos (linha que começa com 'Art.')."""
    partes = re.split(r'\n(?=Art\.?\s*\d)', '\n' + texto)
    for p in partes:
        p = p.strip()
        if not p:
            continue
        m = re.match(r'Art\.?\s*(\d+[ºo°]?(?:-[A-Z])?)', p)
        yield (('art. ' + m.group(1)) if m else 'preâmbulo'), p


def secoes_md(texto):
    titulo = ''
    buf = []
    for linha in texto.split('\n'):
        if re.match(r'#{1,3} ', linha):
            if buf and ''.join(buf).strip():
                yield titulo, '\n'.join(buf).strip()
            titulo, buf = linha.lstrip('#').strip(), []
        else:
            buf.append(linha)
    if buf and ''.join(buf).strip():
        yield titulo, '\n'.join(buf).strip()


def main():
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    if os.path.exists(SAIDA):
        os.remove(SAIDA)
    db = sqlite3.connect(SAIDA)
    db.execute("""CREATE VIRTUAL TABLE docs USING fts5(fonte, titulo, texto, ref UNINDEXED, link UNINDEXED, data UNINDEXED,
                  tokenize='unicode61 remove_diacritics 2')""")
    cont = {}

    def add(fonte, titulo, texto, ref='', link='', data=''):
        db.execute('INSERT INTO docs VALUES (?,?,?,?,?,?)', (fonte, titulo, limpa(texto), ref, link, data))
        cont[fonte] = cont.get(fonte, 0) + 1

    # leis (por artigo)
    for f in sorted(glob.glob(os.path.join(RAIZ, 'juridico', 'legislacao', '*', '*.txt'))):
        if f.endswith('_paragrafos.txt'):
            continue
        s = open(f, encoding='utf-8').read()
        cab, _, corpo = s.partition('\n\n')
        url = (re.search(r'Fonte:\s*(\S+)', cab) or [None, ''])[1]
        nome = os.path.basename(f)[:-4]
        esfera = 'BA' if '/bahia/' in f.replace('\\', '/') else 'federal'
        for art, txt in artigos(corpo):
            add('lei', f'{nome} ({esfera}) — {art}', txt, ref=f'{nome} {art}', link=url)
    # STJ
    p = os.path.join(RAIZ, 'juridico', 'jurisprudencia', 'stj', 'stj_acordaos_ambientais.json')
    if os.path.exists(p):
        for d in json.load(open(p, encoding='utf-8')):
            add('stj', f"{d.get('classe')} {d.get('numero')} — {(d.get('orgao') or '').title()} — Rel. {(d.get('relator') or '').title()}",
                '\n'.join(x for x in [d.get('ementa'), d.get('tese'), d.get('termos'), ' | '.join(d.get('normas') or [])] if x),
                ref=f"STJ {d.get('classe')} {d.get('numero')}", link=d.get('link_processo', ''), data=d.get('data_decisao', ''))
    p = os.path.join(RAIZ, 'juridico', 'jurisprudencia', 'stj', 'temas_repetitivos_ambientais.csv')
    if os.path.exists(p):
        for r in csv.DictReader(open(p, encoding='utf-8')):
            add('tema', f"{r.get('tipoPrecedente')} {r.get('numeroPrecedente')} ({r.get('situacao')})",
                '\n'.join(x for x in [r.get('questaoSubmetidaAJulgamento'), 'TESE: ' + (r.get('teseFirmada') or ''),
                                      r.get('referenciaLegislativa')] if x),
                ref=f"STJ {r.get('tipoPrecedente')} {r.get('numeroPrecedente')}", data=r.get('dataJulgamento', ''))
    # STF (repercussão geral e controle concentrado)
    p = os.path.join(RAIZ, 'juridico', 'jurisprudencia', 'stf', 'teses_repercussao_geral.json')
    if os.path.exists(p):
        for r in json.load(open(p, encoding='utf-8'))['teses']:
            add('stf', f"STF Tema {r['tema']} ({r['repercussao']}) — {r['paradigma']}", 'TESE: ' + r['tese'],
                ref=f"STF Tema {r['tema']}", link=r['link'], data=r['data_tese'])
    p = os.path.join(RAIZ, 'juridico', 'jurisprudencia', 'stf', 'stf_temas_e_controle.json')
    if os.path.exists(p):
        d = json.load(open(p, encoding='utf-8'))
        for t in d['temas']:
            add('stf', f"STF Tema {t['tema']} — página do tema (situação)", t['texto'], ref=f"STF Tema {t['tema']}", link=t['url'])
        for c in d['controle_concentrado']:
            for bloco in re.split(r'\n (?=\d\d/\d\d/\d{4}\n)', c['decisoes']):
                if 'Decisão' in bloco:
                    add('stf', f"{c['classe']} {c['numero']} — decisão", bloco.strip(), ref=f"STF {c['classe']} {c['numero']}",
                        link=c['url'], data=bloco.strip()[:10])
    # TJBA
    p = os.path.join(RAIZ, 'juridico', 'jurisprudencia', 'tjba', 'tjba_inema_multas.json')
    if os.path.exists(p):
        for d in json.load(open(p, encoding='utf-8')):
            add('tjba', f"{d.get('classe') or ''} {d.get('processo')} — {(d.get('orgao') or '').title()}",
                (d.get('ementa') or '') + '\n' + (d.get('trechos') or ''), ref=f"TJBA {d.get('processo')}",
                link=d.get('link_inteiro_teor', ''), data=(d.get('data') or '')[:10])
    # CEPRAM, termos de compromisso, editais (DOE-BA)
    pasta = os.path.join(RAIZ, 'multas', 'bahia_doe')
    p = os.path.join(pasta, 'cepram_recursos.csv')
    if os.path.exists(p):
        for r in csv.DictReader(open(p, encoding='utf-8-sig'), delimiter=';'):
            add('cepram', f"Res. CEPRAM {r.get('numero')} — {r.get('resultado')} — {r.get('municipio') or ''}",
                '\n'.join(x for x in [r.get('decisao'), r.get('motivos'), r.get('dispositivo')] if x),
                ref=f"Res. CEPRAM {r.get('numero')} (proc. {r.get('processo')})", link=r.get('link_doe', ''),
                data=r.get('data_publicacao', ''))
    p = os.path.join(pasta, 'conversoes_tc.csv')
    if os.path.exists(p):
        for r in csv.DictReader(open(p, encoding='utf-8-sig'), delimiter=';'):
            add('tc', f"{r.get('ato_tipo')} — desconto {r.get('desconto_pct') or '?'}%", (r.get('objeto') or '') + '\n' + (r.get('texto') or '')[:3000],
                ref=f"DOE {r.get('data_publicacao')} ({r.get('processos')})", link=r.get('link_doe', ''), data=r.get('data_publicacao', ''))
    p = os.path.join(pasta, 'autos_editais.csv')
    if os.path.exists(p):
        for r in csv.DictReader(open(p, encoding='utf-8-sig'), delimiter=';'):
            add('doe', f"{r.get('processo')} — {r.get('tipo_ato')} — {r.get('fase')} — {r.get('municipio') or ''}",
                '\n'.join(x for x in [r.get('autuado'), r.get('descricao'), r.get('edital_motivo')] if x),
                ref=f"{r.get('processo')}", link=r.get('link_doe', ''), data=r.get('data_publicacao', ''))
    # guias e teses (por seção)
    for f in sorted(glob.glob(os.path.join(RAIZ, 'juridico', '*.md')) + glob.glob(os.path.join(RAIZ, 'juridico', 'legislacao', '*.md')) + glob.glob(os.path.join(RAIZ, 'juridico', 'jurisprudencia', '*', 'indice_temas.md'))):
        nome = os.path.relpath(f, RAIZ)
        for tit, txt in secoes_md(open(f, encoding='utf-8').read()):
            add('guia', f'{nome} — {tit}', txt, ref=nome)
    db.commit()
    db.execute("INSERT INTO docs(docs) VALUES('optimize')")
    db.commit()
    tam = os.path.getsize(SAIDA) / 1e6
    print(f'{os.path.relpath(SAIDA, RAIZ)}: {sum(cont.values())} trechos ({tam:.0f} MB)', cont)


if __name__ == '__main__':
    main()
