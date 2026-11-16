"""Gera juridico/precedentes_cepram.md a partir de multas/bahia_doe/base_fiscalizacao_bahia.json.gz:
lista as decisões favoráveis do CEPRAM (CT Recursal) por motivo, sem nomes de pessoas físicas."""
import gzip, json, os, re
from collections import defaultdict
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
b = json.load(gzip.open(os.path.join(RAIZ, 'multas/bahia_doe/base_fiscalizacao_bahia.json.gz'), 'rt', encoding='utf-8'))
cep = [c for c in b['cepram'] if c['resultado'].startswith('Favorável')]
def categoria(c):
    d = re.sub(r'\s+', ' ', c['dispositivo']).lower()
    if 'prescri' in d: return '1. Prescrição'
    if 'notifica' in d: return '2. Nulidade da notificação (reabre a defesa)'
    if 'advert' in d and 'convert' in d: return '3. Multa convertida em advertência'
    if re.search(r'redu', d): return '4. Redução da multa'
    if 'arquiv' in d: return '5. Arquivamento (perda do objeto)'
    if re.search(r'anul|cancel|nul', d): return '6. Penalidade anulada/cancelada'
    return '7. Outros favoráveis'
grupos = defaultdict(list)
for c in cep: grupos[categoria(c)].append(c)
def resumo(c):
    d = re.sub(r'\s+', ' ', c['dispositivo'])
    m = re.search(r'Art\.?\s*1\s*[º°o]?\s*[-–]?\s*(.*?)(?:Art\.?\s*2|$)', d)
    s = m.group(1) if m else d
    s = re.sub(r'(?:em desfavor d[aeo]|aplicada [àa]o?|imposto pelo .*? (?:a|ao|à)|em face d[aeo]|instaurado em face d[aeo])\s+[^,;]+', '[autuado]', s)
    s = re.sub(r'(?:CPF|CNPJ)\s*(?:n[º°o])?\s*:?\s*[\d\*\.\-/]+', '', s)
    s = re.sub(r'Endere[çc]o\s*:?[^;]*?(?=,\s*(?:anulando|convertendo|reduzindo|reconhecendo|com|promovendo|determinando)|\.|$)', '', s)
    s = re.sub(r'[,;]?\s*;?\s*\.?\s*(?:CEP\s*:?\s*)?[\d\.]*\d{3}-\d{3}\s*,?\s*[A-Za-zÀ-ú\' ]{2,40}\s*-\s*BA\.?', '', s)
    s = re.sub(r'\s*,\s*;\s*', ', ', s)
    return re.sub(r'\s{2,}', ' ', s).strip()[:420]
L = ['# Precedentes favoráveis do CEPRAM (Câmara Técnica Recursal)', '',
     f'Gerado de `multas/bahia_doe` (DOE-BA, 2016–2026): {len(cep)} decisões favoráveis ao autuado de {len(b["cepram"])} decisões sobre recursos.',
     'A resolução publicada traz só o dispositivo; o fundamento (voto do relator) está no processo — pedir cópia (ver `acesso_processos.md`).',
     'Fato gerador, pedido do recorrente e voto do relator tirados das pautas da CT Recursal: `cepram_votos_relator.md` '
     '(inclui o resumo por tipo de infração — ex.: autos por não apresentação do PAD/PARA quase sempre anulados desde 2023).', '']
for g in sorted(grupos):
    L.append(f'## {g} ({len(grupos[g])})\n')
    L.append('| Resolução | Data | Processo | Município | Dispositivo (resumo) |\n|---|---|---|---|---|')
    for c in sorted(grupos[g], key=lambda x: x['data_publicacao'], reverse=True):
        L.append(f"| {c['numero'] or ''} | {c['data_resolucao'] or c['data_publicacao']} | {c['processo'] or ''} | {c['municipio'] or ''} | {resumo(c).replace('|', '/')} |")
    L.append('')
open(os.path.join(RAIZ, 'juridico/precedentes_cepram.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print({g: len(v) for g, v in sorted(grupos.items())})
