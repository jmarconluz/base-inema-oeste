"""Gera juridico/jurisprudencia/tjba/indice_temas.md: as decisões do TJBA do acervo agrupadas por tema de defesa
(prescrição, nulidade, competência, autoria, embargo, dosimetria, conversão, execução fiscal, demora do órgão).

Classificação automática por palavras da ementa (ou dos trechos, se não houver ementa): serve para achar rápido as decisões a ler;
o resultado (favorável ou não, e a quem) tem de ser conferido no inteiro teor antes de citar.

Uso: python scripts/indexar_tjba.py
"""
import json, os, re, unicodedata
from collections import defaultdict

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, 'juridico', 'jurisprudencia', 'tjba')
ACERVO = os.path.join(PASTA, 'tjba_inema_multas.json')


def sa(s):
    return unicodedata.normalize('NFD', s or '').encode('ascii', 'ignore').decode().lower()


# fora do foco (ação de indenização, processo criminal), salvo se a ementa falar do auto ou da multa administrativa
EXCLUIR = re.compile(r'apelacao criminal|habeas corpus|trafico de drogas|danos morais|danos materiais|indenizat|pescador')
FOCO = re.compile(r'auto de infracao|multa (administrativa|ambiental)|infracao (administrativa|ambiental)|sancao administrativa')
SANCIONADOR = re.compile(r'multa|auto de infracao|infracao|sancao|penalidade|embargo|interdic|poder de policia|termo de compromisso|conversao|fiscalizac')
AMBIENTAL = re.compile(r'ambient|inema|ibama|\bsema\b|cepram|florest|desmat|supressao|outorga|licenc|recursos hidricos|fauna|flora|poluic|residuo|reserva legal|\bapp\b|preservacao permanente')
TEMAS = [
    ('Prescrição (Lei 12.209/2011, art. 109; Lei 9.873/1999; intercorrente)', re.compile(r'prescri')),
    ('Nulidade, notificação, ampla defesa e motivação', re.compile(r'nulidade|\bnul[oa]\b|cerceamento|ampla defesa|contraditorio|notificac|ausencia de motivac|falta de motivac')),
    ('Competência (LC 140/2011; Estado × Município × IBAMA)', re.compile(r'competencia (do|da|para|administrativa|fiscalizat|comum)|complementar (n[o.]* *)?140|lc 140|lei complementar 140')),
    ('Autoria e responsabilidade administrativa (subjetiva, intranscendência)', re.compile(r'responsabilidade administrativa|responsabilidade subjetiva|natureza subjetiva|intranscend|autoria|\bdolo\b|\bculpa\b')),
    ('Embargo e interdição', re.compile(r'embargo d[ae] (obra|atividade|area)|termo de embargo|\bembargad[oa]\b.*(area|obra|atividade)|interdic')),
    ('Valor da multa, proporcionalidade e advertência', re.compile(r'proporcional|razoabilidade|reducao d[ao] (multa|valor)|valor da multa|advertencia|dosimetria|confiscat')),
    ('Conversão de multa e termo de compromisso/ajustamento', re.compile(r'conversao d[ae] multa|termo de (ajustamento|compromisso)|\btac\b')),
    ('Execução fiscal, CDA e dívida ativa', re.compile(r'execucao fiscal|\bcda\b|certidao de divida|divida ativa')),
    ('Demora do órgão e mandado de segurança (prazo para decidir)', re.compile(r'razoavel duracao|demora (na|da|injustificada)|omissao (administrativa|do poder publico|da autoridade)|prazo para (decidir|analise|apreciacao)')),
]
MAX_POR_TEMA = 80


def ementa_curta(d):
    e = re.sub(r'\s+', ' ', d.get('ementa') or '').strip()
    m = re.search(r'\bE\s?M\s?E\s?N\s?T\s?A\b[:.\s-]*', e)
    if m:
        e = e[m.end():]
    elif d.get('trechos'):
        e = re.sub(r'\s+', ' ', d['trechos']).strip()
    else:
        e = re.sub(r'^.*?(?=(DIREITO|APELA[CÇ][AÃ]O|AGRAVO|MANDADO DE SEGURAN|REEXAME|RECURSO|EMBARGOS|A[CÇ][AÃ]O)\b)', '', e, count=1)
    e = e.replace('|', '/')
    return (e[:330] + '…') if len(e) > 330 else e


def main():
    dec = json.load(open(ACERVO, encoding='utf-8'))
    grupos = defaultdict(list); analogia = []
    for d in dec:
        # a ementa decide (os trechos do inteiro teor trazem muito ruído); sem ementa útil, usa os trechos
        em = d.get('ementa') or ''
        txt = sa(em if len(em) >= 200 else em + ' ' + (d.get('trechos') or ''))
        amb = bool(AMBIENTAL.search(txt)); sanc = bool(SANCIONADOR.search(txt))
        if EXCLUIR.search(txt) and not FOCO.search(txt):
            continue
        for nome, rx in TEMAS:
            if rx.search(txt):
                if amb and (sanc or nome.startswith('Demora')):
                    grupos[nome].append(d)
                elif nome.startswith('Prescrição'):
                    analogia.append(d)
    def linha(d):
        data = (d.get('data') or '')[:10] or 's/d'
        return (f"| {data} | [{d.get('processo') or '?'}]({d['link_inteiro_teor']}) | {d.get('classe') or ''} | "
                f"{(d.get('orgao') or '').title()} | {ementa_curta(d)} |")
    def ordem(d):
        return d.get('data') or ''
    n_amb = sum(1 for d in dec if AMBIENTAL.search(sa((d.get('ementa') or '') + ' ' + (d.get('trechos') or ''))))
    datas = sorted((d.get('data') or '')[:10] for d in dec if d.get('data'))
    L = ['# TJBA — decisões por tema de defesa', '',
         f'Gerado por `scripts/indexar_tjba.py` a partir de `tjba_inema_multas.json`: {len(dec)} decisões do 2º grau '
         f'(publicadas de {datas[0]} a {datas[-1]}; parte sem data no portal), {n_amb} com assunto ambiental. Nos temas '
         'abaixo entram só as decisões ambientais que tratam de multa, auto de infração, embargo, interdição ou outra '
         'sanção (no tema da demora do órgão, também as de licenciamento e outorga).', '',
         'Classificação automática pelas palavras da ementa: use para achar o que ler. **Antes de citar, abra o inteiro '
         'teor** (link) e confira quem venceu, o fundamento e se a decisão transitou ou foi reformada.', '']
    for nome, _ in TEMAS:
        lst = sorted(grupos.get(nome, []), key=ordem, reverse=True)
        L += [f'## {nome} — {len(lst)} decisões', '']
        if not lst:
            L += ['(nenhuma no acervo)', '']; continue
        L += ['| Publicação | Processo | Classe | Órgão | Ementa (início) |', '|---|---|---|---|---|']
        L += [linha(d) for d in lst[:MAX_POR_TEMA]]
        if len(lst) > MAX_POR_TEMA:
            L.append(f'| | | | | … e mais {len(lst) - MAX_POR_TEMA} no JSON |')
        L.append('')
    lst = sorted(analogia, key=ordem, reverse=True)
    L += [f'## Prescrição em outros processos sancionadores da Bahia (Lei 12.209/2011 — analogia) — {len(lst)} decisões', '',
          'Decisões sem assunto ambiental (PROCON, servidores, outros órgãos) que aplicam a Lei 12.209/2011 à prescrição. '
          'Úteis para mostrar como o TJBA conta os prazos da lei estadual de processo administrativo.', '',
          '| Publicação | Processo | Classe | Órgão | Ementa (início) |', '|---|---|---|---|---|']
    L += [linha(d) for d in lst[:MAX_POR_TEMA]]
    if len(lst) > MAX_POR_TEMA:
        L.append(f'| | | | | … e mais {len(lst) - MAX_POR_TEMA} no JSON |')
    open(os.path.join(PASTA, 'indice_temas.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('temas:', {k[:25]: len(v) for k, v in grupos.items()}, 'analogia:', len(analogia))


if __name__ == '__main__':
    main()
