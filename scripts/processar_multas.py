"""Gera as tabelas da base de multas/fiscalização a partir das matérias coletadas no DOE-BA.

Entrada: multas/bahia_doe/brutos/doe_fiscalizacao_AAAA.json.gz (saída do coletor/coletor_multas.js, já enxuta)
Saída (multas/bahia_doe/):
  autos_editais.csv      um registro por autuado em cada edital (auto de infração, notificação, homologação)
  cepram_recursos.csv    decisões do CEPRAM (CT Recursal) sobre recursos contra autos de infração
  conversoes_tc.csv      termos de compromisso / conversão de multa / descontos
  outros_atos.csv        demais atos de fiscalização (decisões, cancelamentos, extratos)
  resumo.md              números da base
CPFs são mascarados. CSV com ';' e UTF-8 com BOM (abre direto no Excel).

Uso: python scripts/processar_multas.py
"""
import csv, glob, gzip, json, os, re, unicodedata
from collections import Counter, defaultdict

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(RAIZ, 'multas', 'bahia_doe')

OESTE = ['Barreiras', 'Luís Eduardo Magalhães', 'São Desidério', 'Formosa do Rio Preto', 'Riachão das Neves',
         'Correntina', 'Jaborandi', 'Cocos', 'Santa Maria da Vitória', 'Baianópolis', 'Angical', 'Cotegipe',
         'Wanderley', 'Cristópolis', 'Catolândia', 'Tabocas do Brejo Velho', 'Santana', 'Canápolis',
         'Serra Dourada', 'Coribe', 'São Félix do Coribe', 'Mansidão', 'Santa Rita de Cássia', 'Brejolândia',
         'Buritirama', 'Sítio do Mato', 'Serra do Ramalho', 'Muquém do São Francisco', 'Barra', 'Ibotirama']


def sem_acento(s):
    return unicodedata.normalize('NFD', s or '').encode('ascii', 'ignore').decode().lower().strip()


OESTE_N = {sem_acento(m) for m in OESTE} | {'luis eduardo magalhaes', 'muquem de sao francisco'}
MUNS = [m['nome'] for m in json.load(open(os.path.join(RAIZ, 'dados', 'municipios_bahia_ibge.json'), encoding='utf-8'))]
MUN_CANON = {sem_acento(m): m for m in MUNS}
MUN_CANON.update({'luis eduardo': 'Luís Eduardo Magalhães', 'lem': 'Luís Eduardo Magalhães', 'dias davila': "Dias d'Ávila",
                  'santa luz': 'Santaluz', 'camaca': 'Camacan', 'muquem de sao francisco': 'Muquém do São Francisco',
                  'xique xique': 'Xique-Xique', 'sao felix do coribe': 'São Félix do Coribe'})
# nomes que também são palavras comuns: só aceitos com contexto explícito (município de X, X/BA, X - BA)
AMBIGUOS = {sem_acento(x) for x in ['Central', 'Planalto', 'Glória', 'Saúde', 'Conde', 'Una', 'Barra', 'Santana', 'Prado', 'Cipó',
            'Laje', 'Mirante', 'Valente', 'Vereda', 'Bonito', 'Gavião', 'Antas', 'Jussara', 'Itapé', 'Fátima', 'Canudos',
            'Candeal', 'Cachoeira', 'Nazaré', 'Matina', 'Milagres', 'Malhada', 'Iuiu', 'Ichu', 'Lamarão', 'Utinga', 'Wagner',
            'Andorinha', 'Brejões', 'Encruzilhada', 'Esplanada', 'Firmino Alves', 'Mascote', 'Teolândia', 'Pintadas', 'Queimadas',
            'Remanso', 'Sobradinho', 'Rodelas', 'Tucano', 'Varzedo', 'Itagi', 'Gandu', 'Catu', 'Caém', 'Ipirá', 'Itaquara', 'Palmeiras',
            'Piatã', 'Ribeira do Amparo', 'São Domingos', 'São Gabriel', 'Santa Luzia', 'Santa Inês', 'Terra Nova', 'Belo Campo',
            'Boa Nova', 'Nova Fátima', 'Novo Horizonte', 'Ponto Novo', 'Riacho de Santana', 'Santo Amaro', 'São Félix', 'Pedrão']}
_MUN_ALT = '|'.join(sorted((re.escape(m) for m in MUNS), key=len, reverse=True))
MUN_CTX_RE = re.compile(r"(?:[Mm]unic[íi]pio\s+(?:de\s+|d[eo]\s+)?|zona\s+rural\s+(?:do\s+munic[íi]pio\s+)?d[eo]\s+|cidade\s+de\s+|distrito\s+de\s+[^,]{2,30},\s*)(" + _MUN_ALT + r")(?![A-Za-zÀ-ú])", re.I)
MUN_UF_RE = re.compile(r"(?<![A-Za-zÀ-ú])(" + _MUN_ALT + r")\s*(?:/|-|–)\s*(?:BA|Ba|Bahia)\b")
MUN_ANY_RE = re.compile(r"(?<![A-Za-zÀ-ú])(" + _MUN_ALT + r")(?![A-Za-zÀ-ú])")

TIPOS = {
    'AIMU': 'Multa', 'AIMD': 'Multa diária', 'AIAD': 'Advertência', 'AIAP': 'Apreensão', 'AIIN': 'Interdição',
    'AIIT': 'Interdição temporária', 'AIID': 'Interdição definitiva', 'AIEM': 'Embargo', 'AIDM': 'Demolição',
    'AISU': 'Suspensão', 'AIDE': 'Destruição/inutilização', 'NOT': 'Notificação', 'NOTC': 'Notificação',
    'NOTH': 'Notificação', 'FISC': 'Fiscalização', 'DEN': 'Denúncia', 'EMER': 'Emergência',
}

CPF_RE = re.compile(r'\b\d{3}\.\d{3}\.\d{3}\s*-\s*\d{2}\b|\b\d{3}\s?\d{3}\s?\d{3}\s?-\s?\d{2}\b')


def mascara(t):
    return CPF_RE.sub('***.***.***-**', t or '')


def normaliza(t):
    t = re.sub(r'\s+', ' ', t.replace(' ', ' '))
    t = re.sub(r'(\d{4})\s*[-–]\s*(\d{4,6})\s*/\s*TEC\s*/\s*([A-Z]{2,6})\s*[-–]\s*(\d{2,5})', r'\1-\2/TEC/\3-\4', t)
    t = re.sub(r'(\d{4})\s*[-–]\s*(\d{4,6})\s*/\s*([A-Z]{2,6})\s*[-–]\s*(\d{2,5})', r'\1-\2/TEC/\3-\4', t)
    t = re.sub(r'\*{3}\s*\.\s*\*{3}\s*\.\s*\*{3}\s*-\s*\*{2}', '***.***.***-**', t)
    t = re.sub(r'R\s*\$\s*([\d\.]+)\s*,\s*(\d{2})', r'R$ \1,\2', t)
    t = re.sub(r'(\d{3}\.\d{3}\.\d{3})\s*-\s*(\d{2})', r'\1-\2', t)
    t = re.sub(r'(\d{2}\.\d{3}\.\d{3})\s*/\s*(\d{4})\s*-\s*(\d{2})', r'\1/\2-\3', t)
    t = re.sub(r'(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})', r'\1/\2/\3', t)
    return t


PROC = r'\d{4}-\d{4,6}/(?:TEC/)?[A-Z]{2,6}-\d{2,5}'
PROC_RE = re.compile(PROC)
DOCPROC_RE = re.compile(
    r'(?P<tdoc>CPF|CNPJ)\s*(?:/MF)?\s*(?:sob\s+o\s+)?(?:n\s*[º°o]\.?|n\.)?\s*:?\s*(?P<doc>[\d\.\-/\s]{11,24}\d|\*{3}\.\*{3}\.\*{3}-\*{2})'
    r'\s*,?\s*(?:[^,]{0,90}?,\s*)?nos\s+autos\s+do\s+processo\s+administrativo\s*(?:de\s*)?(?:n\s*[º°o]\.?|n\.)?\s*'
    r'(?P<proc>' + PROC + ')', re.I)
NOME_RE = re.compile(r'(?:Autuad[oa]s?\s*:|Notificad[oa]s?\s*:|;|:|\bao\s+Autuado\b|\bà\s+|\bao\s+)\s*([^;:]{2,220}?)\s*,?\s*(?:inscrit[ao]\s+no\s*)?$', re.I)
CABEC_RE = re.compile(r'(?=EDITAL DE NOTIFICA[ÇC][ÃA]O|EDITAL DE CI[ÊE]NCIA|RESOLU[ÇC][ÃA]O\s+(?:CEPRAM\s+)?N\s*[º°o]|EXTRATO D[OE]|TERMO DE COMPROMISSO|PORTARIA\s+(?:INEMA\s+)?N\s*[º°o])')
MUN_RE = re.compile(r'[Mm]unic[íi]pio\s+de\s+([A-ZÀ-Ý][A-Za-zÀ-ú\'\- ]{2,45}?)(?=\s*(?:[,;.\)/]|\s-\s|\s+-?\s*BA\b|\s+Bahia|\s+e\s|\s+no\s|\s+na\s|\s+em\s|\s+onde|\s+conforme|\s+com\s|\s+sem\s|$))')


def num(s):
    if not s:
        return None
    try:
        return float(s.replace('.', '').replace(',', '.'))
    except ValueError:
        return None


def data_iso(s):
    m = re.match(r'(\d{1,2})[/\.](\d{1,2})[/\.](\d{4})', s or '')
    return f'{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}' if m else None


MESES = {'janeiro': 1, 'fevereiro': 2, 'marco': 3, 'abril': 4, 'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
         'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12}


def municipio(texto):
    t = texto or ''
    for rx in (MUN_CTX_RE, MUN_UF_RE):
        m = rx.search(t)
        if m:
            return MUN_CANON.get(sem_acento(m.group(1)), m.group(1))
    for m in MUN_ANY_RE.finditer(t):
        k = sem_acento(m.group(1))
        if k not in AMBIGUOS and k != 'salvador':
            return MUN_CANON.get(k, m.group(1))
    m = MUN_ANY_RE.search(t)
    if m and sem_acento(m.group(1)) == 'salvador':
        return 'Salvador'
    return None


def eh_oeste(mun):
    return bool(mun) and sem_acento(mun) in OESTE_N


def descricao(body):
    m = re.search(r'["“]\s*(.+?)\s*["”](?=\s*(?:\.|;|,|Oportunidade|E,|E\s|$))', body)
    if m:
        return m.group(1)
    m = re.search(r'["“]\s*(.+)', body)
    return m.group(1)[:1500] if m else None


def coordenadas(t):
    out = []
    for m in re.finditer(r'Lat(?:itude)?\.?\s*:?\s*(-?\s*\d{1,2}[\.,]\d{3,})\s*[°º]?\s*[SN]?\s*[,;e/]?\s*(?:e\s+)?Long(?:itude)?\.?\s*:?\s*(-?\s*0?\d{2}[\.,]\d{3,})', t, re.I):
        lat = float(m.group(1).replace(' ', '').replace(',', '.')); lon = float(m.group(2).replace(' ', '').replace(',', '.'))
        if lat > 0: lat = -lat
        if lon > 0: lon = -lon
        out.append(f'{lat:.6f},{lon:.6f}')
    for m in re.finditer(r'(\d{1,2})\s*[°º]\s*(\d{1,2})\s*[\'’′]\s*([\d,\.]+)\s*["”″]{1,2}\s*S[^0-9]{1,25}?(\d{2})\s*[°º]\s*(\d{1,2})\s*[\'’′]\s*([\d,\.]+)\s*["”″]{1,2}\s*[WO]', t):
        g = [float(x.replace(',', '.')) for x in m.groups()]
        out.append(f'{-(g[0] + g[1] / 60 + g[2] / 3600):.6f},{-(g[3] + g[4] / 60 + g[5] / 3600):.6f}')
    for m in re.finditer(r'\bS\s*-?\s*0?(\d{1,2}[\.,]\d{3,})\s*[°º]?\s*,?\s*e?\s*W\s*-?\s*0?(\d{2}[\.,]\d{3,})', t):
        out.append(f"{-float(m.group(1).replace(',', '.')):.6f},{-float(m.group(2).replace(',', '.')):.6f}")
    for m in re.finditer(r'(\d{1,2}[\.,]\d{3,})\s*[°º]?\s*S\b[^0-9]{0,30}?0?(\d{2}[\.,]\d{3,})\s*[°º]?\s*[WO]\b', t):
        out.append(f"{-float(m.group(1).replace(',', '.')):.6f},{-float(m.group(2).replace(',', '.')):.6f}")
    return '; '.join(dict.fromkeys(out)) or None


def parse_edital(ato, base, linhas):
    ms = list(DOCPROC_RE.finditer(ato))
    if not ms:
        return
    intro = ato[:ms[0].start()]
    edital_motivo = 'lugar incerto e não sabido' if re.search(r'incerto', ato[:1500], re.I) else None
    divida = bool(re.search(r'D[ÍI]VIDA\s+ATIVA', ato, re.I))
    ato_defesa = bool(re.search(r'apresentar\s+(?:a\s+)?(?:sua\s+)?Defesa|Defesa\s+Administrativa', ato, re.I))
    ato_recurso = bool(re.search(r'interpor\s+recurso|apresentar\s+recurso|Recurso\s+Administrativo|recurso\s+ao\s+CEPRAM', ato, re.I))
    ato_pagto = bool(re.search(r'pagamento|recolhimento', ato, re.I))
    fim_entrada = []
    for i, m in enumerate(ms):
        prox = ms[i + 1].start() if i + 1 < len(ms) else len(ato)
        fim_entrada.append(prox)
    ini_prev = 0
    for i, m in enumerate(ms):
        prefixo = ato[ini_prev:m.start()] if i == 0 else ato[ms[i - 1].end():m.start()]
        # o nome fica no fim do prefixo (depois do último ';' ou de 'Autuado:')
        nm = NOME_RE.search(prefixo[-260:])
        nome = nm.group(1).strip(' ,') if nm else prefixo[-120:].strip(' ,')
        nome = re.split(r'["”]\s*[.;,]?\s*(?:e\s+)?', nome)[-1]
        nome = re.split(r'\.\s+(?=[A-ZÀ-Ý]{2,}\s)', nome)[-1]
        nome = re.sub(r'^(?:o|a|ao|à|e)\s+', '', nome.strip(' ,.;'), flags=re.I)
        # corpo: do fim do nº do processo até o início do nome do próximo autuado
        corpo = ato[m.end():fim_entrada[i]]
        if i + 1 < len(ms):
            pn = NOME_RE.search(corpo[-260:])
            if pn:
                corpo = corpo[:len(corpo) - (len(corpo[-260:]) - pn.start())]
        proc = m.group('proc')
        sigla = re.search(r'/([A-Z]{2,6})-\d', proc).group(1)
        hom = re.search(r'em\s+(\d{1,2}/\d{1,2}/\d{4})\s*,?\s*foi\s+homologad[oa]', corpo, re.I)
        val = re.search(r'valor\s+(?:original\s+)?(?:de\s+)?R\$\s*([\d\.]+,\d{2})', corpo, re.I)
        atu = re.search(r'atualizad[oa]\s+(?:em|para)\s+R\$\s*([\d\.]+,\d{2})', corpo, re.I)
        desc = descricao(corpo)
        const = (re.search(r'(?:constatad[ao]|realizad[ao]|verificad[ao]|ocorrid[ao]|fiscaliza[çc][ãa]o)[^"”]{0,350}?(?:dia|em|data\s+de)\s+(\d{1,2}[/\.]\d{1,2}[/\.]\d{4})', corpo, re.I)
                 or re.search(r'(?:no\s+dia|na\s+data\s+de)\s+(\d{1,2}[/\.]\d{1,2}[/\.]\d{4})', desc or ''))
        area = re.search(r'([\d\.]*\d,\d+|\d+)\s*(?:ha\b|hectares)', desc or corpo)
        mun = municipio(desc or '') or municipio(corpo)
        if sigla.startswith('NOT'):
            fase = 'Notificação'
        elif divida:
            fase = 'Inscrição em dívida ativa (cobrança)'
        elif hom:
            fase = 'Homologação (decisão de 1ª instância)'
        elif re.search(r'apresentar\s+(?:a\s+)?Defesa', corpo, re.I) or (ato_defesa and not ato_recurso):
            fase = 'Lavratura (prazo de defesa)'
        elif re.search(r'recurso', corpo, re.I) or ato_recurso:
            fase = 'Decisão (prazo de recurso)'
        elif ato_pagto:
            fase = 'Cobrança/pagamento'
        else:
            fase = 'Outro'
        prazo = re.search(r'prazo\s+de\s+(\d+)\s*\([^)]*\)\s*dias\s+(?:úteis\s+)?para\s+([^,.;]{3,60})', corpo, re.I)
        ib_auto = re.search(r'Auto\s+de\s+Infra[çc][ãa]o\s*-?\s*n[º°o]?\s*(\d{5,7}\s*-?\s*[A-Z])\b', corpo)
        ib_proc = re.search(r'Processo\s+IBAMA\s*n?[º°o]?\s*([\d\.]{5,}/\d{4}-\d{2})', corpo)
        linhas.append(dict(
            base, ato_tipo='Edital de notificação', fase=fase, edital_motivo=edital_motivo,
            autuado=mascara(nome)[:200], tipo_doc=m.group('tdoc').upper(),
            documento=(re.sub(r'\s', '', m.group('doc')) if m.group('tdoc').upper() == 'CNPJ' else '***.***.***-**'),
            processo=proc, sigla=sigla, tipo_ato=TIPOS.get(sigla, sigla),
            data_homologacao=data_iso(hom.group(1)) if hom else None,
            valor_rs=num(val.group(1)) if val else None,
            valor_atualizado_rs=num(atu.group(1)) if atu else None,
            data_constatacao=data_iso(const.group(1)) if const else None,
            area_ha=num(area.group(1)) if area else None,
            municipio=mun, oeste=eh_oeste(mun),
            coordenadas=coordenadas(corpo),
            prazo=(prazo.group(1) + ' dias para ' + prazo.group(2).strip()) if prazo else None,
            auto_ibama=re.sub(r'\s', '', ib_auto.group(1)) if ib_auto else None,
            processo_ibama=ib_proc.group(1) if ib_proc else None,
            descricao=mascara(desc)[:3000] if desc else None,
            texto=mascara(corpo)[:4000],
        ))


DEC_RE = re.compile(r'Art\.?\s*1\s*[º°o]?\.?\s*[-–:]?\s*(Deferir\s+parcialmente|Deferir|Indeferir|N[ãa]o\s+conhecer|Conhecer|Dar\s+provimento|Negar\s+provimento|Arquivar|Declarar|Julgar|Acolher|Anular|Cancelar|Reduzir|Manter|Converter|Reconhecer)', re.I)


def classifica_decisao(verbo, art1):
    v = sem_acento(verbo or '')
    a = sem_acento(art1 or '')
    if v.startswith('deferir parcialmente') or 'parcialmente' in a[:200] or v.startswith('reduzir'):
        res = 'Favorável parcial'
    elif v.startswith(('deferir', 'dar provimento', 'anular', 'cancelar', 'acolher', 'reconhecer')):
        res = 'Favorável'
    elif v.startswith(('indeferir', 'negar', 'manter')):
        res = 'Desfavorável'
    elif v.startswith('nao conhecer'):
        res = 'Não conhecido'
    elif v.startswith('arquivar'):
        res = 'Arquivamento'
    elif v.startswith(('declarar', 'julgar', 'converter', 'conhecer')):
        res = 'Favorável' if re.search(r'nul|prescri|insubsist|improced|cancel|arquiv', a) else 'Outro'
    else:
        res = 'Outro'
    motivos = []
    for chave, rx in [('prescrição', r'prescri'), ('nulidade da notificação', r'notifica'), ('nulidade', r'nul'),
                      ('redução da multa', r'redu[cz]'), ('conversão em advertência', r'advert'),
                      ('conversão/termo de compromisso', r'convers|termo de compromisso'),
                      ('arquivamento', r'arquiv'), ('cancelamento', r'cancel'), ('intempestivo', r'intempest'),
                      ('ilegitimidade', r'ilegitim'), ('incompetência', r'incompet'),
                      ('falta de provas/laudo', r'prova|laudo'), ('bis in idem', r'bis in idem|duplicidade')]:
        if re.search(rx, a):
            motivos.append(chave)
    return res, ', '.join(dict.fromkeys(motivos))


def parse_resolucao(ato, base, linhas_cep, linhas_outros, linhas_conv):
    num_m = re.search(r'RESOLU[ÇC][ÃA]O\s+(?:CEPRAM\s+)?N\s*[º°o]\.?\s*([\d\.]+)', ato)
    dt = re.search(r'DE\s+(\d{1,2})\s+DE\s+([A-Za-zÇçÃã]+)\s+DE\s+(\d{4})', ato[:200], re.I)
    data_res = None
    if dt and sem_acento(dt.group(2)) in MESES:
        data_res = f'{dt.group(3)}-{MESES[sem_acento(dt.group(2))]:02d}-{int(dt.group(1)):02d}'
    procs = PROC_RE.findall(ato)
    a1 = re.search(r'Art\.?\s*1\s*[º°o]?\.?.*?(?=Art\.?\s*2\s*[º°o]?|$)', ato, re.S)
    art1 = a1.group(0) if a1 else ato[:1500]
    if re.search(r'convers[ãa]o\s+d[ae]\s+multa|desconto\s+de\s+\d+\s*%|Compromiss[áa]rio', ato, re.I):
        parse_conversao(ato, base, linhas_conv, 'Resolução')
        return
    if not re.search(r'recurso', ato, re.I) or not re.search(r'auto\s+de\s+infra', ato, re.I):
        if re.search(r'auto\s+de\s+infra', ato, re.I):
            linhas_outros.append(dict(base, ato_tipo='Resolução', numero=num_m.group(1) if num_m else None,
                                      processos='; '.join(dict.fromkeys(procs)), texto=mascara(ato)[:4000]))
        return
    dm = DEC_RE.search(art1)
    verbo = dm.group(1) if dm else None
    res, motivos = classifica_decisao(verbo, art1)
    aut = re.search(r'(?:desfavor\s+de|aplicada\s+(?:a|à|ao)|interposto\s+por|em\s+face\s+d[eao]|autuad[oa]\s*:?)\s+([^,;:]{3,160}?)\s*[,;:]?\s*(?:inscrit[ao]\s+no\s+)?(CPF|CNPJ)', art1, re.I)
    doc = re.search(r'(CPF|CNPJ)\s*(?:/MF)?\s*(?:sob\s+o\s+)?(?:n\s*[º°o]\.?)?\s*:?\s*([\d\.\-/]{11,20}\d)', art1, re.I)
    mun = None
    mm = re.search(r'CEP\s*:?\s*[\d\.\-]{8,11}\s*,?\s*([A-Za-zÀ-ú\' ]{3,40}?)\s*[-/]\s*BA\b', art1)
    if mm:
        mun = mm.group(1).strip()
    tipo_auto = re.search(r'Auto\s+de\s+Infra[çc][ãa]o\s+de\s+([A-Za-zÀ-ú ]{3,40}?)(?=\s+(?:emitido|lavrado|n[º°o]|aplicad|,)|,)', art1, re.I)
    sig = re.search(r'/([A-Z]{2,6})-\d', procs[0]).group(1) if procs else None
    linhas_cep.append(dict(
        base, numero=num_m.group(1) if num_m else None, data_resolucao=data_res,
        orgao='CEPRAM - CT Recursal' if re.search(r'C[ÂA]MARA\s+T[ÉE]CNICA\s+RECURSAL|CT\s+RECURSAL', ato, re.I) else 'CEPRAM',
        processo=procs[0] if procs else None, sigla=sig, tipo_ato=TIPOS.get(sig, (tipo_auto.group(1).strip() if tipo_auto else None)),
        decisao=verbo, resultado=res, motivos=motivos,
        autuado=mascara(aut.group(1).strip()) if aut else None,
        tipo_doc=doc.group(1).upper() if doc else None,
        documento=(doc.group(2) if doc and doc.group(1).upper() == 'CNPJ' else ('***.***.***-**' if doc else None)),
        municipio=mun, oeste=eh_oeste(mun),
        valor_rs=num((re.search(r'R\$\s*([\d\.]+,\d{2})', art1) or [None, None])[1]) if re.search(r'R\$\s*([\d\.]+,\d{2})', art1) else None,
        dispositivo=mascara(art1)[:3000],
    ))


def parse_conversao(ato, base, linhas_conv, tipo):
    procs = PROC_RE.findall(ato)
    comp = re.search(r'Compromiss[áa]ri[oa]\s*:?\s*([^.;:]{3,160}?)(?=\s*[.;]|\s+Interveniente|\s+Objeto|\s+CPF|\s+CNPJ)', ato, re.I)
    desc = re.search(r'desconto\s+de\s+(\d{1,2})\s*%', ato, re.I)
    vals = [num(v) for v in re.findall(r'R\$\s*([\d\.]+,\d{2})', ato)]
    obj = re.search(r'Objeto\s*:?\s*([^.]{5,400})', ato, re.I)
    linhas_conv.append(dict(
        base, ato_tipo=tipo, compromissario=mascara(comp.group(1).strip()) if comp else None,
        processos='; '.join(dict.fromkeys(procs)), desconto_pct=int(desc.group(1)) if desc else None,
        valores_rs='; '.join(f'{v:.2f}' for v in vals if v) or None,
        objeto=mascara(obj.group(1).strip())[:600] if obj else None,
        texto=mascara(ato)[:4000],
    ))


def main():
    arquivos = sorted(glob.glob(os.path.join(BASE, 'brutos', 'doe_fiscalizacao_*.json.gz')))
    editais, cep, conv, outros = [], [], [], []
    for arq in arquivos:
        for mat in json.load(gzip.open(arq, 'rt', encoding='utf-8')):
            t = normaliza(mat['texto'])
            base = dict(data_publicacao=mat['data'], materia_id=mat['mid'], edicao_id=mat['edicao_id'],
                        titulo_materia=mat['titulo'], link_doe=f"https://dool.egba.ba.gov.br/ver-html/{mat['edicao_id']}/#e:{mat['edicao_id']}")
            for ato in CABEC_RE.split(t):
                ato = ato.strip(' []')
                if len(ato) < 40:
                    continue
                if re.match(r'EDITAL', ato):
                    antes = len(editais)
                    parse_edital(ato, base, editais)
                    if len(editais) == antes and re.search(r'auto\s+de\s+infra', ato, re.I):
                        outros.append(dict(base, ato_tipo='Edital', processos='; '.join(dict.fromkeys(PROC_RE.findall(ato))), texto=mascara(ato)[:4000]))
                elif re.match(r'RESOLU', ato):
                    parse_resolucao(ato, base, cep, outros, conv)
                elif re.match(r'TERMO DE COMPROMISSO|EXTRATO', ato) and re.search(r'multa|auto\s+de\s+infra|convers', ato, re.I):
                    parse_conversao(ato, base, conv, 'Termo de compromisso/Extrato')
                elif re.search(r'auto\s+de\s+infra', ato, re.I) and re.search(r'nul|cancel|insubsist|arquiv|prescri|julg|decis', ato, re.I):
                    outros.append(dict(base, ato_tipo=ato[:30].split(' N')[0].title(), processos='; '.join(dict.fromkeys(PROC_RE.findall(ato))), texto=mascara(ato)[:4000]))
                elif DOCPROC_RE.search(ato):
                    parse_edital(ato, base, editais)

    def grava(nome, linhas, campos):
        with open(os.path.join(BASE, nome), 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=campos, delimiter=';', extrasaction='ignore')
            w.writeheader()
            for l in linhas:
                w.writerow({k: ('' if l.get(k) is None else l.get(k)) for k in campos})

    comuns = ['data_publicacao', 'link_doe', 'materia_id', 'edicao_id', 'titulo_materia']
    # remove duplicatas (mesmo processo republicado na mesma data)
    vistos = set(); ed2 = []
    for l in editais:
        k = (l['processo'], l['data_publicacao'], l['fase'])
        if k in vistos:
            continue
        vistos.add(k); ed2.append(l)
    editais = ed2
    grava('autos_editais.csv', editais, ['data_publicacao', 'fase', 'processo', 'sigla', 'tipo_ato', 'autuado', 'tipo_doc', 'documento',
                                         'valor_rs', 'valor_atualizado_rs', 'data_homologacao', 'data_constatacao', 'municipio', 'oeste', 'area_ha', 'coordenadas',
                                         'prazo', 'edital_motivo', 'auto_ibama', 'processo_ibama', 'descricao', 'texto'] + comuns[1:])
    grava('cepram_recursos.csv', cep, ['data_publicacao', 'numero', 'data_resolucao', 'orgao', 'processo', 'sigla', 'tipo_ato', 'resultado',
                                       'decisao', 'motivos', 'autuado', 'tipo_doc', 'documento', 'municipio', 'oeste', 'valor_rs', 'dispositivo'] + comuns[1:])
    grava('conversoes_tc.csv', conv, ['data_publicacao', 'ato_tipo', 'compromissario', 'processos', 'desconto_pct', 'valores_rs', 'objeto', 'texto'] + comuns[1:])
    grava('outros_atos.csv', outros, ['data_publicacao', 'ato_tipo', 'numero', 'processos', 'texto'] + comuns[1:])
    with gzip.open(os.path.join(BASE, 'base_fiscalizacao_bahia.json.gz'), 'wt', encoding='utf-8') as g:
        json.dump({'editais': editais, 'cepram': cep, 'conversoes': conv, 'outros': outros}, g, ensure_ascii=False)

    # resumo
    L = []
    L.append('# Base de fiscalização ambiental da Bahia (DOE-BA)\n')
    anos = sorted({l['data_publicacao'][:4] for l in editais + cep})
    L.append(f'Período: publicações de {min(l["data_publicacao"] for l in editais + cep)} a {max(l["data_publicacao"] for l in editais + cep)}.\n')
    L.append(f'- Registros de autuados em editais: **{len(editais)}** (processos distintos: {len({l["processo"] for l in editais})})')
    L.append(f'- Decisões do CEPRAM sobre recursos: **{len(cep)}**')
    L.append(f'- Termos de compromisso / conversões / descontos: **{len(conv)}**')
    L.append(f'- Outros atos de fiscalização: **{len(outros)}**\n')
    L.append('## Autuados em editais por tipo de ato e fase\n')
    L.append('| Tipo | Registros | Valor total (R$) |\n|---|---:|---:|')
    for tp, n in Counter(l['tipo_ato'] for l in editais).most_common():
        v = sum(l['valor_rs'] or 0 for l in editais if l['tipo_ato'] == tp)
        L.append(f'| {tp} | {n} | {v:,.2f} |'.replace(',', 'X').replace('.', ',').replace('X', '.'))
    L.append('\n| Fase | Registros |\n|---|---:|')
    for f, n in Counter(l['fase'] for l in editais).most_common():
        L.append(f'| {f} | {n} |')
    L.append('\n## Por ano de publicação\n')
    L.append('| Ano | Autuados em editais | Multas (AIMU) | Decisões CEPRAM | Favoráveis (total+parcial) |\n|---|---:|---:|---:|---:|')
    for a in anos:
        e = [l for l in editais if l['data_publicacao'].startswith(a)]
        c = [l for l in cep if l['data_publicacao'].startswith(a)]
        fav = sum(1 for l in c if l['resultado'].startswith('Favorável'))
        L.append(f'| {a} | {len(e)} | {sum(1 for l in e if l["sigla"] == "AIMU")} | {len(c)} | {fav} |')
    L.append('\n## Decisões do CEPRAM por resultado\n')
    L.append('| Resultado | Decisões |\n|---|---:|')
    for r, n in Counter(l['resultado'] for l in cep).most_common():
        L.append(f'| {r} | {n} |')
    L.append('\n### Motivos mais citados nas decisões favoráveis\n')
    mot = Counter()
    for l in cep:
        if l['resultado'].startswith('Favorável'):
            for x in (l['motivos'] or '').split(', '):
                if x:
                    mot[x] += 1
    L.append('| Motivo | Decisões |\n|---|---:|')
    for r, n in mot.most_common():
        L.append(f'| {r} | {n} |')
    oe = [l for l in editais if l['oeste']]
    L.append(f'\n## Oeste Baiano\n\n- Autuados em editais com município do Oeste identificado: **{len(oe)}**')
    for mun, n in Counter(l['municipio'] for l in oe).most_common(15):
        L.append(f'  - {mun}: {n}')
    L.append('\n## Municípios com mais autuados em editais (todos)\n')
    for mun, n in Counter(l['municipio'] for l in editais if l['municipio']).most_common(20):
        L.append(f'- {mun}: {n}')
    L.append('\n## Observações\n')
    L.append('- O DOE traz os editais (autuados não localizados pelo correio, art. 261, III, do Decreto 14.024/2012), as homologações, '
             'as decisões do CEPRAM e os termos de compromisso. Autos entregues pessoalmente ao autuado não aparecem no DOE.')
    L.append('- Campos extraídos automaticamente do texto; conferir sempre no `texto`/`dispositivo` e no `link_doe`.')
    L.append('- CPFs mascarados. CNPJs mantidos.')
    open(os.path.join(BASE, 'resumo.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('\n'.join(L[:12]))


if __name__ == '__main__':
    main()
