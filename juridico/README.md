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
| `jurisprudencia/tjba/tjba_inema_multas.json` | 682 decisões do TJBA que citam INEMA, multa ambiental, IBAMA ou CEPRAM (ementa, trechos, link do inteiro teor) |

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

- **Diário Oficial (multas, CEPRAM, conversões):** `coletor/coletor_multas.js` no navegador, só as datas novas;
  depois `python scripts/processar_multas.py` e `python scripts/gerar_precedentes_cepram.py`.
- **IBAMA:** `coletor/coletor_ibama.js` (ver `scripts/ibama_navegador.md`).
- **TJBA:** `coletor/coletor_tjba.js` (API pública do portal de jurisprudência).
- **Leis:** baixar de novo a página do Planalto/legislabahia e comparar (`git diff`).
- Uma tarefa agendada repete isso periodicamente e registra as novidades no histórico do repositório.

## Limites

- Material técnico de apoio; não substitui advogado nas ações judiciais.
- Campos das tabelas extraídos automaticamente do texto do DOE: conferir sempre no texto e no link.
- O DOE só traz os autuados notificados por edital, as homologações e as decisões do CEPRAM; autos entregues em mãos
  não aparecem ali (por isso a base do IBAMA e as cópias dos processos completam o quadro).
