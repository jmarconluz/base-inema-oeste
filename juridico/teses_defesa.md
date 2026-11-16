# Teses de defesa contra autos de infração ambiental (foco Bahia/INEMA, com IBAMA)

Versão 1 — 14/11/2026. Cada tese traz: quando usar, base legal (texto integral em `legislacao/artigos_chave.md`),
precedentes conferidos, prova a juntar e uma nota de força:

- **Forte** – lei expressa + precedente de tribunal superior ou do próprio CEPRAM.
- **Média** – lei expressa, mas a aplicação depende dos fatos ou há divergência nos tribunais.
- **Argumentativa** – tese defensável, sem precedente firme localizado; usar como reforço.

> Aviso: material de apoio técnico, não é parecer jurídico. Na esfera administrativa o autuado pode ser representado
> por procurador com procuração (Decreto BA 14.024/2012, art. 266). Ação judicial (anulatória, mandado de segurança,
> embargos à execução) exige advogado.

Ordem prática de análise: **1) prazos → 2) prescrição → 3) nulidades do auto e da notificação → 4) autoria/culpa →
5) competência e duplicidade → 6) Código Florestal → 7) dosimetria → 8) saídas negociadas.**

---

## 1. Prescrição

### 1.1 Prescrição da pretensão punitiva — Bahia (INEMA) — Forte

- **Regra:** 5 anos contados do **conhecimento do fato** pela autoridade (Lei BA 12.209/2011, art. 109). A Lei 10.431/2006
  e o Decreto 14.024/2012 não têm regra própria de prescrição; o Decreto só manda observar "as regras relativas à
  prescrição" ao relavrar auto nulo (art. 263, §2º). A Lei 12.209 se aplica subsidiariamente aos processos com
  disciplina específica (arts. 1º, §2º, e 186).
- **Uso:** auto lavrado mais de 5 anos depois de o INEMA ter tido conhecimento do fato (vistoria anterior, denúncia,
  análise de processo de licença, alerta de satélite já disponível ao órgão).
- **Prova:** data da vistoria/denúncia/relatório que deu ciência ao órgão; histórico no SEIA; data do alerta (PRODES/DETER/MapBiomas).

### 1.2 Prescrição durante o processo — Bahia (INEMA) — Forte

- **Regra:** a publicação do ato que instaura o processo (o auto) **interrompe** a prescrição, que "volta a correr em sua
  integralidade" depois de 180 dias (Lei BA 12.209/2011, art. 109, §1º, c/c art. 108, §3º — prazo para decisão final
  de 180 dias, prorrogável uma vez). Na prática: se não houver decisão final em **5 anos + 180 dias** após a
  instauração (ou + 360 dias, se houve prorrogação justificada), a pretensão punitiva prescreve.
- **Por que funciona na Bahia:** o STJ, no Tema Repetitivo 1.294 (REsp 2.137.071, 1ª Seção), fixou que o Decreto
  20.910/1932 não serve para reconhecer prescrição intercorrente em processos estaduais e municipais, que dependem de
  lei local. A Bahia tem a lei local (12.209/2011, art. 109).
- **Precedentes no CEPRAM (base `multas/bahia_doe/cepram_recursos.csv`):** Res. 5.268/2025 (proc. 2012-012800/TEC/AIMU-0327)
  e Res. 5.283/2025 (proc. 2015-002131/TEC/AIMU-0179) — recurso deferido "reconhecendo a prescrição da pretensão
  punitiva com a extinção do respectivo processo".
- **Prova:** linha do tempo do processo (data da lavratura/publicação do auto, de cada despacho e da decisão final),
  tirada da cópia integral do processo.

### 1.3 Prescrição intercorrente de 3 anos — Média (IBAMA: Forte)

- **IBAMA:** processo parado mais de 3 anos aguardando julgamento ou despacho = prescrição intercorrente
  (Lei 9.873/1999, art. 1º, §1º; Decreto 6.514/2008, art. 21, §2º). O que interrompe: art. 22 do Decreto (só atos
  que impliquem instrução do processo).
- **INEMA:** o Decreto 14.024 manda aplicar subsidiariamente a Lei 9.605/1998 "e o seu Regulamento" (art. 253), isto é,
  o Decreto 6.514. Argumento possível, mas o Tema 1.294 do STJ exige lei local para prescrição intercorrente — por isso
  na Bahia a tese principal é a da Lei 12.209 (item 1.2) e esta fica como reforço.

### 1.4 Prescrição da cobrança (execução fiscal) — Forte

- **Súmula 467 do STJ:** a execução da multa ambiental prescreve em 5 anos contados do término do processo administrativo.
- **Uso:** CDA/execução ajuizada mais de 5 anos depois da decisão definitiva; ou execução parada (art. 40 da Lei 6.830/1980).
- A base `autos_editais.csv` marca as fases "Inscrição em dívida ativa (cobrança)" (1.731 registros) — conferir as datas.

## 2. Nulidades do auto e da notificação (Bahia)

### 2.1 Notificação irregular — Forte

- **Regra:** a ciência do auto segue esta ordem — pessoalmente; depois por correio com AR; **só então** por edital, e
  apenas se o autuado estiver em lugar incerto ou não sabido. O edital tem de sair no DOE **e** no SEIA
  (Decreto 14.024, art. 261 e §2º). A notificação deve descrever os fatos, indicar os dispositivos violados e ir com
  cópia do documento inaugural; é condição de validade do processo (Lei BA 12.209, art. 49, §§1º e 2º).
  É nulo o processo sem notificação ou sem abertura de prazo de defesa (Lei 12.209, art. 112, III).
- **Precedentes no CEPRAM:** Res. 5.325/2026, 5.327/2026 e 5.353/2026 — recurso deferido em parte "anulando os atos
  administrativos a partir da fase de notificação", com reabertura do prazo de defesa.
- **Prova:** AR devolvido/ausente, endereço correto constante do próprio processo ou do CEFIR/SEIA, edital publicado só
  no DOE.
- **Mostre o prejuízo concreto.** No Tema 1.329 (repetitivo, acórdão publicado, RE pendente), o STJ decidiu que, no
  processo federal do Decreto 6.514, a intimação por edital para alegações finais (redação original do art. 122,
  parágrafo único) só anula os atos seguintes se a parte demonstrar efetivo prejuízo para a defesa, inclusive antes do
  pagamento da multa. Por prudência, use o mesmo raciocínio no processo estadual: diga o que a defesa deixou de
  fazer (prova, alegação, desconto por pagamento) por causa do vício.

### 2.2 Auto sem os requisitos obrigatórios — Forte/Média

- **Regra:** o auto deve conter: autuado e endereço; o fato; o dispositivo infringido; local, data e hora; prazo para
  corrigir (se for o caso); penalidade e fundamento; assinatura; prazo de defesa e recurso (Decreto 14.024, art. 260).
- **Vício insanável** = quando corrigir o auto exige mudar o fato descrito → nulidade e arquivamento (art. 263, §1º).
  Erro só de enquadramento pode ser corrigido pela autoridade julgadora (art. 263, §3º), mas a correção tem de reabrir
  a defesa (art. 262, parágrafo único; Lei 12.209, art. 111).
- **Exemplos fortes:** fato descrito de forma genérica ("por causar degradação"), área ou local indefinidos, data da
  infração ausente, penalidade sem fundamento.

### 2.3 Agente sem designação para fiscalizar — Média

- Só lavra auto o servidor de órgão do SISNAMA/SEGREH **designado para atividades de fiscalização**
  (Lei BA 10.431, art. 176-B; Lei 9.605, art. 70, §1º). Pedir no processo a portaria de designação/credenciamento.

### 2.4 Falta de prova da infração material — Média

- Infração material é a que causa ou pode causar degradação (Decreto 14.024, art. 257, II); exige relatório de
  fiscalização, laudo, fotos, coordenadas. Auto de "degradação" sem laudo ou com área estimada sem medição é atacável.
- Modelos de recurso circulantes usam justamente a falta de laudo de constatação e de nexo causal.

### 2.5 Dupla visita para ME/EPP — Forte (com exceções)

- Na fiscalização ambiental de microempresa e empresa de pequeno porte, o auto só pode ser lavrado após a
  dupla visita, sob pena de **nulidade** (LC 123/2006, art. 55, §§1º e 6º). Exceções: reincidência, fraude,
  resistência ou embaraço, e ocupação irregular de APP e faixas de domínio (art. 55, §§1º e 9º).
- **Precedente:** STJ, REsp 1.952.610/RS, 1ª Turma, j. 07/11/2023 (dupla visita obrigatória para ME/EPP fora das
  hipóteses de risco — caso da ANP).

### 2.6 Decisão sem motivação / cerceamento de defesa — Média

- Lei 9.784/1999, arts. 2º, 3º, 38 e 50 (motivação, direito de produzir provas); Lei BA 12.209, art. 112, III, "c"
  (recusa imotivada de prova imprescindível gera nulidade). Homologação "padrão", que não enfrenta a defesa, é atacável.

## 3. Autoria, culpa e quem responde

### 3.1 Responsabilidade administrativa é subjetiva — Forte

- **STJ, EREsp 1.318.051/RJ, 1ª Seção, rel. Min. Mauro Campbell Marques, j. 08/05/2019:** a responsabilidade
  administrativa ambiental é **subjetiva** — exige dolo ou culpa e nexo causal (a civil é objetiva). A tese consta da
  edição 216 da "Jurisprudência em Teses" do STJ (Direito Ambiental IV, tese 5).
- **Uso:** dano causado por terceiro (invasor, vizinho, incêndio vindo de fora, prestador de serviço), ausência de
  conduta do autuado, cumprimento de licença/ASV válida.
- **Prova:** boletim de ocorrência, contrato com terceiro, imagens mostrando origem do fogo/desmate, ASV/licença.

### 3.2 Multa não passa para o comprador nem para o herdeiro — Forte

- A multa é pessoal (CF, art. 5º, XLV — intranscendência). O STJ (1ª Turma, 2024) afastou multa administrativa
  cobrada de herdeiro sem conduta própria; e a Turma já tratou de transferência da posse antes da infração
  (AgInt nos EDcl no REsp 1.967.742/PR, rel. Min. Regina Helena Costa, j. 24/10/2022, citado pelo TJMT).
- **Atenção:** a obrigação de **reparar o dano** acompanha o imóvel (Súmula 623 do STJ) — a multa não.
- **Uso direto na due diligence/corretagem:** o comprador herda o passivo de recuperação, não a multa.

- **Cuidado com a confusão entre multa e reparação:** a obrigação de **reparar** o dano ambiental acompanha o imóvel.
  No Tema 1.204 (repetitivo, trânsito em julgado), o STJ fixou que as obrigações ambientais são *propter rem* e podem
  ser exigidas do proprietário ou possuidor atual, de qualquer dos anteriores ou de ambos; fica isento o alienante
  cujo direito real cessou antes do dano, se não concorreu para ele. Já a **multa** é pessoal (3.1). Na compra de
  fazenda, a multa não passa, mas o passivo de recuperação passa.

### 3.3 Autuação só por imagem de satélite — Média

- Os tribunais aceitam imagem de satélite como prova da **materialidade**, inclusive sem vistoria (há decisões nesse
  sentido). Mas a **autoria** atribuída ao proprietário por presunção exige exame cuidadoso da negativa de autoria
  (TRF1 anulou autos e embargo baseados no mesmo polígono sem prova de autoria).
- **Defesa:** não atacar a tecnologia; atacar data, área e autoria com **laudo multitemporal** (série histórica
  PRODES/MapBiomas/Sentinel/Landsat): desmate anterior à posse, anterior a 22/07/2008, fora do imóvel, regeneração,
  área menor que a autuada. É exatamente o laudo de contestação de alertas que a Ecoplan já faz.

## 4. Competência e duplicidade

### 4.1 Órgão licenciador prevalece — Média

- Cabe ao órgão que licencia/autoriza a atividade lavrar o auto; os demais podem fiscalizar, mas prevalece o auto do
  licenciador (LC 140/2011, art. 17, caput e §3º; Decreto BA 14.024, art. 240 e §3º).
- **Limite fixado pelo STF (ADI 4.757/DF, Plenário, rel. Min. Rosa Weber, j. 12/12/2022):** a prevalência não impede a
  atuação supletiva de outro ente quando houver omissão ou insuficiência da fiscalização do órgão licenciador. O STJ
  (2025) aplicou esse entendimento para manter multa do IBAMA sobre atividade licenciada por outro órgão. Por isso a
  tese funciona melhor quando o licenciador **já agiu** sobre o mesmo fato (auto, notificação, TC) — aí a
  duplicidade fica clara.
- **Uso:** atividade licenciada pelo município (LC 140, art. 9º) autuada pelo INEMA, ou licenciada pelo INEMA autuada
  pelo IBAMA. Em agravo contra autos do INEMA, o TJBA entendeu que a alegação de competência exclusiva do município
  exige exame aprofundado da LC 140 e do Decreto 14.024 e negou a liminar — ou seja, a tese precisa vir com prova
  documental do licenciamento municipal desde o início (ver `jurisprudencia/tjba`).

### 4.2 Multa estadual substitui a federal — Forte

- "O pagamento de multa imposta pelos Estados, Municípios, Distrito Federal ou Territórios substitui a multa federal na
  mesma hipótese de incidência" (Lei 9.605/1998, art. 76). Cruzar a base do INEMA (`multas/bahia_doe`) com a do
  IBAMA (`multas/ibama`) pelo mesmo fato.
- LINDB, art. 22, §3º: sanções do mesmo fato devem ser consideradas na dosimetria das demais.

## 5. Código Florestal (desmatamento antigo, APP e Reserva Legal)

### 5.1 Infrações anteriores a 22/07/2008 e PRA — Forte

- Enquanto o prazo de adesão ao PRA estiver aberto e enquanto o termo de compromisso estiver sendo cumprido, o
  proprietário **não pode ser autuado** por infrações anteriores a 22/07/2008 relativas a supressão irregular em APP,
  Reserva Legal e uso restrito; com o termo assinado, as sanções ficam suspensas e, cumprido o termo, as multas são
  convertidas (Lei 12.651/2012, art. 59, §§4º e 5º). Na Bahia o PRA foi instituído pela Lei 13.597/2016.
- **STF, ADC 42 e ADIs 4.901/4.902/4.903/4.937:** dispositivos válidos, com interpretação conforme para que a
  prescrição fique interrompida durante o cumprimento do termo (não há "anistia" automática, há suspensão condicionada).
- **Prova:** laudo multitemporal comprovando que a supressão é anterior a 22/07/2008; CEFIR/CAR; adesão ao PRA.

### 5.2 Reserva Legal pela lei da época — Forte

- Quem suprimiu vegetação respeitando a lei vigente à época está dispensado de recompor a RL nos percentuais atuais
  (Lei 12.651/2012, art. 68). Imóveis de até 4 módulos fiscais: RL = vegetação existente em 22/07/2008 (art. 67).
- Área rural consolidada em APP: continuidade das atividades com recomposição parcial (art. 61-A).

### 5.3 Auto por não apresentação do PAD (PARA — Decreto BA 12.071/2010) — Forte no CEPRAM (fundamento a confirmar)

- **Quando usar:** auto de multa do INEMA "pela não apresentação do Projeto de Adequação e Regularização Ambiental
  (PAD) ... declarado no Termo de Adesão ao Plano Estadual de Adequação e Regularização Ambiental dos Imóveis Rurais
  (PARA), conforme determina o artigo 3º do Decreto Estadual nº 12.071/2010" — autos típicos do Oeste (2011–2015).
- **Precedente administrativo reiterado (conferido em 16/11/2026):** cruzando as resoluções do CEPRAM publicadas no
  DOE (`multas/bahia_doe`) com o fato gerador das pautas da CT Recursal (54ª a 85ª reunião, site da SEMA), há
  **65 decisões favoráveis — todas anulando a multa — e 5 desfavoráveis** nesse tipo de auto. As 5 desfavoráveis são de
  10/06/2022 (Res. 5.043, 5.045, 5.061, 5.073 e 5.075); desde 29/09/2023 (Res. 5.165) **todas** foram favoráveis,
  incluindo 44 em 07/07/2026, julgadas em bloco na seção "Processos Caso Plano Estadual de Adequação e Regularização
  Ambiental dos Imóveis Rurais – PARA" da pauta da 80ª reunião (Res. 5.370 a 5.415). Por município: Barreiras ≥ 16,
  Luís Eduardo Magalhães ≥ 12, Jaborandi 11, São Desidério 3, Formosa do Rio Preto e Correntina 1 cada. Lista completa
  em `cepram_votos_relator.md`; exemplo: Res. 5.400/2026 (Barreiras, auto 2013-011637/TEC/AIMU-0729, SEI
  046.0525.2025.0018521-16), DOE https://dool.egba.ba.gov.br/ver-html/22291/#e:22291.
- **Atenção:** as pautas e os registros de resultado **não trazem o fundamento** da anulação. Antes de afirmar o motivo
  na peça, pedir cópia do voto em um desses processos (SEI Bahia — `acesso_processos.md`). Na defesa, citar as
  resoluções como precedentes do próprio CEPRAM e pedir tratamento isonômico (Lei BA 12.209/2011, art. 3º — impessoalidade e segurança jurídica; LINDB, art. 30).
- **Reforço:** se o passivo for anterior a 22/07/2008 e houver CEFIR/PRA, somar a tese 5.1.

## 6. Embargo e interdição

- **Restrito à área da infração** — não alcança o resto da propriedade nem atividades não relacionadas
  (Decreto 6.514, art. 15-A). Pedir desembargo parcial com mapa (QGIS) separando a área.
- **Cessa com a regularização** — apresentando documentação que regularize a atividade (Decreto 6.514, art. 15-B);
  na Bahia o embargo/interdição temporários duram até o atendimento das exigências ou a assinatura de termo de
  compromisso (Decreto 14.024, arts. 278, §1º, e 282, §1º).
- **Cai com o auto** quando a autoria não é provada (precedente do TRF1 comentado acima).
- Termos de embargo antigos: a CT Recursal do CEPRAM decidiu diligenciar todos os processos de interdição, suspensão,
  demolição, embargo e apreensão com mais de 5 anos para o INEMA verificar a situação atual (pautas de 2026).

## 7. Dosimetria (quando não dá para anular, reduzir)

- Critérios obrigatórios: atenuantes/agravantes, gravidade, antecedentes, porte, escolaridade, infração formal ou
  material, **condição socioeconômica** (Decreto 14.024, art. 249; Lei 10.431, art. 187; Lei 9.605, art. 6º).
  Auto/decisão que não demonstra esses critérios → redução ou nulidade da multa.
- Atenuantes (Decreto 14.024, art. 250): reparação espontânea, primariedade, baixa escolaridade, colaboração,
  comunicação imediata.
- Reincidência só conta se o auto anterior foi **confirmado em julgamento** e nos 3 anos anteriores (art. 252).
- Infração leve ou grave admite **advertência** (Lei 10.431, art. 181; Decreto 14.024, art. 267), e a multa pode ser
  convertida em advertência pela autoridade julgadora (art. 269).
- **Precedentes no CEPRAM:** multa convertida em advertência — Res. 4.637/2018, 4.872/2021 e 5.193/2024 (autuado de
  Barreiras); reduções — 50% (Res. 5.176/2023 e 5.261/2025), 1/3 (Res. 5.179/2023), 70% (Res. 5.243/2024).
- O CEPRAM pode cancelar, reduzir ou trocar a penalidade (Lei 10.431, art. 192, §2º).

## 8. Saídas negociadas (quando a defesa é fraca)

| Medida | Bahia (INEMA/SEMA) | IBAMA |
|---|---|---|
| Conversão da multa em serviços ambientais | desconto de até **90%** (leve), **60%** (grave) ou **30%** (gravíssima) se pedida **no prazo de defesa**; cai 10 pontos após o recurso e mais 10 após a notificação para pagar (Decreto 14.024, art. 295-A) | desconto de 40% com a defesa ou 35% até as alegações finais (Decreto 6.514, art. 143, §2º) |
| Pagamento à vista | — | desconto de 30% (Decreto 6.514, art. 113, parágrafo único) |
| Parcelamento | até 12 meses (Decreto 14.024, art. 274, §1º); conversão indireta em até 36 parcelas (art. 295-B, §3º) | conforme regulamento |
| Termo de compromisso | suspende interdição/embargo e a exigibilidade da multa convertida (arts. 278, 282, 291, 298, §6º) | — |

**Cuidado:** assinar o termo de conversão implica renúncia a defesa e recursos sobre as multas convertidas
(Decreto 14.024, art. 298, §1º, I). Por isso: primeiro verificar prescrição e nulidades; se forem fracas, pedir a
conversão **dentro do prazo de defesa** para garantir o maior desconto.

## 9. Fase judicial (execução fiscal)

- Prescrição da cobrança (Súmula 467) e intercorrente na execução (art. 40 da Lei 6.830/1980).
- Ilegitimidade do comprador/herdeiro (item 3.2).
- O TJBA não admite discutir autoria e nexo causal por exceção de pré-executividade (precisa de embargos à execução com
  prova) — AI 8064602-72.2025.8.05.0000; e o depósito integral suspende a exigibilidade — AI 8001232-22.2025.8.05.0000.

## 10. Demora do órgão (licenças e outorgas)

- O TJBA tem concedido mandado de segurança contra a demora do INEMA/SEMA em processos administrativos
  (ex.: AI 8041184-08.2025.8.05.0000 — outorga; MS 8042430-10.2023.8.05.0000 — processo parado havia mais de 14 anos).
  Útil para a parte de licenciamento da Ecoplan.

---

## 11. Precedentes obrigatórios do STJ (temas repetitivos)

Conferidos em 15/11/2026 no CSV oficial de precedentes qualificados do Portal de Dados Abertos do STJ (lista completa em
`jurisprudencia/stj/temas_repetitivos_ambientais.csv`; acórdãos por tema em `jurisprudencia/stj/indice_temas.md`).
Repetitivo vincula juízes e tribunais (CPC, art. 927, III); para o órgão ambiental, serve de forte argumento.

| Tema | O que o STJ fixou (resumo fiel) | Situação | Uso na defesa |
|---|---|---|---|
| 146 | Cobrança da multa ambiental prescreve em 5 anos (Decreto 20.910/1932, por isonomia, à falta de regra específica) | Trânsito em julgado | A favor — multa estadual/municipal na execução (seção 1.4) |
| 147 | A prescrição da cobrança só começa com o vencimento do crédito sem pagamento | Trânsito em julgado | Define o termo inicial (seção 1.4) |
| 324 a 327 | Federal (Lei 9.873): 5 anos para constituir o crédito, contados da infração; se permanente ou continuada, de quando cessou; interrompem a notificação (inclusive por edital), ato inequívoco de apuração, decisão condenatória recorrível e tentativa de conciliação | Trânsito em julgado | IBAMA: conferir as datas no processo (seção 1.3) e se o órgão tratou a infração como permanente (prazo contado de quando cessou) |
| 328 | Federal: 3 anos para concluir o processo administrativo ("prescrição intercorrente") | Trânsito em julgado | A favor — IBAMA (seção 1.3) |
| 329 a 331 | Federal: a execução prescreve em 5 anos contados do fim do processo administrativo; lista as causas de interrupção | Trânsito em julgado | A favor — execução fiscal do IBAMA (seção 9) |
| 1.159 | A multa ambiental da Lei 9.605 **não depende** de advertência prévia | Trânsito em julgado | **Contra** — não alegue nulidade por falta de advertência; peça a conversão em advertência pelos arts. 267 e 269 do Decreto 14.024 (seção 7) |
| 1.204 | Obrigações ambientais (reparação) são *propter rem* | Trânsito em julgado | Contra o comprador quanto à reparação; não alcança a multa (seção 3.2) |
| 1.293 | Lei 9.873, art. 1º, §1º (intercorrente de 3 anos) vale para infração aduaneira não tributária | Trânsito em julgado | Reforça a aplicação ampla da intercorrente federal |
| 1.294 | O Decreto 20.910 não serve para reconhecer prescrição intercorrente em processos estaduais e municipais, nem por analogia | Acórdão publicado; RE pendente | Na Bahia, use a lei estadual (Lei 12.209, art. 109, §1º — seção 1.2), não o Decreto 20.910 |
| 1.329 | Decreto 6.514: edital para alegações finais só anula os atos seguintes se houver prejuízo efetivo comprovado | Acórdão publicado; RE pendente | Mostre o prejuízo concreto (seção 2.1) |
| 1.036 e 1.043 | Apreensão do instrumento da infração não depende de uso exclusivo ou habitual; o dono do veículo não tem direito a ser fiel depositário (cabe à Administração decidir) | Trânsito em julgado | Contra — em apreensão, discuta prova e proporcionalidade, não o uso habitual |
| 1.447 | Afetado: definir se a conversão da multa em medidas alternativas é decisão discricionária do órgão, com controle judicial só de legalidade | Afetado (sem tese) | Acompanhar — afeta pedidos judiciais de conversão (seção 8) |

## Pendências desta versão (próximas atualizações)

- Ler o voto/relatório dos processos com decisão favorável do CEPRAM (156) para registrar os **fundamentos** — a
  resolução publicada só traz o dispositivo. Feito em 16/11/2026 o que as pautas públicas permitem (fato gerador,
  pedido e voto proposto de 124 delas, em `cepram_votos_relator.md`); a motivação continua só no processo (SEI).
- Localizar acórdão do TJBA aplicando o art. 109 da Lei 12.209 a multa do INEMA (há decisão do TJBA calculando o prazo
  pelo art. 109, §1º, ainda não conferida no inteiro teor).
- Conferir número do acórdão do STJ (1ª Turma, 2024) sobre multa e herdeiro e do acórdão do TRF1 que anulou autos e
  embargo por falta de prova de autoria (fonte secundária: comentário publicado em comunidadeambiental.com.br).
- Jurisprudência do TRF1 (multas do IBAMA na Bahia) e do STJ por tema — coletar pelo navegador (SCON e portal do TRF1).
- Infração instantânea x permanente em desmatamento (marco inicial da prescrição) — pesquisar posição atual do STJ.
