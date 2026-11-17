"""Extrai das pautas da Câmara Técnica Recursal do CEPRAM (PDFs do site da SEMA) os dados de cada processo:
número do auto, número SEI, tipo, valor, município, fato gerador, pedido do recorrente (pautas até 2023) e histórico (inclui o "Voto do Relator").

Fonte: https://www.ba.gov.br/meioambiente/404/pautas-da-camara-tecnica-recursal (PDFs públicos, com texto).
Os PDFs são baixados pelo navegador embutido (o ambiente de nuvem não alcança o site) e exportados em envelopes
(chave pdf_ct_*); depois de `python scripts/decodificar_partes.py`, grave os PDFs numa pasta e rode:

    python scripts/extrair_pautas_ct.py PASTA_DOS_PDFS [URLS.json]

Saída: multas/cepram_pautas/pautas_ct_recursal.json.gz (um registro por processo e por pauta) e
juridico/cepram_votos_relator.md (fato gerador e voto do relator das decisões favoráveis do CEPRAM).
O nome do interessado ("Int.:") NÃO é gravado (repositório público).
"""
import glob, gzip, json, os, re, sys
from collections import defaultdict

import pdfplumber

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from privacidade import mascara  # CPF, RG e CNH mascarados (repositório público)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = os.path.join(RAIZ, 'multas', 'cepram_pautas', 'pautas_ct_recursal.json.gz')
MD = os.path.join(RAIZ, 'juridico', 'cepram_votos_relator.md')
RE_AUTO = re.compile(r'(\d{4})\s*[-–]\s*(\d{6})\s*/\s*TEC\s*/\s*([A-Z]{4})\s*[-–]\s*(\d{4})')
RE_SEI = re.compile(r'046\.\d{4}\.\d{4}\.\d{7}-\d{2}')


def norm_auto(s):
    m = RE_AUTO.search(s or '')
    return f'{m.group(1)}-{m.group(2)}/TEC/{m.group(3)}-{m.group(4)}' if m else None


def linhas(pdf):
    """Devolve a sequência de (lado, texto) — lado 'E' (descritores) ou 'D' (histórico) — linha a linha."""
    corte = 440
    out = []
    for p in pdf.pages:
        w = p.extract_words(keep_blank_chars=False, use_text_flow=False)
        h = [x for x in w if x['text'].upper().startswith('HISTÓRICO') or x['text'].upper().startswith('HISTORICO')]
        if h:
            corte = h[0]['x0'] - 30
        por_linha = defaultdict(list)
        for x in w:
            por_linha[round(x['top'] / 3)].append(x)
        for k in sorted(por_linha):
            ws = sorted(por_linha[k], key=lambda x: x['x0'])
            e = ' '.join(x['text'] for x in ws if x['x0'] < corte)
            d = ' '.join(x['text'] for x in ws if x['x0'] >= corte)
            if e: out.append(('E', e))
            if d: out.append(('D', d))
    return out


def campo(txt, nome, prox):
    m = re.search(nome + r'\s*:?\s*(.*?)(?=' + prox + r'|$)', txt, re.S)
    return re.sub(r'\s+', ' ', m.group(1)).strip() if m else None


def extrair(caminho, url=None):
    pdf = pdfplumber.open(caminho)
    primeira = pdf.pages[0].extract_text() or ''
    m = re.search(r'(\d+)\s*[ªº°]\s*Reuni[ãa]o\s+(Ordin[áa]ria|Extraordin[áa]ria)', primeira, re.I)
    reuniao = (m.group(1) + 'ª ' + m.group(2).capitalize()) if m else os.path.basename(caminho)
    d = re.search(r'Data\s*:?\s*(\d{2})/(\d{2})/(\d{4}|\d{2})\b', primeira)  # pautas antigas: "Data: 22/11/19" ou "Data11/06/2021"
    data = f'{d.group(3) if len(d.group(3)) == 4 else "20" + d.group(3)}-{d.group(2)}-{d.group(1)}' if d else None
    blocos, atual = [], None
    for lado, t in linhas(pdf):
        if lado == 'E' and re.search(r'DESCRITORES', t):
            atual = {'E': [], 'D': []}; blocos.append(atual); continue
        if atual is not None:
            atual[lado].append(t)
    out = []
    for b in blocos:
        e = '\n'.join(b['E']); hist = re.sub(r'\s+', ' ', ' '.join(b['D'])).strip()
        auto = norm_auto(e)
        if not auto:
            continue
        sei = RE_SEI.search(e)
        rot = r'(?:Do\s+[Pp]edido|Conselheir[oa]\s+[Rr]elator[a]?|Int\.|Interessad[oa]|Tipo|Valor|Munic[íi]pio|Fato\s+Gerador|Relator(?:es)?(?:\s+Anterior(?:es)?|\s+Atual)?|\d+\.\s+[A-ZÁ-Ú]|Processo)\s*:'
        out.append({k: (mascara(v) if isinstance(v, str) else v) for k, v in {
            'reuniao': reuniao, 'data_reuniao': data, 'fonte': url or os.path.basename(caminho),
            'auto': auto, 'sei': sei.group(0) if sei else None,
            'tipo': campo(e, r'Tipo', rot), 'valor': campo(e, r'Valor', rot),
            'municipio': campo(e, r'Munic[íi]pio', rot),
            'fato_gerador': campo(e, r'Fato\s+Gerador', rot + r'|\n\s*\d+\.\d'),
            'pedido': campo(e, r'Do\s+[Pp]edido', rot),
            'historico': hist[:6000],
        }.items()})
    return out


def ultimo_voto(hist):
    """Último 'Voto do relator' do histórico (até 'Demais membros' ou o próximo evento)."""
    vs = list(re.finditer(r'Voto\s+(?:d[oa]\s+)?(?:relator|de\s+vistas?)[^:]{0,40}:\s*(.*?)(?=Demais\s+Membros|Reuni[ãa]o\s+(?:[Vv]irtual|Extraordin)|Voto\s+(?:d[oa]\s+)?relator|N[ãa]o\s+foi\s+analisado|Adiado|Pedido\s+de\s+vistas|$)', hist, re.I | re.S))
    vs = [v.group(1).strip(' .;') for v in vs if len(v.group(1).strip()) > 8]
    return vs[-1] if vs else None


def tema(fg):
    """Tipo de infração pelo fato gerador (classificação aproximada, só para o resumo)."""
    f = fg or ''
    if re.search(r'\bPAD\b|\(PARA\)|Adequa[çc][ãa]o e Regulariza[çc][ãa]o Ambiental', f): return 'Não apresentação do PAD (PARA — Dec. BA 12.071/2010)'
    f = f.lower()
    if re.search(r'licen', f) and re.search(r'sem |aus[êe]ncia|n[ãa]o poss|desacordo|vencida', f): return 'Operar sem licença / em desacordo'
    if 'condicionante' in f: return 'Descumprir condicionante'
    if re.search(r'notifica', f): return 'Não atender notificação'
    if re.search(r'desmat|supress|corte raso|\bfogo\b|queima', f): return 'Desmatamento / supressão / fogo'
    if re.search(r'preserva[çc][ãa]o permanente|\bapp\b', f): return 'APP'
    if re.search(r'\bdof\b|produtos? florest|carv[ãa]o|lenha', f): return 'DOF / produtos florestais'
    if re.search(r'outorga|po[çc]o|capta[çc]|barrag', f): return 'Recursos hídricos'
    return 'Outros'


def resumo_temas(b, por_auto):
    cont = defaultdict(lambda: defaultdict(int))
    for c in b['cepram']:
        res = c['resultado']
        if res not in ('Favorável', 'Favorável parcial', 'Desfavorável'):
            continue
        auto = norm_auto(c.get('processo'))
        if auto not in por_auto:
            continue
        r = max(por_auto[auto], key=lambda x: x['data_reuniao'] or '')
        cont[tema(r['fato_gerador'])]['fav' if res.startswith('Fav') else 'desf'] += 1
    L = ['## Resumo por tipo de infração (decisões do CEPRAM cujo auto aparece nas pautas coletadas)', '',
         '| Tipo de infração (pelo fato gerador da pauta) | Favoráveis | Desfavoráveis |', '|---|---|---|']
    for k, v in sorted(cont.items(), key=lambda kv: -(kv[1]['fav'] + kv[1]['desf'])):
        L.append(f"| {k} | {v['fav']} | {v['desf']} |")
    L.append('')
    return L


def gerar_md(regs):
    b = json.load(gzip.open(os.path.join(RAIZ, 'multas/bahia_doe/base_fiscalizacao_bahia.json.gz'), 'rt', encoding='utf-8'))
    fav = [c for c in b['cepram'] if c['resultado'].startswith('Favorável')]
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    por_auto = defaultdict(list)
    for r in regs:
        por_auto[r['auto']].append(r)
    L = ['# Fato gerador e voto do relator — decisões favoráveis do CEPRAM (pautas da CT Recursal)', '',
         'Gerado por `scripts/extrair_pautas_ct.py` a partir das pautas públicas da Câmara Técnica Recursal '
         '(https://www.ba.gov.br/meioambiente/404/pautas-da-camara-tecnica-recursal). Para cada decisão favorável de '
         '`precedentes_cepram.md`, mostra a pauta mais recente (até a data da resolução) em que o auto aparece. '
         'O "voto do relator" da pauta é o dispositivo proposto, às vezes com o motivo; o fundamento completo continua no '
         'processo (pedir cópia — `acesso_processos.md`). Nomes de interessados não são gravados. Extração automática do PDF em '
         'duas colunas: em algumas pautas o município ou o fato gerador saem com pedaços do histórico — conferir no PDF da pauta antes de citar.', '']
    achados = 0
    linhas_md = []
    for c in sorted(fav, key=lambda x: x['data_resolucao'] or x['data_publicacao'], reverse=True):
        auto = norm_auto(c.get('processo'))
        lim = c['data_resolucao'] or c['data_publicacao']
        cand = [r for r in por_auto.get(auto, []) if not r['data_reuniao'] or r['data_reuniao'] <= (lim or '9999')]
        if not cand:
            continue
        r = max(cand, key=lambda x: x['data_reuniao'] or '')
        achados += 1
        voto = ultimo_voto(r['historico'])
        linhas_md.append(f"### Res. {c['numero'] or '?'} ({lim}) — {auto} — {r['municipio'] or c.get('municipio') or ''}\n")
        linhas_md.append(f"- **Pauta:** {r['reuniao']} da CT Recursal ({r['data_reuniao']}) — {r['fonte']}")
        if r['sei']: linhas_md.append(f"- **Processo SEI:** {r['sei']}")
        if r['valor']: linhas_md.append(f"- **Valor do auto:** {r['valor']}")
        if r['fato_gerador']: linhas_md.append(f"- **Fato gerador:** {r['fato_gerador'][:900]}")
        if r.get('pedido'): linhas_md.append(f"- **Pedido do recorrente (pauta):** {r['pedido'][:600]}")
        if voto: linhas_md.append(f"- **Voto do relator na pauta** (pode ter mudado na sessão; vale o dispositivo publicado): {voto[:900]}")
        linhas_md.append('')
    L += resumo_temas(b, por_auto) + ['## Decisões favoráveis, uma a uma', '']
    L.insert(4, f'Decisões favoráveis com pauta localizada: **{achados} de {len(fav)}** (pautas coletadas: todas as publicadas na página da CT Recursal, da 12ª reunião, mar/2016, à 85ª, dez/2026; o PDF da 29ª, de 19/10/2018, só tem o cabeçalho, e a pauta da 74ª, de 02/09/2025, não está na página — só o registro de resultado).\n')
    open(MD, 'w', encoding='utf-8').write('\n'.join(L + [x for x in linhas_md]) + '\n')
    return achados, len(fav)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    pasta = sys.argv[1]
    urls = json.load(open(sys.argv[2], encoding='utf-8')) if len(sys.argv) > 2 else {}
    anteriores = []
    if os.path.exists(SAIDA):
        anteriores = json.load(gzip.open(SAIDA, 'rt', encoding='utf-8'))
    novos = []
    for f in sorted(glob.glob(os.path.join(pasta, '*.pdf'))):
        if 'Registro' in os.path.basename(f):
            continue
        try:
            rs = extrair(f, urls.get(os.path.basename(f)))
        except Exception as e:
            print('erro', f, e); continue
        print(f'{os.path.basename(f)}: {len(rs)} processos')
        novos += rs
    chave = lambda r: (r['fonte'], r['auto'])
    todos = {chave(r): r for r in anteriores}
    todos.update({chave(r): r for r in novos})
    regs = sorted(todos.values(), key=lambda r: (r['data_reuniao'] or '', r['auto']))
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    with gzip.open(SAIDA, 'wt', encoding='utf-8') as g:
        json.dump(regs, g, ensure_ascii=False)
    print(len(regs), 'registros em', os.path.relpath(SAIDA, RAIZ))
    print('decisões favoráveis com pauta: %d de %d' % gerar_md(regs))


if __name__ == '__main__':
    main()
