# Autos de infração e embargos do IBAMA

Fonte: Portal de Dados Abertos do IBAMA (`dadosabertos.ibama.gov.br`), conjuntos
"Fiscalização - auto de infração" e "Termos de embargo". Arquivos baixados em 16/11/2026
(versão publicada pelo IBAMA em 16/11/2026; a anterior era de 13/11/2026).

| Arquivo | Conteúdo |
|---|---|
| `autos_infracao_ibama_BA.csv.gz` | 26.019 linhas de autos de infração do IBAMA na Bahia (1977–2026), com descrição, valor, enquadramento, município, coordenadas, processo, status e área |
| `termos_embargo_ibama_BA.csv.gz` | 4.964 termos de embargo do IBAMA na Bahia, com polígono (WKT), área, situação de desembargo, imóvel e auto vinculado |
| `autos_ibama_brasil_resumo.csv` | Brasil inteiro: 713.505 autos, agrupados por UF, ano, status, cancelamento e tipo de infração (quantidade e valor) |
| `embargos_ibama_brasil_resumo.csv` | Brasil inteiro: 117.255 termos de embargo, por UF, ano, status e desembargo (quantidade e área) |

CSV com `;`, UTF-8 com BOM. CPFs mascarados.

## Uso na defesa e na due diligence

- **Histórico do imóvel/autuado:** filtrar por município, nome, CNPJ ou coordenadas antes de comprar uma fazenda
  (os polígonos de embargo abrem direto no QGIS a partir da coluna `GEOM_AREA_EMBARGADA`).
- **Comparar o enquadramento e a dosimetria** de um auto novo com autos semelhantes (`DS_ENQUADRAMENTO_ADMINISTRATIVO`,
  `FUNDAMENTACAO_MULTA`, `VAL_AUTO_INFRACAO`, `GRAVIDADE_INFRACAO`).
- **Bis in idem / art. 76 da Lei 9.605/98:** cruzar o mesmo fato com a base do INEMA (`multas/bahia_doe`).
- **Cópia do processo:** o número `NU_PROCESSO_FORMATADO` é o processo SEI do IBAMA (consulta em
  `sei.ibama.gov.br` – Pesquisa Pública, ou pedido de vista/cópia pelo autuado).

## Atualizar

Os arquivos ficam no armazenamento do IBAMA (`stibamadadosabertosprd.blob.core.windows.net`), que só se acessa pelo
navegador. O procedimento está em `scripts/ibama_navegador.md`; para gravar os CSVs a partir dos pacotes, `python scripts/ibama_csv.py` (formato igual ao destes arquivos, CPF mascarado).
