# Base jurídica ambiental — defesa de autos de infração (foco Bahia)

Montada em 14/11/2026 para a Ecoplan Consultoria Ambiental. Serve para analisar e defender multas, embargos e
interdições do INEMA, do IBAMA e de municípios, com foco no Oeste Baiano.

## Comece por aqui

| Arquivo | Para quê |
|---|---|
| `checklist_analise_auto.md` | roteiro quando chega um auto: prazos, prescrição, nulidades, autoria, competência, Código Florestal, dosimetria, estratégia |
| `teses_defesa.md` | as teses, com base legal, precedentes conferidos e grau de força |
| `precedentes_cepram.md` | 156 decisões favoráveis do CEPRAM (prescrição, nulidade da notificação, advertência, redução, anulação), com nº da resolução e do processo |
| `modelos_pecas.md` | esqueletos de defesa, recurso ao CEPRAM, prescrição, conversão de multa e desembargo |
| `acesso_processos.md` | como obter a cópia integral dos processos (SEIA, SEI Bahia, LAI, IBAMA) + modelos de pedido |
| `legislacao/artigos_chave.md` | texto integral dos artigos usados nas teses (federal e Bahia) |
| `legislacao/federal/`, `legislacao/bahia/` | texto vigente completo das leis e decretos (Planalto e Casa Civil-BA) |
| `jurisprudencia/stj/indice_temas.md` | STJ: 62 temas repetitivos com assunto ambiental (tese firmada) e 3.895 acórdãos ambientais separados por tema de defesa |
| `jurisprudencia/stj/stj_acordaos_ambientais.json` | os 3.895 acórdãos do STJ (1990–2026; 1ª e 2ª Turmas, 1ª Seção e Corte Especial): ementa, tese, normas citadas, link da consulta processual — fonte: Portal de Dados Abertos do STJ |
| `jurisprudencia/stj/temas_repetitivos_ambientais.csv` | os temas repetitivos e precedentes qualificados ambientais, do CSV oficial do STJ |
| `jurisprudencia/tjba/indice_temas.md` | decisões do TJBA separadas por tema de defesa (prescrição, nulidade, competência, autoria, embargo, valor da multa, conversão, execução fiscal, demora do órgão), com link do inteiro teor |
| `jurisprudencia/tjba/tjba_inema_multas.json` | 1.263 decisões do 2º grau do TJBA (INEMA, multa ambiental, IBAMA, CEPRAM, SEMA, Lei 10.431, Decreto 14.024, Lei 12.209, Lei 9.605, Decreto 6.514...): ementa, trechos, link do inteiro teor |
| `PENDENCIAS.md` | o que ainda falta pesquisar (fundamentos do CEPRAM, STJ, TRF1, normas do INEMA...); a atualização semanal avança um item por vez |

Bases de dados relacionadas (fora desta pasta):

- `multas/bahia_doe/` — 15.117 autuados em editais do INEMA (2016–2026), 847 decisões do CEPRAM, 138 conversões/TCs.
- `multas/ibama/` — 26.013 autos e 4.963 embargos do IBAMA na Bahia (com polígonos) e o resumo do Brasil inteiro.

## Legislação guardada

Federal: Lei 9.605/1998, Decreto 6.514/2008, LC 140/2011, Lei 12.651/2012, Lei 9.873/1999, Lei 9.784/1999,
Lei 10.650/2003, Lei 12.527/2011, LC 123/2006, Lei 6.938/1981, Lei 9.433/1997, Lei 11.428/2006, Decreto 6.660/2008,
Lei 9.985/2000, Lei 13.874/2019, Lei 6.830/1980, Decreto 20.910/1932, LINDB.

Bahia: Lei 10.431/2006, Decreto 14.024/2012, Lei 11.612/2009, Lei 12.209/2011 (processo administrativo — prescrição),
Decreto 15.805/2014, Lei 12.618/2012 (LAI), Lei 13.597/2016 (PRA).

Normas e formulários do INEMA: `modelos_inema/` (raiz do repositório).

## Como a base se atualiza

Toda semana uma tarefa agendada segue o roteiro de `ATUALIZACAO.md` (raiz do repositório):

- **Diário Oficial (multas, CEPRAM, conversões):** `coletor/coletor_multas.js` no navegador refaz os últimos 10 dias
  e exporta só as matérias novas; `scripts/incorporar_doe.py` (mascara CPF), `processar_multas.py` e
  `gerar_precedentes_cepram.py` refazem as tabelas.
- **TJBA:** `coletor/coletor_tjba.js` (`TJ.novas`), `scripts/incorporar_tjba.py` e `scripts/indexar_tjba.py`;
  varredura completa uma vez por mês.
- **Leis:** `coletor/coletor_lex.js` compara o texto vigente no Planalto e na Casa Civil-BA com
  `legislacao/hashes.json`; mudança vira registro em `legislacao/ALTERACOES.md` e revisão das teses.
- **STJ:** uma vez por mês, `coletor/coletor_stj.js` no Portal de Dados Abertos do STJ (só os arquivos mensais novos),
  `scripts/incorporar_stj.py` e `scripts/indexar_stj.py`. A pesquisa scon.stj.jus.br tem verificação contra robôs e
  não é usada para coleta.
- **IBAMA:** uma vez por mês, `coletor/coletor_ibama.js` (ver `scripts/ibama_navegador.md`).
- **Expansão:** um item de `PENDENCIAS.md` por semana.

## Limites

- Material técnico de apoio; não substitui advogado nas ações judiciais.
- Campos das tabelas extraídos automaticamente do texto do DOE: conferir sempre no texto e no link.
- O DOE só traz os autuados notificados por edital, as homologações e as decisões do CEPRAM; autos entregues em mãos
  não aparecem ali (por isso a base do IBAMA e as cópias dos processos completam o quadro).
