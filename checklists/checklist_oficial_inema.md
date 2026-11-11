# Checklist oficial do INEMA – ASV e outorga (poço e superficial)

Fonte principal: **Portaria INEMA nº 11.292, de 13/02/2016** (versão consolidada publicada no site do INEMA), que define os documentos e estudos para os atos do INEMA. Ela continua listada como norma vigente na página "Normas Técnicas e Portarias" do INEMA (consulta de 11/11/2026).

Normas complementares usadas aqui:
- **IN INEMA nº 03, de 30/06/2022**: perfuração de poços (APPO), outorga e monitoramento no **aquífero Urucuia** (oeste da Bahia).
- **IN SEMA/INEMA nº 01, de 24/08/2021**: critérios para dados georreferenciados. **Revogou a Portaria IMA 13.950/2010**, que ainda é citada em vários formulários antigos do INEMA.
- **Portaria INEMA nº 22.181/2021**: medidores e monitoramento dos usos da água.
- **Portaria INEMA nº 22.078/2021**: Reserva Legal.

A coluna "% aprovados" vem do índice dos processos deferidos no SEIA (`checklist_inema_preliminar.md`). Ela mostra o que o INEMA aceitou na prática.

Os arquivos oficiais citados estão em `modelos_inema/` (repositório) e em `E:\Downloads\modelos_inema\`.

---

## 1. Documentos gerais (Anexo I, item 1) – valem para ASV e outorga

| Documento | Modelo / observação |
|---|---|
| Documentos do requerente: CNPJ e Inscrição Estadual (PJ), ou RG/CPF ou documento equivalente (PF); para órgão público, o ato de nomeação de quem assina | — |
| Comprovante de representação legal, com RG e CPF. Se houver procurador: procuração pública, ou particular com firma reconhecida, e os documentos do procurador | — |
| Comprovante de pagamento da remuneração (Anexo V do Decreto 14.024/2012) | Gerado no SEIA |
| Comprovante de regularidade da Reserva Legal, quando couber | Portaria 22.078/2021 |
| Cópia da licença ambiental anterior, quando couber | — |
| Registro no CEAPD (INEMA), quando couber | — |
| Inscrição no CEFIR (imóvel rural) | `cefir_seia/` |
| Documento de propriedade ou posse aceito pelo CEFIR: escritura com certidão de inteiro teor, título, contrato de compra e venda ou de promessa, formal de partilha, contrato de assentamento do INCRA, declaração dos confrontantes, entre outros | — |

## 2. Autorização de Supressão de Vegetação Nativa – ASV (Anexo III, item 5)

| Documento exigido | % aprovados | Modelo oficial |
|---|---|---|
| Requerimento de Atos Florestais | — | `florestal_asv/F-ATD-056-14_Requerimento_Atos_Florestais.doc` |
| Inventário Florestal (amostragem ou censo), conforme modelo do INEMA | 73% | `florestal_asv/Inventario_florestal_atualizado_22022016.pdf` e o TR `IN-ATD-002-00_Termo_de_Referncia_para_a_Elaborao_de_Inventrio_Florestal.pdf` |
| Estudo fitossociológico com estágio de regeneração (Res. CONAMA 05/1994), **só** para Mata Atlântica ou áreas do mapa da Lei 11.428/2006 | 78% | — (no oeste, Cerrado, em geral não se aplica; conferir o mapa da Lei da Mata Atlântica) |
| Declaração do aproveitamento socioeconômico e ambiental do produto/subproduto | 81% | `florestal_asv/F-ATD-079-00_Declarao_de_Aproveitamento_...doc` |
| Autorização de passagem por imóvel de terceiro, se couber | — | — |
| Escritura pública com certidão de inteiro teor | — | — |
| Anuência do proprietário/posseiro, se o empreendimento estiver em imóvel de terceiro | — | — |
| Estudo Ambiental para Supressão: (a) identificação (nome, área, local); (b) projeto técnico com ocupação econômica atual e projetada e viabilidade técnica e econômica; (c) cronograma e metodologia da supressão | 73% | Modelo próprio Ecoplan (a montar a partir dos aprovados) |
| Planta planimétrica georreferenciada, com tabela de coordenadas: ocupação atual e futura, vegetação nativa, área a suprimir, APP e Reserva Legal | 81% | Modelo QGIS (seção 5) |
| Memorial descritivo da poligonal de supressão em SIRGAS 2000 | 81% | — |
| Proposta de Educação Ambiental (Res. CEPRAM 4.610/2018 e Documento Técnico Orientador) | 81% | Documento Técnico Orientador (`modelos/`, site do INEMA) |
| Proposta de compensação (Mata Atlântica, estágio médio ou avançado), quando couber | 66% | — |

**Fauna (Anexo III, item 10)**: quando há supressão, os processos aprovados quase sempre trazem o **Plano de Salvamento de Fauna** (66%), o CTF dos profissionais e da consultoria, a carta de aceite da instituição que recebe o material biológico, a carta de aceite da área de soltura e a declaração do veterinário.

**Outros**: Relatório de Caracterização do Imóvel – RCI (`IN-ATD-001-00`), plantio compensatório (`licenciamento/F-ATD-082-00`), SINAFLOR (exigência federal para ASV), ART de cada responsável técnico.

## 3. Outorga – captação subterrânea (poço) (Anexo IV, item 1)

| Documento exigido | % aprovados | Modelo oficial |
|---|---|---|
| Requerimento de Outorga | — | `outorga/F-OUT-003-03_Requerimento_de_Outorga.doc` |
| Formulário de Caracterização do Empreendimento (FCE) | — | Gerado no SEIA |
| Memorial descritivo: justificativa, demandas com memória de cálculo, metodologia e parâmetros da vazão, sistema de recalque e projeto técnico da captação | 88% | Modelo próprio (a partir dos aprovados) |
| Relatório técnico com croqui do sistema de captação e distribuição | 88% | — |
| **APPO** – Autorização para Perfuração de Poço (poços perfurados após 08/10/2009) | 70% | Pedido próprio (Anexo IV, item 4) |
| **Declaração de Conformidade de Poço** (poços perfurados antes de 08/10/2009) | — | `outorga/F-OUT-018-01_Modelo_Declarao_de_Conformidade_de_Poo.doc` |
| Relatório de acompanhamento geológico: município, localidade, coordenadas, profundidade, NE/ND, vazão, aquífero, rocha, RT da perfuração, data, aspectos construtivos, uso, perfil litológico, **teste de bombeamento**, análise físico-química | 88% | — |
| Cessão de uso ou autorização de passagem, se houver uso de área de terceiro | — | — |

### Regras extras no aquífero Urucuia (IN INEMA 03/2022) – oeste da Bahia
- A perfuração deve ser acompanhada por geólogo ou engenheiro de minas, com ART (art. 8º). A empresa perfuradora precisa de cadastro no INEMA (art. 7º; formulário `outorga/F-OUT-001-02`).
- Não pode haver poço em APP nem em Reserva Legal aprovada, salvo utilidade pública, interesse social ou baixo impacto (art. 9º).
- Distância mínima entre poços de usuários diferentes, e também entre o poço e um rio perene ou intermitente (art. 12):

| Distância | Expectativa de captação |
|---|---|
| < 500 m | só dispensa (consumo humano e dessedentação) |
| 500–1.000 m | até 1.800 m³/dia |
| 1.000–1.500 m | até 3.600 m³/dia |
| 1.500–2.000 m | até 5.400 m³/dia |
| 2.000–2.500 m | até 7.200 m³/dia |
| > 2.500 m | até 9.000 m³/dia |

- Máximo de **9.000 m³/dia** por poço no SAU (art. 20). Para passar dos limites da tabela, é preciso estudo hidrogeológico com ART (art. 22).
- Vazão até **0,5 L/s** fica dispensada de outorga, salvo restrição na área. No abastecimento público rural, o limite é 1,5 L/s (art. 4º).
- Exige estudo hidrogeológico, teste de bombeamento e projeto que justifique a demanda (art. 16). O INEMA pode pedir perfilagem geofísica, análise química e teste de interferência (arts. 17–19).
- Piezômetro a 25–50 m do poço produtor, com medidor automático de nível (art. 23). A Ficha do Poço de Monitoramento vai no Relatório de Condicionantes, antes de pedir a outorga (art. 24).
- Medidor de vazão conforme Portaria 22.181/2021 (art. 26).
- O prazo da APPO é de 2 anos, prorrogável por mais 2 (PPV no SEIA), pedido com 90 dias de antecedência (arts. 28–29).

## 4. Outorga – captação superficial (Anexo IV, item 1)

| Documento exigido | Modelo oficial |
|---|---|
| Requerimento de Outorga e FCE | `outorga/F-OUT-003-03_Requerimento_de_Outorga.doc` |
| Memorial descritivo com demandas, memória de cálculo da vazão, sistema de recalque e projeto técnico da captação | — |
| Relatório técnico com croqui do sistema de captação e distribuição | — |
| Captação em barramento existente: Licença do barramento **ou** Declaração de Inexigibilidade | — |
| Captação em barramento existente: Outorga de construção do barramento **ou** Dispensa / Notificação de Comunicação | — |
| Cessão de uso ou autorização de passagem, se houver uso de área de terceiro | — |
| Rio de domínio federal (por exemplo, o São Francisco): a outorga é da **ANA**, não do INEMA | — |

Para irrigação, os processos aprovados trazem também o projeto agronômico, com balanço hídrico e dimensionamento hidráulico.

**Dispensa de outorga de captação (Anexo IV, item 5)**: FCE, justificativa técnica, projeto básico e Termo de Compromisso (`outorga/TERMO_DE_COMPROMISSO_PARA_DISPENSA_DE_OUTORGA...pdf`, `modelos/Dispensa_de_Outorga_-_MODELO.doc`), mais a APPO ou a Declaração de Conformidade, no caso de poço.

**Renovação**: pedido até 90 dias antes do vencimento, com a declaração `outorga/Declarao_para_fins_de_Renovao_da_Outorga.doc` (arts. 28–29 da Portaria 11.292).

## 5. Padrão dos mapas e plantas (IN SEMA/INEMA 01/2021)

- Sistema geodésico **SIRGAS 2000**. Plantas em UTM; no oeste, as zonas 23S (EPSG:31983) e 24S (EPSG:31984), divididas pelo meridiano 42° W.
- Vetores em **shapefile** ou geodatabase, **sem erros topológicos**: polígonos fechados, sem vértices sobrepostos, sem duplicidade.
- Vetorização com imagem de resolução compatível com a escala do mapa. Os dados devem ser generalizados conforme essa escala.
- Drone (RPA): seguir a Norma de Execução INCRA/DF nº 02/2018.
- Mapa com os elementos da cartografia sistemática e temática (título, legenda, escala, norte, grade de coordenadas, sistema de referência, fonte e data da imagem, responsável técnico), com precisão e legibilidade.
- Metadados no padrão da IDE-Bahia / CECAR.
- Para ASV e manejo, a planta mostra também as **coordenadas das parcelas do inventário florestal**.
