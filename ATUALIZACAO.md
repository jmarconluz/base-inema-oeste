# Atualização semanal da base de multas e da base jurídica

Procedimento seguido pela tarefa agendada "Base de multas e jurídica: atualização semanal" (e por quem for rodar à
mão). Escreva tudo em português. Se uma etapa falhar, registre o motivo e siga com as outras.

## Regras

- Os sites do governo da Bahia (DOE, Casa Civil, TJBA) só respondem do Brasil e o ambiente de nuvem não alcança sites
  do governo: tudo o que é coleta roda no **navegador embutido** do Claude no computador do usuário
  (ferramentas `mcp__remote-devices__Claude_Browser__*`). Se o navegador não responder (computador desligado ou app
  fechado), não insista: avise o usuário e encerre.
- Nunca digitar senha nem fazer login; nunca contornar captcha, bloqueio ou termos de uso; não mexer no Chrome do
  usuário (lá pode estar rodando a coleta do SEIA) nem no SEIA.
- O repositório é público: CPF, RG e CNH sempre mascarados (`scripts/privacidade.py`); nenhum dado de cliente aqui.
- Não invente número, data nem norma. Não apague arquivos existentes.
- **Fontes confiáveis e atualização contínua (regra permanente do RT, 21/11/2026):** cada execução tenta subir de nível
  pelo menos um item da base — trocar fonte secundária [2ª] por fonte oficial [C], fechar um item "bloqueado" ou
  "aguardando" quando houver caminho legítimo, completar o que falta — e registra a data da conferência. O que não der
  para conferir fica marcado com o motivo. Quando o navegador embutido não alcançar um site oficial, tente o WebSearch e
  o WebFetch: em 21/11/2026 o WebFetch abriu páginas do gov.br (ICMBio, Participa + Brasil) que o shell da nuvem não
  alcança. Ele devolve um resumo da página, não o texto: serve para conferir situação, número e data, não para guardar
  texto integral no acervo. Regra completa no CLAUDE.md do `ecoplan-laudos`.

## 0. Preparar

```bash
# add_repo jmarconluz/base-inema-oeste (access push), depois:
git clone https://github.com/jmarconluz/base-inema-oeste && cd base-inema-oeste
git config user.email noreply@anthropic.com && git config user.name Claude
SHA=$(git rev-parse HEAD); mkdir -p /tmp/pacotes
```

- Carregue as ferramentas do navegador embutido de uma vez (ToolSearch com `mcp__remote-devices__Claude_Browser__`,
  max_results 64) e leia a skill `built-in-browser`, se estiver na lista.
- `tabs_context`: reaproveite abas que já estejam nos sites; senão `tabs_create` + `navigate`.
- Sites já liberados no navegador embutido: `dool.egba.ba.gov.br`, `jurisprudencia.tjba.jus.br`,
  `www.legislabahia.ba.gov.br`, `www.planalto.gov.br`, `dadosabertos.ibama.gov.br`, o blob de dados abertos do IBAMA
  `dadosabertos.web.stj.jus.br`, `www.ibama.gov.br` (página de legislação do IBAMA), `www.ba.gov.br` (site da SEMA:
  pautas da CT Recursal), `gestor.meioambiente.ba.gov.br` (Consulta de Publicações da SEMA: resoluções do CEPRAM em PDF)
  e `conama.mma.gov.br` (resoluções do CONAMA); desde 23/11/2026 também `www.gov.br` (páginas do ICMBio, do IBAMA e da
  AGU), `jurisprudenciaws.tjba.jus.br` (API e inteiro teor do TJBA) e a consulta pública do PJe do 2º grau do TRF1
  (`pje2g.trf1.jus.br`, que leva a `pje2g-consultapublica.trf1.jus.br`; sem verificação contra robôs, busca pelo número).
  Ainda não liberados: `www.in.gov.br` (DOU) e `jurisprudencia.trf1.jus.br` (recusados em 23/11/2026).
  Site novo precisa ser liberado pelo usuário: numa execução agendada não fique esperando a liberação — registre
  "aguardando liberação de <site> no navegador" em `juridico/PENDENCIAS.md`, peça a liberação no resumo e siga.
- Os coletores são carregados no navegador direto do GitHub, no commit `SHA` (sem copiar código à mão):

```js
(0, eval)(await (await fetch('https://raw.githubusercontent.com/jmarconluz/base-inema-oeste/<SHA>/coletor/<arquivo>.js')).text())
// se o fetch acima der "Failed to fetch" (aconteceu em 17/11/2026 nas páginas da SEMA e do TJBA), use o espelho jsDelivr do mesmo commit:
(0, eval)(await (await fetch('https://cdn.jsdelivr.net/gh/jmarconluz/base-inema-oeste@<SHA>/coletor/<arquivo>.js')).text())
```

- **Exportação em pacotes:** os coletores devolvem envelopes `{chave, parte, partes, n, dados, pad}` com mais de
  120 mil caracteres; o resultado do `javascript_tool` é salvo num arquivo (a mensagem de erro informa o caminho,
  em `/tmp/claude-tool-results/...`) e não entra na conversa. Junte as partes com
  `python scripts/decodificar_partes.py /tmp/pacotes <arquivos>` (sem arquivos, ele procura todos sozinho).
- Operações longas no navegador: se o `javascript_tool` estourar o tempo, dispare sem `await`
  (`window.__x = f().then(r => window.__r = r)`) e consulte `window.__r` depois.

## 1. Diário Oficial da Bahia (multas, notificações, homologações, CEPRAM, termos de compromisso)

```bash
python3 -c "import gzip,json,glob;print(max(m['data'] for f in glob.glob('multas/bahia_doe/brutos/*.json.gz') for m in json.load(gzip.open(f,'rt'))))"
```

Seja `ULT` essa data e `DESDE` = ULT − 10 dias (recobre edição que saiu atrasada). Na aba em `https://dool.egba.ba.gov.br/`:

```js
// carregar coletor/coletor_multas.js (bloco acima), depois:
await MUL.rodar('<DESDE>', '<HOJE>', 3, true)   // refaz o intervalo; matérias gravadas por id, sem duplicar
await MUL.p({desde: '<DESDE>'}, 0)               // e as partes 1..partes-1, se houver
```

```bash
python scripts/decodificar_partes.py /tmp/pacotes <arquivos salvos>
python scripts/incorporar_doe.py /tmp/pacotes/doe_enx_tudo_desde_<DESDE>.json
python scripts/processar_multas.py && python scripts/gerar_precedentes_cepram.py
```

Anote do `multas/bahia_doe/resumo.md` e do `git diff --stat`: autuados novos (quantos no Oeste), decisões novas do
CEPRAM (quantas favoráveis e por qual motivo), conversões/termos de compromisso.

## 2. TJBA (jurisprudência)

Na aba em `https://jurisprudencia.tjba.jus.br/`, carregue `coletor/coletor_tjba.js`. `DESDE` = data mais recente do
acervo (`juridico/jurisprudencia/tjba/tjba_inema_multas.json`, campo `data`) − 30 dias. Se o `fetch` para
`jurisprudenciaws.tjba.jus.br/graphql` ficar pendurado a partir dessa aba (aconteceu em 23/11/2026: nem a busca do
próprio portal respondia), abra uma aba em `https://jurisprudenciaws.tjba.jus.br/inteiroTeor/<hash de uma decisão do
acervo>` e carregue o coletor nela: é a mesma origem da API e respondeu em menos de 1 segundo.

```js
await TJ.novas('<DESDE>')        // todos os termos de TJ.TERMOS, da decisão mais recente para trás
await TJ.preparar()              // depois TJ.parte(0), TJ.parte(1)...
```

```bash
python scripts/decodificar_partes.py /tmp/pacotes <arquivos> && python scripts/incorporar_tjba.py /tmp/pacotes/tjba.json
python scripts/indexar_tjba.py
```

Na **primeira execução de cada mês**, faça a varredura completa (`for (const t of TJ.TERMOS) await TJ.colher(t)`),
que pega decisões antigas indexadas com atraso. A paginação da API começa em 0.

Leia as decisões novas que tratem de prescrição, nulidade, competência, autoria, embargo, conversão de multa ou
execução fiscal de multa ambiental; se alguma for útil para a defesa, cite-a (número, órgão, data, link) na tese
correspondente de `juridico/teses_defesa.md`, depois de conferir no inteiro teor.

## 3. Legislação

Em uma aba em `https://www.legislabahia.ba.gov.br/` e em outra em
`https://www.planalto.gov.br/ccivil_03/leis/l9605.htm`, carregue `coletor/coletor_lex.js` e rode
`await LEX.verificarRepo('<SHA>')`. Ele compara o texto vigente com `juridico/legislacao/hashes.json`.

Se `mudou` não vier vazio: `await LEX.preparar([urls])`, `LEX.parte(i)`, decodifique e rode
`python scripts/verificar_legislacao.py atualizar /tmp/pacotes/lex_*.json`. Abra a página oficial, identifique a
mudança (nova redação, revogação, artigo incluído) e revise `juridico/legislacao/artigos_chave.md`,
`juridico/teses_defesa.md` e `juridico/modelos_pecas.md` onde a norma é citada.

Normas novas: pesquise (WebSearch) leis, decretos, resoluções do CEPRAM e portarias do INEMA/SEMA publicadas nos
últimos 7 dias sobre fiscalização, infrações, multas, conversão de multas, embargos, prescrição ou processo
administrativo ambiental (Bahia e federal). Norma nova relevante entra no acervo: arquivo em
`juridico/legislacao/<federal|bahia>/` com o cabeçalho `Fonte: <url>` + linha `(Texto vigente: ...)` + linha em
branco + texto extraído com `LEX.preparar`; depois `python scripts/verificar_legislacao.py hashes`.

## 4. IBAMA e STJ (só na primeira execução do mês)

IBAMA: siga `scripts/ibama_navegador.md` (autos de infração e termos de embargo da Bahia e resumo do Brasil). Para gravar os
CSVs: `python scripts/ibama_csv.py <arquivos salvos>` (os envelopes do IBAMA são do formato antigo `tipo: 'pk'`;
não use o `decodificar_partes.py` para eles). Na mesma execução, numa aba em `https://www.ibama.gov.br/`, confira a IN IBAMA 19/2023
com `await LEX.verificar(['<url do hashes.json>'])` e compare o `sha256` com o de `juridico/legislacao/hashes.json`
(o `LEX.verificarRepo` não roda nessa página: o site substitui o `URL` do navegador).
Ainda na mesma execução, numa aba na página oficial da IN ICMBio 9/2023 compilada
(https://www.gov.br/icmbio/pt-br/acesso-a-informacao/autuacoes-ambientais/infracoes-ambientais/normativas/instrucao-normativa-no-9-gabin-icmbio-de-23-de-agosto-de-2023),
carregue `coletor/coletor_lex.js` e rode `await LEX.verificarRepo('<SHA>')`: o texto integral está no acervo desde
23/11/2026 (`legislacao/federal/in_icmbio_09_2023.txt`, compilada com a IN ICMBio nº 13/2026, página "atualizada em
20/02/2026"). Se `mudou` não vier vazio, siga o mesmo caminho da seção 3 (`LEX.preparar`, `verificar_legislacao.py
atualizar`) e revise a seção 8 de `teses_defesa.md` e o trecho da IN em `artigos_chave.md`.

STJ: numa aba em `https://dadosabertos.web.stj.jus.br/dataset/`, carregue `coletor/coletor_stj.js` e rode
`await STJ.colher(undefined, '<AAAAMM01 do mês anterior>')` (só os arquivos mensais novos) e `await STJ.temas()`;
(o `STJ.temas()` exporta o CSV oficial inteiro, ~2,5 MB; a seleção dos temas ambientais é feita no Python);
depois `await STJ.preparar()` e `STJ.parte(i)`; decodifique e rode `python scripts/incorporar_stj.py
/tmp/pacotes/stj.json` e `python scripts/indexar_stj.py`. Se surgir tema repetitivo ambiental novo ou mudar a situação
de um já listado (ex.: Tema 1.447 julgado), atualize a seção 11 de `juridico/teses_defesa.md`. Não use a pesquisa
scon.stj.jus.br para coleta (tem verificação contra robôs).

## 5. Expansão da base (1 item por execução, até ~40 minutos)

Pegue o primeiro item em aberto de `juridico/PENDENCIAS.md`, trabalhe nele e registre ali o que foi feito (data,
resultado, arquivos). Item que depender de login, captcha ou decisão do usuário: marque "bloqueado" com o motivo e
passe ao próximo na semana seguinte.

### Pautas da CT Recursal do CEPRAM (fato gerador e voto do relator)

Numa aba em `https://www.ba.gov.br/meioambiente/404/pautas-da-camara-tecnica-recursal`, carregue
`coletor/coletor_pdf.js` e rode `await PDF.pacote(PDF.links().map(x => x.url).filter(<só os novos>), 'pdf_ct_<rótulo>')`;
depois `PDF.parte(0)`, `PDF.parte(1)`... (480 mil caracteres por parte; o canal do navegador corta acima de ~500 mil).
Os já baixados estão em `multas/cepram_pautas/pdfs_baixados.json`. Na nuvem: `python scripts/decodificar_partes.py
/tmp/pacotes <arquivos>`, grave os PDFs (campo `b64`) numa pasta e rode `python scripts/extrair_pautas_ct.py <pasta>
<urls.json>` (acumula em `multas/cepram_pautas/pautas_ct_recursal.json.gz` e refaz `juridico/cepram_votos_relator.md`).
Resoluções do CEPRAM em PDF: Consulta de Publicações (`gestor.meioambiente.ba.gov.br/Consultas/ConsultaPublicacao/`,
GET com `texto`, `colegiado=COL_CEPRAM`, `tipoPublicacao=24`); as resoluções em `legislacao/bahia/resolucao-cepram-*`
vêm de lá e são conferidas à mão (o `LEX.verificarRepo` não lê PDF).

## 6. Conferir e publicar

Monte a base unificada para conferir que tudo continua legível: `python scripts/montar_conglomerado.py` (o arquivo
gerado fica fora do git).

```bash
# mascara CPF, RG e CNH em todos os arquivos de dados (idempotente) e confere: a 2ª linha tem de dizer 0
python scripts/privacidade.py --aplicar && python scripts/privacidade.py --conferir | tail -1
git add -A && git commit -m "Atualização semanal AAAA-MM-DD: <resumo>" && git pull --rebase origin main && git push origin HEAD:main
git status && git log origin/main -1 --oneline
```

## 7. Avisar o usuário

`SendUserMessage`, em até 8 linhas: autuados novos (destaque Oeste Baiano), decisões novas do CEPRAM (favoráveis e
motivo), decisões novas do TJBA úteis à defesa, leis alteradas ou novas, item da expansão feito, falhas.
`PushNotification` só se houver lei alterada, norma nova relevante ou falha que dependa do usuário.
