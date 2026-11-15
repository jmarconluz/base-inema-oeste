"""Controle de alterações da legislação guardada em juridico/legislacao/{federal,bahia}/*.txt.

Cada arquivo tem um cabeçalho ("Fonte: <url>" ...), uma linha em branco e o texto vigente extraído pelo
coletor/coletor_lex.js. O arquivo juridico/legislacao/hashes.json guarda, por norma, a URL, o SHA-256 e o
tamanho do texto; o navegador (LEX.verificarRepo) compara com o site oficial e aponta o que mudou.

Uso:
    python scripts/verificar_legislacao.py hashes                 # (re)gera hashes.json a partir dos arquivos
    python scripts/verificar_legislacao.py atualizar PACOTE.json   # grava os textos novos (saída do LEX.preparar
                                                                   # decodificada), atualiza hashes.json e registra
                                                                   # a mudança em juridico/legislacao/ALTERACOES.md
Arquivos *_paragrafos.txt são derivados e ficam fora do controle.
"""
import datetime, glob, hashlib, json, os, re, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEG = os.path.join(RAIZ, 'juridico', 'legislacao')
HASHES = os.path.join(LEG, 'hashes.json')


def arquivos():
    for f in sorted(glob.glob(os.path.join(LEG, '*', '*.txt'))):
        if not f.endswith('_paragrafos.txt'):
            yield f


def ler(f):
    s = open(f, encoding='utf-8').read()
    cab, _, corpo = s.partition('\n\n')
    m = re.match(r'Fonte:\s*(\S+)', cab)
    return (m.group(1) if m else None), cab, corpo


# Cabeçalho institucional do Planalto (muda de formato sem mudar a norma): fica fora do hash.
CAB_PLANALTO = re.compile(r'^Presid[êe]ncia da Rep[úu]blica\n(?:Casa Civil\n)?(?:Subchefia|Secretaria Especial) para Assuntos Jur[íi]dicos\n')


def canon(t):
    return CAB_PLANALTO.sub('', t)


def sha(t):
    return hashlib.sha256(canon(t).encode('utf-8')).hexdigest()


def gerar_hashes():
    out = []
    for f in arquivos():
        url, _, corpo = ler(f)
        if url:
            out.append({'url': url, 'arquivo': os.path.relpath(f, RAIZ), 'sha256': sha(corpo), 'chars': len(corpo)})
    json.dump(out, open(HASHES, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{len(out)} normas em {os.path.relpath(HASHES, RAIZ)}')


def atualizar(pacotes):
    ref = {x['url']: x for x in json.load(open(HASHES, encoding='utf-8'))}
    log = []
    hoje = datetime.date.today().isoformat()
    for p in pacotes:
        for d in json.load(open(p, encoding='utf-8')):
            if d.get('erro') or d['url'] not in ref:
                print('ignorado:', d.get('url'), d.get('erro', 'URL fora do hashes.json')); continue
            r = ref[d['url']]
            if sha(d['texto']) == r['sha256']:
                print('sem mudança:', r['arquivo']); continue
            caminho = os.path.join(RAIZ, r['arquivo'])
            _, cab, corpo_antigo = ler(caminho)
            open(caminho, 'w', encoding='utf-8').write(cab + '\n\n' + d['texto'])
            log.append(f"| {hoje} | [{os.path.basename(caminho)}]({d['url']}) | {len(corpo_antigo)} → {len(d['texto'])} caracteres |")
            print('ATUALIZADO:', r['arquivo'], len(corpo_antigo), '->', len(d['texto']))
    if log:
        alt = os.path.join(LEG, 'ALTERACOES.md')
        if not os.path.exists(alt):
            open(alt, 'w', encoding='utf-8').write('# Alterações detectadas na legislação guardada\n\n'
                                                   'Conferir no site oficial o que mudou (nova redação, revogação, inclusão) '
                                                   'e revisar as teses e os modelos que citam a norma.\n\n'
                                                   '| Data | Norma | Tamanho do texto |\n|---|---|---|\n')
        open(alt, 'a', encoding='utf-8').write('\n'.join(log) + '\n')
    gerar_hashes()


if __name__ == '__main__':
    if len(sys.argv) >= 2 and sys.argv[1] == 'hashes':
        gerar_hashes()
    elif len(sys.argv) >= 3 and sys.argv[1] == 'atualizar':
        atualizar(sys.argv[2:])
    else:
        sys.exit(__doc__)
