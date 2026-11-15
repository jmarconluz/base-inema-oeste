"""Máscara de dados pessoais (CPF, RG e CNH) usada em toda a base — o repositório é público.

    from privacidade import mascara
    mascara('Fulano, CPF nº 123.456.789-09, RG 1234567 SSP/BA')
    -> 'Fulano, CPF nº ***.***.***-**, RG ******* SSP/BA'

CNPJ (empresa) não é mascarado. Uso pela linha de comando (varre os arquivos versionados):
    python scripts/privacidade.py --conferir     # só conta o que seria mascarado
    python scripts/privacidade.py --aplicar      # mascara e regrava (gz com mtime=0)
"""
import gzip, os, re, subprocess, sys

MASCARA_CPF = '***.***.***-**'
# CPF com pontos (aceita espaços soltos entre os grupos, comuns no texto do DOE)
CPF_FORMATADO = re.compile(r'(?<!\d)\d{3}\s*\.\s*\d{3}\s*\.\s*\d{3}\s*-\s*\d{2}(?!\d)')
# CPF sem pontos, com hífen: 123456789-09 (não pega números de processo com / ou .)
CPF_HIFEN = re.compile(r'(?<![\d./\-])\d{3}\s?\d{3}\s?\d{3}\s?-\s?\d{2}(?![\d/])')
# 11 dígitos logo depois do rótulo CPF (até 25 caracteres sem dígito no meio: "CPF sob o nº ", "CPF/MF: ")
CPF_ROTULO = re.compile(r'(C\.?\s?P\.?\s?F\.?[^0-9]{0,25}?)(?<!\d)\d{11}(?!\d)')
# RG e CNH só quando rotulados
RG = re.compile(r'(\b(?:R\.?\s?G\.?|C\.?\s?I\.?|[Cc]arteira de [Ii]dentidade|[Ii]dentidade)(?:\s*n[º°o.]*)?\s*[:.\-]?\s*)(?<![\d])(\d[\d.\-]{4,14}\d)(?![\d/])')
CNH = re.compile(r'(\bCNH(?:\s*n[º°o.]*)?\s*[:.\-]?\s*)(?<!\d)\d{9,11}(?!\d)')


def mascara(t):
    if not t:
        return t
    t = CPF_FORMATADO.sub(MASCARA_CPF, t)
    t = CPF_HIFEN.sub(MASCARA_CPF, t)
    t = CPF_ROTULO.sub(lambda m: m.group(1) + MASCARA_CPF, t)
    t = RG.sub(lambda m: m.group(1) + '*' * len(m.group(2)), t)
    t = CNH.sub(lambda m: m.group(1) + '***********', t)
    return t


TEXTO = ('.json', '.csv', '.geojson', '.md', '.txt', '.tsv')
FORA = ('juridico/legislacao/', 'scripts/', 'coletor/')     # lei fica literal; código não é dado


def arquivos(raiz):
    saida = subprocess.run(['git', '-C', raiz, 'ls-files'], capture_output=True, text=True).stdout.split('\n')
    for f in saida:
        if f and not f.startswith(FORA) and (f.endswith(TEXTO) or f.endswith(tuple(e + '.gz' for e in TEXTO))):
            yield f


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ('--conferir', '--aplicar'):
        sys.exit(__doc__)
    aplicar = sys.argv[1] == '--aplicar'
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    total = 0
    for f in arquivos(raiz):
        c = os.path.join(raiz, f)
        gz = f.endswith('.gz')
        bruto = gzip.open(c, 'rb').read() if gz else open(c, 'rb').read()
        t = bruto.decode('utf-8')          # mantém BOM e quebras de linha (\r\n do CSV) como estão
        novo = mascara(t)
        if novo == t:
            continue
        n = sum(1 for a, b in zip(t.split('\n'), novo.split('\n')) if a != b)
        total += n
        print(f'{f}: {n} linha(s) com dado pessoal')
        if aplicar:
            if gz:
                with gzip.GzipFile(c, 'wb', mtime=0) as g:
                    g.write(novo.encode('utf-8'))
            else:
                open(c, 'wb').write(novo.encode('utf-8'))
    print(('mascaradas' if aplicar else 'a mascarar') + f': {total} linha(s)')


if __name__ == '__main__':
    main()
