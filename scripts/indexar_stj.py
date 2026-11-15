"""Gera juridico/jurisprudencia/stj/indice_temas.md: acórdãos do STJ do acervo agrupados por tema de defesa e os
temas repetitivos ambientais (tese firmada).

Classificação automática pelas palavras da ementa, da tese e das normas citadas: serve para achar rápido o que
ler; o resultado e o alcance de cada precedente têm de ser conferidos no inteiro teor antes de citar.

Uso: python scripts/indexar_stj.py
"""
import csv, json, os, re, unicodedata
from collections import defaultdict

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, 'juridico', 'jurisprudencia', 'stj')
ACERVO = os.path.join(PASTA, 'stj_acordaos_ambientais.json')
TEMAS = os.path.join(PASTA, 'temas_repetitivos_ambientais.csv')
MAX = 80


def sa(s):
    return unicodedata.normalize('NFD', s or '').encode('ascii', 'ignore').decode().lower()


TEMAS_DEFESA = [
    ('Prescrição (Lei 9.873/1999, intercorrente, Súmula 467)', r'prescri|lei:009873'),
    ('Autoria, culpa e responsabilidade administrativa subjetiva', r'responsabilidade administrativa|subjetiv|\bdolo\b|\bculpa\b|intranscend|transmiss|herdeir|sucessor|adquirente'),
    ('Nulidade do auto, notificação, defesa e motivação', r'nulidade|\bnul[oa]\b|cerceamento|ampla defesa|contraditorio|alegacoes finais|motivac|notificac|devido processo'),
    ('Competência para fiscalizar e autuar (LC 140/2011)', r'competencia (para|do|da|comum|fiscaliz|administrativa)|complementar (n[o. ]*)?140|lcp:000140|supletiv|orgao licenciador'),
    ('Advertência prévia, valor da multa e dosimetria', r'advertencia|art:00072|proporcional|razoabil|dosimetria|valor da multa|multa diaria|reducao d[ao] (multa|valor)|confisc'),
    ('Embargo, interdição e suspensão de atividade', r'embarg[oa] (de|da|do)|termo de embargo|interdic|suspensao (da|de) atividade|demolic'),
    ('Conversão de multa, TAC e termo de compromisso', r'conversao d[ae] multa|termo de ajustamento|termo de compromisso|servicos de preservacao'),
    ('Código Florestal: APP, Reserva Legal, área consolidada, PRA/CAR', r'reserva legal|preservacao permanente|area consolidada|regularizacao ambiental|lei:012651|lei:004771|cadastro ambiental rural|codigo florestal'),
    ('Execução fiscal de multa ambiental (CDA, dívida ativa)', r'execucao fiscal|\bcda\b|divida ativa|certidao de divida'),
    ('Outorga e recursos hídricos', r'outorga|recursos hidricos|agua subterranea|poco'),
    ('Responsabilidade civil e reparação do dano (contexto)', r'dano ambiental|reparacao|indeniza|responsabilidade civil|risco integral|propter rem'),
]


def data_br(d):
    d = d or ''
    return f'{d[6:8]}/{d[4:6]}/{d[:4]}' if len(d) == 8 else (d or 's/d')


def ementa_curta(d, n=320):
    e = re.sub(r'\s+', ' ', d.get('ementa') or '').strip().replace('|', '/')
    return e[:n] + ('…' if len(e) > n else '')


def main():
    dec = json.load(open(ACERVO, encoding='utf-8'))
    grupos = defaultdict(list)
    for d in dec:
        txt = sa(' '.join([d.get('ementa') or '', d.get('tese') or '', d.get('termos') or '', ' '.join(d.get('normas') or [])]))
        for nome, rx in TEMAS_DEFESA:
            if re.search(rx, txt):
                grupos[nome].append(d)
    datas = sorted(d['data_decisao'] for d in dec if d.get('data_decisao'))
    L = ['# STJ — acórdãos ambientais por tema de defesa', '',
         f'Fonte: Portal de Dados Abertos do STJ (espelhos de acórdãos da 1ª e 2ª Turmas, 1ª Seção e Corte Especial). '
         f'{len(dec)} acórdãos que citam a Lei 9.605/1998, o Decreto 6.514/2008 (ou o 3.179/1999), a Lei 9.873/1999, o '
         f'Código Florestal, a LC 140/2011 ou a Lei 6.938/1981, ou que tratam de sanção ambiental; julgados de '
         f'{data_br(datas[0])} a {data_br(datas[-1])}. Gerado por `scripts/indexar_stj.py`.', '',
         'Classificação automática: use para achar o que ler. **Antes de citar, confira a ementa completa no JSON e o '
         'inteiro teor** (link da consulta processual), quem venceu e se a tese se aplica ao caso.', '']
    if os.path.exists(TEMAS):
        tm = list(csv.DictReader(open(TEMAS, encoding='utf-8')))
        L += [f'## Temas repetitivos e precedentes qualificados com assunto ambiental — {len(tm)}', '',
              '| Tipo e nº | Situação | Tese firmada (início) |', '|---|---|---|']
        for r in sorted(tm, key=lambda r: int(re.sub(r'\D', '', r.get('numeroPrecedente') or '0') or 0), reverse=True):
            tese = re.sub(r'\s+', ' ', r.get('teseFirmada') or r.get('questaoSubmetidaAJulgamento') or '').replace('|', '/')
            L.append(f"| {r.get('tipoPrecedente', '')} {r.get('numeroPrecedente', '')} | {r.get('situacao', '')} | "
                     f"{tese[:400]}{'…' if len(tese) > 400 else ''} |")
        L.append('')
    for nome, _ in TEMAS_DEFESA:
        lst = sorted(grupos.get(nome, []), key=lambda d: d.get('data_decisao') or '', reverse=True)
        L += [f'## {nome} — {len(lst)} acórdãos', '']
        if not lst:
            L += ['(nenhum no acervo)', '']
            continue
        L += ['| Julgamento | Processo | Órgão | Relator | Ementa (início) |', '|---|---|---|---|---|']
        for d in lst[:MAX]:
            L.append(f"| {data_br(d.get('data_decisao'))} | [{d.get('classe')} {d.get('numero')}]({d.get('link_processo')}) | "
                     f"{(d.get('orgao') or '').title()} | {(d.get('relator') or '').title()} | {ementa_curta(d)} |")
        if len(lst) > MAX:
            L.append(f'| | | | | … e mais {len(lst) - MAX} no JSON |')
        L.append('')
    open(os.path.join(PASTA, 'indice_temas.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print({k[:30]: len(v) for k, v in grupos.items()})


if __name__ == '__main__':
    main()
