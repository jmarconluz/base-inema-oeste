"""Decretos estaduais de utilidade pública e interesse social (desapropriação, servidão administrativa, ocupação) – Bahia.

Fonte oficial: Legisla Bahia (Casa Civil), Pesquisa Avançada, Decretos Numerados (coletor/coletor_dup.js).
Entrada: pacote(s) do coletor já decodificados (lista de decretos). Acumula em
         dados/utilidade_publica/brutos/dup_ba.json.gz (chave: endereço do decreto).
Saída (dados/utilidade_publica/):
  decretos_utilidade_publica_ba.csv   um decreto por linha: data, número, finalidade, entidade, processo SEI, municípios,
                                      oeste, área, onde fica, para que serve, se cita imóvel rural, ementa e endereço oficial
  resumo.md                           números da base
Nenhum dado pessoal: os decretos dizem "pertencente a quem de direito". CSV com ';' e UTF-8 com BOM.

Uso: python scripts/processar_dup.py [pacote.json ...]     (sem pacote, só refaz as tabelas)
"""
import csv, gzip, json, os, re, sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from processar_multas import MUN_CANON, MUNS, OESTE_N, RAIZ, sem_acento  # noqa: E402

BASE = os.path.join(RAIZ, 'dados', 'utilidade_publica')
BRUTO = os.path.join(BASE, 'brutos', 'dup_ba.json.gz')
CAMPOS = ['data', 'numero', 'finalidade', 'entidade', 'processo_sei', 'municipios', 'oeste', 'area', 'onde', 'para_que',
          'rural', 'tem_coordenadas', 'ementa', 'link']

_MUN_ALT = '|'.join(sorted((re.escape(m) for m in MUNS), key=len, reverse=True))
# "no Município de X - Bahia", "nos Municípios de X, Y e Z - Bahia", "Município de X/BA"
TRECHO_MUN_RE = re.compile(r"Munic[íi]pios?\s+d[eo]s?\s+(.{2,300}?)(?:\s*[-–/,]\s*(?:Bahia|BA)\b|,\s*conforme|\.\s|\n|$)")
NOME_MUN_RE = re.compile(r"(?<![A-Za-zÀ-ú])(" + _MUN_ALT + r")(?![A-Za-zÀ-ú])")
AREA_RE = re.compile(r"(?:medindo|totalizando|com\s+(?:a\s+)?[áa]rea\s+(?:total\s+)?de|[áa]rea\s+de\s+terras?\s+de)\s+([\d.]+(?:,\d+)?)\s*(m²|m2|ha|hectares?)", re.I)
ONDE_RE = re.compile(r"situad[ao]s?\s+(.{3,260}?),?\s+no?s?\s+Munic[íi]pio", re.I | re.S)
PARA_RE = re.compile(r"destinam?-se\s+(?:à|às|ao|aos|a)\s*(.{5,400}?)(?:\.\s|\.\n|\.$|\n)", re.I | re.S)
SEI_RE = re.compile(r"Processo\s+(?:SEI\s+)?n[º°o]\s*([\d./-]{10,40})")
ENT_RE = re.compile(r"Processo\s+(?:SEI\s+)?n[º°o]\s*[\d./-]{10,40},?\s+d[ao]\s+(.{5,160}?)(?:,|\n)")
SIGLA_RE = re.compile(r"\s[-–]\s([A-Z]{3,10})\b")
RURAL_RE = re.compile(r"fazenda|zona rural|im[óo]vel rural|rodovia|\bBA[- ]\d{3}|\bBR[- ]\d{3}|barragem|adutora|linha de transmiss|"
                      r"ferrovia|povoado|localidades?\s+de|assentamento|estrada|aeroporto|aer[óo]dromo|parque e[óo]lico|usina", re.I)


def limpo(s):
    return re.sub(r'\s+', ' ', s or '').strip(' ,;.-')


def municipios(texto):
    """Municípios citados no art. 1º (o decreto sempre diz 'no Município de X - Bahia')."""
    achados = []
    for m in TRECHO_MUN_RE.finditer(texto):
        for n in NOME_MUN_RE.findall(m.group(1)):
            nome = MUN_CANON.get(sem_acento(n), n)
            if nome not in achados:
                achados.append(nome)
    return achados


def finalidade(ementa):
    e = sem_acento(ementa)
    if 'servidao' in e:
        return 'servidão administrativa'
    if 'interesse social' in e:
        return 'desapropriação por interesse social'
    if 'ocupacao' in e:
        return 'ocupação temporária'
    return 'desapropriação'


def linha(d):
    t = d.get('texto') or ''
    corpo = t.split('D E C R E T A', 1)[-1]
    muns = municipios(corpo) or municipios(t)
    a = AREA_RE.search(corpo)
    onde = ONDE_RE.search(corpo)
    para = PARA_RE.search(corpo)
    ent = ENT_RE.search(t)
    entidade = limpo(ent.group(1)) if ent else ''
    sig = SIGLA_RE.search(' ' + entidade)
    if not sig:
        sig = re.search(r"realizados?\s+pel[ao]\s+.{5,120}?\s[-–]\s([A-Z]{3,10})\b", corpo)
    sei = SEI_RE.search(t)
    return {
        'data': d.get('data', ''), 'numero': d.get('numero', ''), 'finalidade': finalidade(d.get('ementa', '')),
        'entidade': (sig.group(1) if sig else entidade)[:60], 'processo_sei': sei.group(1).rstrip('.,') if sei else '',
        'municipios': '; '.join(muns), 'oeste': any(sem_acento(m) in OESTE_N for m in muns),
        'area': f"{a.group(1)} {'m²' if a.group(2).lower().startswith('m') else 'ha'}" if a else '',
        'onde': limpo(onde.group(1))[:260] if onde else '', 'para_que': limpo(para.group(1))[:300] if para else '',
        'rural': bool(RURAL_RE.search(corpo[:2500])), 'tem_coordenadas': bool(re.search(r'coordenadas|v[ée]rtice|UTM|SIRGAS', t, re.I)),
        'ementa': limpo(d.get('ementa', ''))[:200], 'link': d.get('url', ''),
    }


def main():
    os.makedirs(os.path.dirname(BRUTO), exist_ok=True)
    acervo = {}
    if os.path.exists(BRUTO):
        acervo = {d['url']: d for d in json.load(gzip.open(BRUTO, 'rt', encoding='utf-8'))}
    antes = len(acervo)
    recebidos = 0
    for p in sys.argv[1:]:
        for d in json.load(open(p, encoding='utf-8')):
            if d.get('url'):
                recebidos += 1
                acervo[d['url']] = d
    regs = sorted(acervo.values(), key=lambda d: (d.get('data', ''), d.get('numero', '')), reverse=True)
    with gzip.open(BRUTO, 'wt', encoding='utf-8') as g:
        json.dump(regs, g, ensure_ascii=False)
    linhas = [linha(d) for d in regs]
    with open(os.path.join(BASE, 'decretos_utilidade_publica_ba.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS, delimiter=';')
        w.writeheader()
        w.writerows(linhas)
    oeste = [x for x in linhas if x['oeste']]
    L = ['# Decretos de utilidade pública e interesse social (Bahia) – desapropriação e servidão\n',
         'Fonte oficial: Legisla Bahia (Casa Civil), Decretos Numerados com a ementa "utilidade pública" '
         '(https://www.legislabahia.ba.gov.br/documentos?categoria%5B0%5D=2&ementa=utilidade+p%C3%BAblica). '
         'Coletor: `coletor/coletor_dup.js`. Só os decretos para desapropriação, servidão administrativa, interesse social '
         'ou ocupação; os que dão título de utilidade pública a entidades ficam de fora.\n']
    if linhas:
        L.append(f"Período: decretos de {min(x['data'] for x in linhas if x['data'])} a {max(x['data'] for x in linhas)}.\n")
    L.append(f'- Decretos: **{len(linhas)}** ({len(oeste)} com município do Oeste Baiano)')
    L.append(f"- Sem município identificado no texto: {sum(1 for x in linhas if not x['municipios'])}")
    L.append('\n## Por finalidade\n')
    for k, n in Counter(x['finalidade'] for x in linhas).most_common():
        L.append(f'- {k}: {n}')
    L.append('\n## Por entidade que desapropria\n')
    for k, n in Counter(x['entidade'] or '(não identificada)' for x in linhas).most_common(15):
        L.append(f'- {k}: {n}')
    L.append('\n## Municípios com mais decretos\n')
    for k, n in Counter(m for x in linhas for m in x['municipios'].split('; ') if m).most_common(20):
        L.append(f'- {k}: {n}')
    if oeste:
        L.append('\n## Oeste Baiano\n')
        L.append('| Data | Decreto | Município | Entidade | Para quê | Área |\n|---|---|---|---|---|---|')
        for x in oeste:
            L.append(f"| {x['data']} | [{x['numero']}]({x['link']}) | {x['municipios']} | {x['entidade']} | {x['para_que'][:110]} | {x['area']} |")
    L.append('\n## Observações\n')
    L.append('- Campos extraídos automaticamente do texto do decreto: conferir sempre no endereço oficial.')
    L.append('- O decreto declara a utilidade pública; a desapropriação depende de acordo ou de ação judicial (Decreto-Lei '
             '3.365/1941) e a declaração caduca em 5 anos se não for efetivada (art. 10).')
    L.append('- A área exata está nas coordenadas do anexo do decreto: o cruzamento com um imóvel se faz pelo anexo.')
    open(os.path.join(BASE, 'resumo.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    if recebidos:
        from processar_diarios import registrar_coleta
        registrar_coleta('utilidade_publica', decretos=len(linhas), oeste=len(oeste), de=min(x['data'] for x in linhas if x['data']),
                         ate=max(x['data'] for x in linhas))
    print(f'recebidos {recebidos}; acervo {antes} -> {len(regs)} decretos; Oeste: {len(oeste)}; '
          f"sem município: {sum(1 for x in linhas if not x['municipios'])}")


if __name__ == '__main__':
    main()
