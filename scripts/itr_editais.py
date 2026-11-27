"""Editais de ITR dos diários municipais (intimação fiscal, termo de constatação e intimação, notificação de lançamento):
lê a tabela "Sujeito(s) Passivo(s)" das páginas escaneadas e, se pedido, compara os nomes com uma lista.

Entrada: imagens das páginas (PNG ou WebP), a página inteira ou só o meio dela, desenhadas no navegador com o pdf.js
(`page.render({..., intent: 'print'})`), como diz o ATUALIZACAO_ACERVO_LOCAL.md (seção 2); página que já vem com texto
entra como arquivo .txt, uma linha da página por linha.
Saída: só na tela. Nada é gravado: os nomes e os documentos lidos não se guardam (este repositório é público).

Uso:
  python scripts/itr_editais.py PAGINAS... [--lista LISTA.csv] [--col-nome nome] [--col-doc documento] [--mostrar]
    --lista     CSV com ';' dos nomes a procurar (na máquina da rotina: cadastro/gerado/clientes.csv da base privada)
    --mostrar   mostra o nome lido por inteiro (sem isso, só as iniciais)

Comparação:
  - pelo documento (CPF ou CNPJ), quando a lista tem;
  - pelo nome: "igual", ou "parcial" quando o primeiro nome é o mesmo e todas as palavras de um estão no outro
    (na lista "Fulano Sousa", no edital "Fulano José Souza"), com tolerância de uma letra nos sobrenomes (Sousa/Souza).
Ligação só pelo nome é indício: confirmar pelo CPF/CNPJ antes de tratar como certa.

Requer: tesseract com o idioma por, Pillow e numpy.
"""
import argparse, csv, os, re, subprocess, tempfile, unicodedata

import numpy as np
from PIL import Image, ImageOps

CPF_RE = re.compile(r'(?<!\d)\d{3}[.,]?\s?\d{3}[.,]?\s?\d{3}\s?[-–.]?\s?\d{2}(?!\d)')
CNPJ_RE = re.compile(r'(?<!\d)\d{2}[.,]?\s?\d{3}[.,]?\s?\d{3}\s?[/|1lI]\s?\d{4}\s?[-–.]?\s?\d{2}(?!\d)')
EDITAL_RE = re.compile(r'EDITAL\s+DE\s+(NOTIFICACAO\s+DE\s+LANCAMENTO|TERMO\s+DE\s+CONSTATACAO\s+E\s+INTIMACAO|INTIMACAO\s+FISCAL)'
                       r'\s+N\S{0,2}\s*(\d{3,6})\s*,?\s*DE\s+(\d{1,2})\s+DE\s+([A-Z]+)\s+DE\s+(\d{4})')
MESES = {'JANEIRO': 1, 'FEVEREIRO': 2, 'MARCO': 3, 'ABRIL': 4, 'MAIO': 5, 'JUNHO': 6, 'JULHO': 7, 'AGOSTO': 8, 'SETEMBRO': 9,
         'OUTUBRO': 10, 'NOVEMBRO': 11, 'DEZEMBRO': 12}
TITULO_RE = re.compile(r'SUJ\w{1,3}TO\W{0,4}S?\W{0,3}PASSIVO')
PARADAS = {'DE', 'DA', 'DO', 'DOS', 'DAS', 'E', 'LTDA', 'SA', 'S', 'A', 'ME', 'EPP', 'EIRELI', 'CIA'}


def sem_acento(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s or '') if unicodedata.category(c) != 'Mn').upper()


def ocr(img, psm=6):
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        img.save(f.name)
    try:
        return subprocess.run(['tesseract', f.name, '-', '-l', 'por', '--psm', str(psm)], capture_output=True, text=True).stdout
    finally:
        os.unlink(f.name)


def sem_grade(img):
    """Apaga as linhas da grade das tabelas, que atrapalham a leitura: fileiras com um traço escuro de mais de 40% da
    largura e traços verticais mais altos que o dobro de uma letra."""
    a = np.array(img.convert('L'))
    escuro = a < 140
    alt, larg = escuro.shape

    def corridas(b):  # tamanho do traço escuro que termina em cada ponto, ao longo das colunas de b
        c = np.zeros(b.shape, dtype=np.int32)
        acum = np.zeros(b.shape[0], dtype=np.int32)
        for x in range(b.shape[1]):
            acum = (acum + 1) * b[:, x]
            c[:, x] = acum
        return c

    for y in np.where(corridas(escuro).max(axis=1) > 0.4 * larg)[0]:
        a[max(0, y - 2):y + 3, :] = 255
    cv = corridas(escuro.T).T  # agora ao longo das linhas: traços verticais
    minimo = max(60, round(larg * 0.028))
    fim = (cv >= minimo) & np.vstack([~escuro[1:], np.ones((1, larg), dtype=bool)])
    for y, x in zip(*np.where(fim)):
        a[y - cv[y, x] + 1:y + 1, max(0, x - 2):x + 3] = 255
    return Image.fromarray(a)


def ler_pagina(caminho):
    """{'edital': (tipo, número, data) ou None, 'linhas': [{'nome', 'doc'}], 'tabela': achou a tabela?}
    Imagem (página escaneada) passa pela leitura ótica; arquivo .txt é a página que já veio com texto, uma linha por linha."""
    if caminho.lower().endswith('.txt'):
        linhas = [l.strip() for l in open(caminho, encoding='utf-8').read().splitlines() if l.strip()]
    else:
        img = Image.open(caminho).convert('L')
        escala = max(1, round(3000 / img.width))
        grande = ImageOps.autocontrast(img.resize((img.width * escala, img.height * escala), Image.LANCZOS))
        linhas = [l.strip() for l in ocr(sem_grade(grande)).splitlines() if l.strip()]
    m = EDITAL_RE.search(sem_acento(' '.join(linhas)))
    edital = None
    if m:
        mes = MESES.get(m.group(4))
        edital = (m.group(1).title(), m.group(2), f'{m.group(5)}-{mes:02d}-{int(m.group(3)):02d}' if mes else '')
    # A tabela fica entre o título "Sujeito(s) Passivo(s)" (ou a linha "Nome Completo / Razão Social | CPF/CNPJ") e o
    # quadro "Titular do Órgão...". Linha com CPF ou CNPJ é contribuinte em qualquer lugar: o texto do edital não traz outro.
    out, dentro, tabela = [], False, False
    for l in linhas:
        s = sem_acento(l)
        if (len(s) < 40 and TITULO_RE.search(s)) or re.search(r'NOME COMPLETO|RAZAO SOCIAL|CPF/?CNPJ', s):
            dentro = tabela = True
            continue
        if dentro and re.search(r'TITULAR DO|^NOME:|CARGO:|MATR.CULA:|ASSINATURA|AUDITOR', s):
            dentro = False  # acabou a tabela: daqui para baixo é o quadro de quem assina
            continue
        docs = [re.sub(r'\D', '', x.group(0)) for x in list(CNPJ_RE.finditer(l)) + list(CPF_RE.finditer(l))]
        docs = [d for d in docs if len(d) in (11, 14)]
        if not docs and not dentro:
            continue
        nome = re.split(r'\d{2,3}[.,]\s?\d{3}', l)[0]
        nome = re.sub(r'\s+', ' ', sem_acento(re.sub(r'[^A-Za-zÀ-ú ]', ' ', nome))).strip()
        if not docs and len([p for p in nome.split() if len(p) >= 3]) < 2:
            continue  # sujeira da leitura
        tabela = True
        linha = {'nome': nome, 'doc': docs[0] if docs else ''}
        if linha not in out:  # há PDF com a camada de texto em dobro
            out.append(linha)
    return {'edital': edital, 'linhas': out, 'tabela': tabela}


def palavras(nome):
    return [p for p in re.findall(r'[A-Z]{2,}', sem_acento(nome)) if p not in PARADAS]


def uma_letra(a, b):
    """Verdadeiro se as palavras diferem em no máximo uma letra (troca, falta ou sobra)."""
    if a == b:
        return True
    if min(len(a), len(b)) < 6 or abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) <= 1
    menor, maior = sorted((a, b), key=len)
    return any(menor == maior[:i] + maior[i + 1:] for i in range(len(maior)))


def dentro(menor, maior):
    return all(any(uma_letra(p, q) for q in maior) for p in menor)


def comparar(nome, doc, lista):
    """[(como, linha da lista)] – 'documento', 'nome igual' ou 'nome parcial'."""
    pl, achados = palavras(nome), []
    for item in lista:
        if doc and item['doc'] == doc:
            achados.append(('documento', item))
            continue
        pn = item['palavras']
        if len(pn) < 2 or len(pl) < 2 or pn[0] != pl[0]:
            continue
        if len(pn) == len(pl) and all(uma_letra(a, b) for a, b in zip(pn, pl)):
            achados.append(('nome igual', item))
        elif dentro(pn, pl) or dentro(pl, pn):
            achados.append(('nome parcial', item))
    return achados


def carregar_lista(caminho, col_nome, col_doc):
    lista = []
    for r in csv.DictReader(open(caminho, encoding='utf-8-sig'), delimiter=';'):
        nome = (r.get(col_nome) or '').strip()
        doc = re.sub(r'\D', '', r.get(col_doc) or '')
        if nome:
            lista.append({'nome': nome, 'id': r.get('id', ''), 'doc': doc if len(doc) in (11, 14) else '',
                          'palavras': palavras(nome)})
    return lista


def iniciais(nome):
    return ' '.join(p[0] + '*' * (len(p) - 1) for p in nome.split())


def main():
    ap = argparse.ArgumentParser(description='Lê os editais de ITR escaneados e compara com uma lista de nomes.')
    ap.add_argument('paginas', nargs='+')
    ap.add_argument('--lista')
    ap.add_argument('--col-nome', default='nome')
    ap.add_argument('--col-doc', default='documento')
    ap.add_argument('--mostrar', action='store_true')
    a = ap.parse_args()
    lista = carregar_lista(a.lista, a.col_nome, a.col_doc) if a.lista else []
    tot = {'paginas': 0, 'sem_tabela': 0, 'contribuintes': 0, 'com_documento': 0, 'documento': 0, 'nome igual': 0,
           'nome parcial': 0}
    ultimo = None
    for p in a.paginas:
        r = ler_pagina(p)
        tot['paginas'] += 1
        if r['edital']:
            ultimo = r['edital']
            rotulo = f"{os.path.basename(p)} | {ultimo[0]} nº {ultimo[1]} ({ultimo[2]})"
        else:  # segunda página do mesmo edital, ou página de outro ato
            rotulo = f"{os.path.basename(p)} | sem cabeçalho de edital" + (f' (o último lido foi o nº {ultimo[1]})' if ultimo else '')
        if not r['tabela']:
            tot['sem_tabela'] += 1
            print(f'{rotulo} | sem tabela de contribuintes nesta página')
            continue
        for l in r['linhas']:
            tot['contribuintes'] += 1
            tot['com_documento'] += bool(l['doc'])
            achados = comparar(l['nome'], l['doc'], lista)
            for como in {c for c, _ in achados}:
                tot[como] += 1
            tipo = {11: 'CPF', 14: 'CNPJ'}.get(len(l['doc']), 'sem documento lido')
            print(f"{rotulo} | {l['nome'] if a.mostrar else iniciais(l['nome'])} | {tipo}"
                  + ''.join(f" | NA LISTA ({c}): {i['nome']} [{i['id']}]" for c, i in achados))
    print(tot)


if __name__ == '__main__':
    main()
