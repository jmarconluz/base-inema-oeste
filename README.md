# Base INEMA – Bahia (foco no Oeste Baiano)

Base de atos autorizativos do **INEMA** publicados no **Diário Oficial do Estado da Bahia (DOE-BA)** nos últimos 10 anos (nov/2016 a nov/2026):

- **Autorização de Supressão de Vegetação Nativa (ASV)**
- **Outorga de direito de uso de recursos hídricos** (captação subterrânea e superficial, barramentos, lançamentos)

Inclui concessões, renovações, alterações e transferências de titularidade. Ficam de fora as revogações, os cancelamentos, os indeferimentos e as suspensões.

Cobre **todo o estado da Bahia**, com o texto integral de cada portaria. Os atos do **Oeste Baiano** também ficam em tabelas próprias.

Ecoplan Consultoria Ambiental – Barreiras/BA.

## Estrutura

```
coletor/coletor_doe.js        coletor que roda no navegador, na página do DOOL (dool.egba.ba.gov.br)
scripts/processar.py          gera as tabelas e o GeoJSON a partir dos arquivos brutos
dados/brutos/                 doe_inema_AAAA.json – saída do coletor, um arquivo por ano
dados/bahia/portarias_bahia.csv / .json   todos os atos da Bahia, com texto integral
dados/bahia/pontos_outorga_bahia.geojson / pontos_asv_bahia.geojson   coordenadas publicadas na Bahia (QGIS), separadas por outorga e ASV
dados/oeste/portarias_oeste.csv          atos do Oeste com o texto integral da portaria
dados/oeste/portarias_oeste.json         idem, em JSON
dados/oeste/pontos_outorga_oeste.geojson / pontos_asv_oeste.geojson   idem, só Oeste
dados/resumo.md               números da base por ano e por município
```

Os CSV usam `;` como separador e codificação UTF-8 com BOM, então abrem direto no Excel. O GeoJSON está em SIRGAS 2000 geográfico (EPSG:4674).

## Campos

| Campo | Descrição |
|---|---|
| chave | nº da portaria + data de publicação (identificador único) |
| categoria / acao | ASV, OUTORGA ou ASV+OUTORGA / verbo do Art. 1º (Conceder, Autorizar, Renovar, Transferir…) |
| tipo_outorga | Poço (captação subterrânea), Captação superficial, Barramento, Lançamento de efluentes, Transferência ou Alteração |
| portaria_num, data_portaria, data_publicacao | identificação do ato |
| processo | nº do processo INEMA, usado para buscar a cópia no SEIA |
| requerente, tipo_pessoa | titular (PF/PJ). CPFs mascarados no texto |
| municipio, municipios_citados, oeste | município do empreendimento e indicação de Oeste Baiano |
| finalidade | finalidade declarada (irrigação por pivô, ampliação de pecuária…) |
| area_ha | área de supressão (ASV) ou área irrigada (outorga) |
| volume_lenhoso_m3 | rendimento lenhoso estimado (ASV) |
| validade | prazo de validade |
| modalidade, bacia, vazao_m3_dia, horas_dia | dados da outorga (vazão somada de todos os pontos, convertida para m³/dia) |
| fazenda, coordenadas, n_pontos | imóvel e coordenadas publicadas |
| link_doe | link da edição no DOOL |
| texto | texto integral da portaria (CPFs mascarados) |

**Municípios considerados Oeste:** Barreiras, Luís Eduardo Magalhães, São Desidério, Formosa do Rio Preto, Riachão das Neves, Correntina, Jaborandi, Cocos, Santa Maria da Vitória, Baianópolis, Angical, Cotegipe, Wanderley, Cristópolis, Catolândia, Tabocas do Brejo Velho, Santana, Canápolis, Serra Dourada, Coribe, São Félix do Coribe, Mansidão, Santa Rita de Cássia, Brejolândia, Buritirama, Sítio do Mato, Serra do Ramalho, Muquém do São Francisco, Barra e Ibotirama.

## Limitações

- Os campos são extraídos automaticamente do texto da portaria. Portarias com redação fora do padrão podem ficar com campos em branco, mas o `texto` integral e o `link_doe` estão sempre lá para conferência.
- O DOE publica só o resumo do ato. Estudos, mapas e condicionantes completos ficam no processo no SEIA.

## Como atualizar

1. Abra https://dool.egba.ba.gov.br. O site só responde a conexões do Brasil.
2. No console da página, cole o conteúdo de `coletor/coletor_doe.js` e rode:
   `await ECO.rodar('AAAA-MM-DD', 'AAAA-MM-DD'); ECO.baixar();`
3. Copie os `doe_inema_AAAA.json` baixados para `dados/brutos/` e rode `python scripts/processar.py`.

## Cópias dos processos (SEIA)

`coletor/coletor_seia.js` roda na consulta pública do SEIA (logado, HTTPS). Para cada processo da lista (`dados/oeste/lista_processos_seia.json`), ele gera uma ficha com os atos e a lista de documentos. Quando a pasta local é conectada, baixa também os PDFs para `E:\Downloads\processos\<processo>\`. O progresso fica salvo no navegador, então dá para parar e retomar.
