# Atualização semanal do acervo local: decretos de utilidade pública, diários municipais, obras e planos

Roteiro da tarefa agendada "ECOPLAN – acervo jurídico local e alertas (semanal)" (quarta-feira, 16h17, horário da
Bahia; criada em 25/11/2026 com o sim do RT) e de quem for rodar à mão. Escreva tudo em português. Se uma etapa falhar, registre
o motivo e siga com as outras. As regras do `ATUALIZACAO.md` (seção Regras) valem aqui: coleta só pelo navegador
embutido do Claude no computador do escritório; nunca digitar senha, fazer login nem contornar captcha, bloqueio,
`robots.txt` ou termos de uso; repositório público, sem dado de cliente; não inventar número, data nem norma.

O que esta rotina mantém (pasta `dados/`):

| Tabela | Fonte oficial | Coletor e script |
|---|---|---|
| `utilidade_publica/decretos_utilidade_publica_ba.csv` | Legisla Bahia (Casa Civil): Decretos Numerados com a ementa "utilidade pública" | `coletor/coletor_dup.js` e `scripts/processar_dup.py` |
| `diarios_municipais/atos_municipais_oeste.csv` | diário oficial de cada prefeitura do Oeste (lista em `diarios_municipais/plataformas.csv`) | `coletor/coletor_diarios.js` e `scripts/processar_diarios.py` |
| `infraestrutura/obras_e_planos_oeste.csv` | página oficial do órgão ou da prefeitura (ferrovia, rodovia, energia, plano diretor) | à mão, uma linha por fato |
| `acervo_local.json` | – | data e números da última coleta (gravado pelos scripts) |

Para que serve: o sistema da ECOPLAN (`ddrural/alertas.py`, no repositório privado) cruza essas tabelas com os imóveis
do cadastro. O que é do município vira contexto na ficha do imóvel; o ato que cita a fazenda vira alerta.

Sem buscas repetidas (pedido do RT em 25/11/2026): esta rotina é a dona dos decretos de utilidade pública, dos diários
municipais e das obras e planos. Ela não pesquisa o que outra rotina já busca: autuações, CEPRAM, TJBA e normas de
fiscalização são da rotina de segunda (`ATUALIZACAO.md`); atos do INEMA, da coleta diária do DOE-BA; notícias do agro,
do radar do projeto do Instagram. O que aparecer aqui e for da alçada de outra rotina vai como pista para a base dela
(`juridico/PENDENCIAS.md`), sem repetir a pesquisa.

## 0. Preparar

```bash
# add_repo jmarconluz/base-inema-oeste (push), jmarconluz/ecoplan-base-dados (push) e jmarconluz/ecoplan-laudos (read)
cd <clone do base-inema-oeste>
git config user.email noreply@anthropic.com && git config user.name Claude
SHA=$(git rev-parse HEAD); mkdir -p /tmp/pacotes
python -c "import json; print(json.dumps(json.load(open('dados/acervo_local.json')), ensure_ascii=False, indent=1))"
```

- Navegador embutido, carga dos coletores pelo commit `SHA` e exportação em pacotes: como na seção 0 do
  `ATUALIZACAO.md`. Sites desta rotina, já liberados em 25/11/2026: `www.legislabahia.ba.gov.br`, `doem.org.br` e
  `pmbarreiras.diariomtransparente.com.br`. Site novo que pedir liberação: registre em `juridico/PENDENCIAS.md`
  ("aguardando liberação de <site> no navegador"), peça no resumo e siga.
- Sem navegador (computador desligado ou app fechado): pule as seções 1 a 4, faça a 6 (integração e resumo dos
  alertas, que não dependem do computador) e diga no aviso que a coleta ficou para a semana seguinte.

## 1. Decretos estaduais de utilidade pública (Legisla Bahia)

Aba em `https://www.legislabahia.ba.gov.br/`. Carregue `coletor/coletor_dup.js` e rode, sem esperar o fim:

```js
window.__r = null; DUP.colher('<desde>').then(r => window.__r = r)   // <desde> = "ate" de utilidade_publica menos 45 dias
// acompanhe DUP.estado (paginas, lidos, rodando); no fim:
await DUP.preparar()        // {chave: 'dup_ba', n, partes}
DUP.parte(0)                // uma chamada por parte: o resultado é salvo em arquivo
```

```bash
python scripts/decodificar_partes.py /tmp/pacotes <arquivos das partes>
python scripts/processar_dup.py /tmp/pacotes/dup_ba.json
```

- O coletor guarda só os decretos de desapropriação, servidão, interesse social ou ocupação (o título de utilidade
  pública dado a entidade fica de fora) e lê o texto de cada um.
- Confira em `dados/utilidade_publica/resumo.md` a seção "Oeste Baiano": decreto novo no Oeste entra no aviso (seção 7)
  com município, entidade, para que serve e o endereço oficial.
- Para recuar o acervo no tempo (hoje começa em 2024), rode uma vez `DUP.colher('<ano>-01-01')`: é demorado
  (cerca de 400 decretos por ano); faça só quando sobrar tempo, um ano por execução.

## 2. Diários oficiais municipais (DOEM e Diário Mtransparente)

Duas abas, o mesmo coletor (`coletor/coletor_diarios.js`), busca por tema (nunca por nome de pessoa):

- `https://doem.org.br/ba/formosadoriopreto/pesquisar` – cobre de uma vez Formosa do Rio Preto, Riachão das Neves,
  Correntina, Santa Rita de Cássia, Cotegipe e Cristópolis;
- `https://pmbarreiras.diariomtransparente.com.br/publicacoes` – Barreiras.

```js
window.__r = null; DOM.colher('<desde>').then(r => window.__r = r)   // <desde> = "ate" de diarios_municipais menos 14 dias
// no fim (DOM.estado.rodando === false): await DOM.preparar(); DOM.parte(0) …   (chaves diarios_doem e diarios_mtransparente)
```

```bash
python scripts/decodificar_partes.py /tmp/pacotes <arquivos das partes>
python scripts/processar_diarios.py /tmp/pacotes/diarios_doem.json /tmp/pacotes/diarios_mtransparente.json
```

- O script classifica cada ato por tema (desapropriação e utilidade pública; urbanismo e uso do solo; tributos sobre
  imóveis; ambiental municipal; participação e planejamento; infraestrutura) e pela relevância; licitação, pessoal e
  orçamento ficam de fora.
- Leia os atos novos de relevância alta em `dados/diarios_municipais/resumo.md`. Para lei de perímetro urbano, plano
  diretor, zoneamento ou decreto de desapropriação, abra a edição e confira o título; o que mudar a vida de imóvel
  rural entra no aviso.

## 3. Obras, ferrovias e planos diretores

Até 3 conferências por execução, só em página oficial (prefeitura, ANTT, DNIT, Infra S.A., ANEEL, SEINFRA-BA):

- releia as linhas de `dados/infraestrutura/obras_e_planos_oeste.csv` com a conferência mais antiga e atualize
  `conferido_em` (com "sem mudança" na observação do commit, quando for o caso);
- fato novo (trecho licitado, decreto de utilidade pública federal, plano diretor aprovado, audiência marcada) entra
  como linha nova: data, municípios, tema, título, o que muda (em linguagem simples), fonte oficial, link, conferido em
  e a marca [C]. Notícia de imprensa só serve de pista: sem fonte oficial, não entra.

## 4. Expansão (um item por execução, até 30 minutos)

Na ordem de `dados/diarios_municipais/plataformas.csv`:

1. município "pronta para ligar": abrir a busca pública da plataforma no navegador, conferir `robots.txt` e termos,
   anotar o endereço e os parâmetros e acrescentar o adaptador ao `coletor/coletor_diarios.js` (mesmo formato de
   registro); mudar a linha do município para "ligada";
2. município "a conferir": achar no site oficial da prefeitura onde o diário é publicado e atualizar a linha;
3. plataforma do IMAP (`robots.txt` recusa acesso automatizado): não automatizar. Fica "manual" até a plataforma
   mudar; consulta só à mão, quando um caso pedir.

Registre o que andou em `juridico/PENDENCIAS.md` (item 8).

## 5. Conferir e publicar

```bash
python scripts/privacidade.py --aplicar && python scripts/privacidade.py --conferir     # tem de dar 0
git add coletor scripts dados juridico/PENDENCIAS.md ATUALIZACAO_ACERVO_LOCAL.md
git commit -m "Acervo local AAAA-MM-DD: <N decretos novos (M no Oeste), K atos municipais novos, o que mais mudou>"
git pull --rebase origin main && git push origin main
```

Nada de cliente da ECOPLAN entra aqui: nem nome de cliente, nem imóvel da carteira, nem o resultado do cruzamento.

## 6. Integrar e ver os alertas (repositórios privados)

```bash
cd <clone do ecoplan-laudos>     # pip install --break-system-packages -q -r requirements.txt, se faltar pacote
DDRURAL_BASE_INEMA=<clone do base-inema-oeste> python -m ddrural integrar --pasta <clone do ecoplan-base-dados>
python -m ddrural alertas --pasta <clone do ecoplan-base-dados>
```

- A integração tem de vir sem erro e com `"pendencias_integracao": 0`; ela refaz `cadastro/gerado/alertas.csv`,
  `semaforo.csv` e `contexto_municipal.csv` e envia só `cadastro/gerado/`.
- `ddrural alertas` imprime o resumo da semana: alertas com prazo correndo, com prazo a confirmar e os novos em 7 dias.

### 6A. Andamento dos processos judiciais registrados (DataJud do CNJ)

O RT autorizou em 25/11/2026 o uso da API pública do DataJud, só para o andamento dos processos já registrados no
cadastro privado (`cadastro/processos_judiciais.csv`, com `acompanhar` = sim), pelo número. Nada de busca por nome ou
CPF/CNPJ, e nada disso vem para este repositório.

```bash
cd <clone do ecoplan-laudos>
python ferramentas/datajud.py js --base <clone do ecoplan-base-dados>      # imprime o código da consulta
```

- Abra uma aba em `https://api-publica.datajud.cnj.jus.br/` (a página mostra um erro 401: é o esperado) e rode ali o
  código impresso. Ele dispara e volta na hora; acompanhe `window.__datajud.fim`. Em dia de servidor cheio (429 ou 504)
  leva alguns minutos por processo.
- No fim, peça `JSON.stringify(window.__datajud)` (o resultado é salvo em arquivo) e rode
  `python ferramentas/datajud.py gravar --base <clone do ecoplan-base-dados> <arquivo>`. Ele diz o que mudou.
- Resultado com partes do índice sem resposta é inconclusivo: nunca escrever "processo não encontrado" por causa dele.
- O DataJud não é em tempo real e traz só o nome dos movimentos, não o texto das decisões. Quando o `gravar` avisar que
  o registro tem mais de 45 dias (`avisos`), não é falha: diga a data do registro junto com o andamento e, se o caso
  pedir a situação de hoje, deixe a conferência no tribunal como passo para o RT (consulta à mão).
- Se algum andamento mudou: commit só de `cadastro/processos_judiciais.csv` no ecoplan-base-dados ("Processos
  judiciais: andamento conferido no DataJud em DD/MM/AAAA") e push; o andamento novo entra no aviso (seção 7).
- Sem processo com `acompanhar` = sim, ou com o site ainda não liberado no navegador, pule esta parte.

## 7. Avisar o RT

Uma mensagem por semana, em até 8 linhas, começando por "⚖️ Alertas e acervo local – DD/MM":

- alertas com prazo correndo ou a confirmar (imóvel ou cliente, o que é e a data) e os novos da semana;
- decreto estadual de utilidade pública novo no Oeste e ato municipal novo que pese em imóvel rural (perímetro urbano,
  plano diretor, zoneamento, desapropriação), com o endereço oficial;
- o item da expansão feito e o que falhou ou ficou aguardando liberação.

Notificação no celular só quando houver alerta vermelho novo, prazo correndo novo, decreto ou ato que cite fazenda da
carteira, ou falha que dependa do RT. Semana sem novidade: uma linha só, sem notificação.
