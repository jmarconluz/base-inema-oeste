"""Atos dos diários oficiais municipais do Oeste da Bahia, por tema (coletor/coletor_diarios.js).

Fontes oficiais: o Diário Oficial de cada prefeitura, pela busca pública da plataforma que ela usa (DOEM/IBDM e Diário
Mtransparente). Busca por tema, nunca por nome de pessoa.
Entrada: pacote(s) do coletor já decodificados (diarios_doem.json, diarios_mtransparente.json). Acumula em
         dados/diarios_municipais/brutos/diarios_oeste.json.gz (chave: município + endereço + título).
Saída (dados/diarios_municipais/):
  atos_municipais_oeste.csv   um ato por linha: município, data, plataforma, edição, caderno, título, temas, relevância,
                              termos que o acharam e endereço oficial
  resumo.md                   números da base
Relevância: "alta" quando o próprio título trata do tema (ex.: "Decreto 158/2026 – Declaração de utilidade pública");
"média" quando só o texto da edição cita o termo e o ato é normativo (lei, decreto, edital, licença): abrir o PDF;
licitações, contratos e atos de pessoal ficam só no bruto. CSV com ';' e UTF-8 com BOM.

Uso: python scripts/processar_diarios.py [pacote.json ...]     (sem pacote, só refaz as tabelas)
"""
import csv, gzip, json, os, re, sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from processar_multas import RAIZ, sem_acento  # noqa: E402

BASE = os.path.join(RAIZ, 'dados', 'diarios_municipais')
BRUTO = os.path.join(BASE, 'brutos', 'diarios_oeste.json.gz')
CAMPOS = ['municipio', 'data', 'plataforma', 'edicao', 'caderno', 'titulo', 'temas', 'relevancia', 'termos', 'link']

TEMAS = [  # (tema, padrão no título sem acento)
    ('desapropriação e utilidade pública', r'desapropria|utilidade publica|servidao administrativa|interesse social|imissao'),
    ('urbanismo e uso do solo', r'plano diretor|perimetro urbano|zoneamento|uso e ocupacao|parcelamento do solo|loteamento|'
                                r'expansao urbana|desmembramento|remembramento|codigo de obras|distrito industrial'),
    ('tributos sobre imóveis', r'\biptu\b|\bitbi\b|codigo tributario|planta generica|valor venal|contribuicao de melhoria'),
    ('ambiental municipal', r'licenca ambiental|licenca de operacao|licenca previa|licenca de instalacao|licenca simplificada|'
                            r'licenca unificada|meio ambiente|ambiental|supressao de vegetacao|comdema|codema|condema'),
    ('participação e planejamento', r'audiencia publica|consulta publica|conferencia municipal'),
    ('infraestrutura', r'estradas? vicina(?:l|is)|\bpavimentacao\b|\brodovias?\b|\bpontes?\b|eletrificacao rural|\baeroporto\b|'
                       r'\bbarragem\b|\badutora\b|\bferrovia\b|linha de transmissao'),
]
TEMAS_RE = [(t, re.compile(p)) for t, p in TEMAS]
TEMA_DO_TERMO = {'desapropriacao': 0, 'utilidade publica': 0, 'servidao administrativa': 0, 'plano diretor': 1,
                 'perimetro urbano': 1, 'zoneamento': 1, 'uso e ocupacao do solo': 1, 'parcelamento do solo': 1, 'loteamento': 1,
                 'expansao urbana': 1, 'iptu': 2, 'itbi': 2, 'codigo tributario': 2, 'planta generica de valores': 2,
                 'licenca ambiental': 3, 'codigo de meio ambiente': 3, 'auto de infracao ambiental': 3,
                 'supressao de vegetacao': 3, 'conselho municipal de meio ambiente': 3, 'audiencia publica': 4,
                 'estrada vicinal': 5}
NORMATIVO = re.compile(r'^(lei|decreto|portaria|resolucao|edital|notifica|licenca|instrucao|audiencia|aviso|ato|extrato|outros|'
                       r'deliberac|parecer|termo|comunicad|errata|oficio|projeto de lei)')
FORA = re.compile(r'pregao|dispensa|inexigibilidade|contrat|licitac|ata de registro|adjudica|homologa|concorrencia|convite|'
                  r'concurso|processo seletivo|pessoal|balanc|orcament|receita|despesa|relatorio|credenciamento|chamad|'
                  r'chamamento|tomada de preco|leilao|compras|registro de preco|apostilamento|distrato|convenio|'
                  r'regime diferenciado|prestacao de contas|recursos|demonstrativo|gestao fiscal|execucao|decreto financeiro|'
                  r'credito suplementar|credito adicional|credito especial|\bqdd\b|parecer|metas fiscais|quadrimestre')
# audiência ou consulta pública só interessa quando trata de planejamento do território, ambiente ou imposto de imóvel
PLANEJAMENTO = re.compile(r'plano diretor|meio ambiente|ambiental|zoneamento|uso do solo|perimetro urbano|codigo tributario|'
                          r'saneamento|residuos solidos|mobilidade|\beia\b|\brima\b|licenc|empreendimento')
# "declara de utilidade pública a associação X" é título dado a entidade, não desapropriação
ENTIDADE = re.compile(r'reconhec\w+\s+(?:de|como de)\s+utilidade publica|torna de utilidade publica|utilidade publica(?:\s+municipal)?\s+'
                      r'(?:(?:a|o|as|os|da|do|das|dos|para a|para o)\s+)?(?:associa|institu|funda|igreja|centro|clube|grupo|sociedade|'
                      r'projeto|liga|lar|casa|creche|sindicato|cooperativa|comunidade|obra|federac|academia|uniao|camara|conselho|'
                      r'colonia|loja|escola|banda|coral|pastoral|parceria|ong\b)')
DESAPROPRIA = re.compile(r'desapropria|servidao administrativa|imissao|para fins de|interesse social')


def registrar_coleta(chave, **info):
    """Anota em dados/acervo_local.json a data e os números da última coleta (a Central e o painel mostram)."""
    import datetime
    arq = os.path.join(RAIZ, 'dados', 'acervo_local.json')
    d = json.load(open(arq, encoding='utf-8')) if os.path.exists(arq) else {}
    d[chave] = dict(info, coletado_em=datetime.date.today().isoformat())
    json.dump(d, open(arq, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)


def classificar(r):
    tit = sem_acento(r.get('titulo', ''))
    cad = sem_acento(r.get('caderno', ''))
    if (FORA.search(cad) or FORA.search(tit[:80])) and not DESAPROPRIA.search(tit):
        return [], 'fora'  # licitação, contrato, pessoal e contas: fora, mesmo que o texto cite o tema
    temas = [t for t, rx in TEMAS_RE if rx.search(tit)]
    if temas and temas[0].startswith('desapropria') and ENTIDADE.search(tit) and not DESAPROPRIA.search(tit):
        temas = temas[1:]  # título de utilidade pública a entidade: não é desapropriação
        if not temas:
            return [], 'fora'
    if temas == ['participação e planejamento'] and not PLANEJAMENTO.search(tit):
        return [], 'fora'
    if temas:
        return temas, 'alta'
    if FORA.search(cad) or FORA.search(tit[:60]):
        return [], 'fora'
    if NORMATIVO.search(cad) or NORMATIVO.search(tit):
        pelos_termos = sorted({TEMAS[TEMA_DO_TERMO[sem_acento(t)]][0] for t in r.get('termos', []) if sem_acento(t) in TEMA_DO_TERMO})
        return pelos_termos, 'média'
    return [], 'fora'


def main():
    os.makedirs(os.path.dirname(BRUTO), exist_ok=True)
    chave = lambda d: '|'.join([d.get('municipio', ''), d.get('link', ''), d.get('titulo', '')])  # noqa: E731
    acervo = {}
    if os.path.exists(BRUTO):
        acervo = {chave(d): d for d in json.load(gzip.open(BRUTO, 'rt', encoding='utf-8'))}
    antes, recebidos = len(acervo), 0
    for p in sys.argv[1:]:
        for d in json.load(open(p, encoding='utf-8')):
            recebidos += 1
            k = chave(d)
            if k in acervo:  # junta os termos que acharam o mesmo ato
                d['termos'] = sorted(set(acervo[k].get('termos', [])) | set(d.get('termos', [])))
            acervo[k] = d
    regs = sorted(acervo.values(), key=lambda d: (d.get('data', ''), d.get('municipio', ''), d.get('titulo', '')), reverse=True)
    with gzip.open(BRUTO, 'wt', encoding='utf-8') as g:
        json.dump(regs, g, ensure_ascii=False)
    linhas = []
    for d in regs:
        temas, rel = classificar(d)
        if rel == 'fora':
            continue
        linhas.append({'municipio': d.get('municipio', ''), 'data': d.get('data', ''), 'plataforma': d.get('plataforma', ''),
                       'edicao': d.get('edicao', ''), 'caderno': d.get('caderno', ''), 'titulo': d.get('titulo', '')[:400],
                       'temas': '; '.join(temas), 'relevancia': rel, 'termos': '; '.join(sorted(d.get('termos', []))),
                       'link': d.get('link', '')})
    with open(os.path.join(BASE, 'atos_municipais_oeste.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS, delimiter=';')
        w.writeheader()
        w.writerows(linhas)
    altas = [x for x in linhas if x['relevancia'] == 'alta']
    L = ['# Diários oficiais municipais do Oeste da Bahia – atos por tema\n',
         'Fontes oficiais: o Diário Oficial de cada prefeitura, pela busca pública da plataforma (DOEM/IBDM em '
         'https://doem.org.br/ba/<município>/pesquisar e Diário Mtransparente em https://pm<município>.diariomtransparente.com.br/publicacoes). '
         'Coletor: `coletor/coletor_diarios.js`; busca por tema, nunca por nome de pessoa.\n']
    if linhas:
        L.append(f"Período: atos de {min(x['data'] for x in linhas if x['data'])} a {max(x['data'] for x in linhas)}.\n")
    L.append(f'- Atos na tabela: **{len(linhas)}** ({len(altas)} de relevância alta: o título trata do tema; '
             f'{len(linhas) - len(altas)} de relevância média: abrir o PDF da edição)')
    L.append(f'- Achados pela busca e deixados só no bruto (licitações, contratos, pessoal): {len(regs) - len(linhas)}')
    L.append('\n## Por município\n')
    L.append('| Município | Atos | Relevância alta | Mais recente |\n|---|---:|---:|---|')
    for m, n in Counter(x['municipio'] for x in linhas).most_common():
        do = [x for x in linhas if x['municipio'] == m]
        L.append(f"| {m} | {n} | {sum(1 for x in do if x['relevancia'] == 'alta')} | {max(x['data'] for x in do)} |")
    L.append('\n## Por tema (relevância alta)\n')
    for t, n in Counter(t for x in altas for t in x['temas'].split('; ') if t).most_common():
        L.append(f'- {t}: {n}')
    L.append('\n## Desapropriação, utilidade pública, perímetro urbano e plano diretor (relevância alta, mais recentes)\n')
    L.append('| Data | Município | Ato |\n|---|---|---|')
    for x in [x for x in altas if re.search(r'desapropria|urbanismo', x['temas'])][:40]:
        L.append(f"| {x['data']} | {x['municipio']} | [{x['titulo'][:150]}]({x['link']}) |")
    L.append('\n## Observações\n')
    L.append('- A tabela traz o título do ato e o endereço da edição; o texto integral está no PDF oficial.')
    L.append('- Municípios cujo diário é publicado em plataforma que recusa acesso automatizado (robots.txt) ficam de fora '
             'e são conferidos à mão: ver `dados/diarios_municipais/plataformas.csv`.')
    open(os.path.join(BASE, 'resumo.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    if recebidos:
        registrar_coleta('diarios_municipais', atos=len(linhas), relevancia_alta=len(altas), ate=max(x['data'] for x in linhas),
                         municipios=sorted({x['municipio'] for x in linhas}))
    print(f'recebidos {recebidos}; bruto {antes} -> {len(regs)}; na tabela {len(linhas)} ({len(altas)} de relevância alta)')


if __name__ == '__main__':
    main()
