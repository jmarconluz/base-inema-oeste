# Checklist: chegou um auto de infração, embargo ou interdição

Usar na ordem. Cada item aponta a tese correspondente em `teses_defesa.md`.

## 0. Identificar

- [ ] Órgão: INEMA (processo `AAAA-NNNNNN/TEC/AIxx-NNNN`), IBAMA (processo SEI `02xxx.xxxxxx/AAAA-xx`), ICMBio,
      município, ADAB?
- [ ] Tipo: multa (AIMU), multa diária, advertência (AIAD), interdição (AIIN), embargo (AIEM), apreensão (AIAP),
      demolição (AIDM), notificação (NOT).
- [ ] Data da infração, da lavratura, da ciência (como foi entregue: pessoal, AR, edital?).
- [ ] Valor, enquadramento (artigo citado), classificação (leve/grave/gravíssima; formal/material).
- [ ] Autuado é ME/EPP? É o atual dono? Quando comprou/arrendou?

## 1. Prazos (contar já)

| Ato | Bahia (INEMA) | IBAMA |
|---|---|---|
| Defesa | 20 dias da ciência (Lei 10.431, art. 192, I; Decreto 14.024, art. 259, I) | 20 dias (Decreto 6.514, art. 113) |
| Recurso | 20 dias ao CEPRAM, da notificação da decisão (art. 259, II) | 20 dias (art. 127) |
| Pagamento | 30 dias da notificação (art. 259, IV) | conforme notificação; 30% de desconto à vista |
| Edital | ciência considerada 5 dias após a publicação (art. 261, §2º) | conforme edital |

**ICMBio** (auto em unidade de conservação federal): rito da IN ICMBio nº 9/2023, compilada com a IN ICMBio nº 13/2026 —
defesa em 20 dias da ciência (art. 58), alegações finais em 10 dias (art. 87; mais 10 a pedido, §4º, incluído pela IN
13/2026), recurso em 20 dias (art. 91); pagamento à vista com 30% de desconto como solução legal (art. 49, §2º).
Conferido na página oficial do ICMBio em 21/11/2026; texto integral no acervo desde 23/11/2026
(`legislacao/federal/in_icmbio_09_2023.txt`; trechos em `legislacao/artigos_chave.md`). A IN Conjunta
MMA/IBAMA/ICMBio nº 1/2021 não é mais o rito: foi substituída pela IN IBAMA 19/2023 no IBAMA e pela IN ICMBio 9/2023 no
ICMBio (ver `PENDENCIAS.md`, item 11).

Contagem: exclui o dia do início, inclui o do fim; prorroga para o dia útil seguinte (Decreto 14.024, art. 259, §2º).
Defesa por e-mail é aceita, mas tem de ser validada em até 5 dias por protocolo ou correio com AR (art. 264, parágrafo único).
Defesa fora do prazo não é conhecida (art. 265, parágrafo único).

## 2. Prescrição (teses 1.1 a 1.4)

- [ ] Mais de 5 anos entre o conhecimento do fato pelo órgão e o auto?
- [ ] Mais de 5 anos + 180 dias entre o auto e a decisão final (Bahia, Lei 12.209, art. 109, §1º)?
- [ ] Processo parado mais de 3 anos (IBAMA)?
- [ ] Já está em dívida ativa/execução? Mais de 5 anos do fim do processo até a execução (Súmula 467)?

## 3. Nulidades (teses 2.x)

- [ ] Notificação: tentou pessoal → AR → edital? Edital saiu no DOE **e** no SEIA? Endereço certo estava no processo?
- [ ] Auto tem os 8 requisitos do art. 260 do Decreto 14.024 (fato claro, dispositivo, local/data/hora, penalidade e
      fundamento, assinatura, prazo de defesa)?
- [ ] Agente designado para fiscalizar?
- [ ] Infração material com relatório/laudo, fotos, coordenadas, área medida?
- [ ] ME/EPP: houve dupla visita? (exceto reincidência, fraude, embaraço, ocupação de APP)
- [ ] A decisão enfrentou a defesa? Negou prova sem motivo?

## 4. Autoria e culpa (teses 3.x)

- [ ] Quem fez? Terceiro, arrendatário, antigo dono, invasor, incêndio de fora?
- [ ] Data do desmate (laudo multitemporal) x data da compra/posse.
- [ ] Havia ASV/licença/outorga válida cobrindo a atividade?

## 5. Competência e duplicidade (teses 4.x)

- [ ] Quem licencia a atividade? (município, INEMA, IBAMA)
- [ ] Existe auto de outro órgão pelo mesmo fato? Já pago? (Lei 9.605, art. 76) — cruzar `multas/bahia_doe` x `multas/ibama`.

## 6. Código Florestal (teses 5.x)

- [ ] A supressão é anterior a 22/07/2008? Imóvel no CEFIR/CAR? Adesão ao PRA (Lei BA 13.597/2016)?
- [ ] RL suprimida respeitando a lei da época (art. 68)? Imóvel até 4 módulos fiscais (art. 67)?

## 7. Embargo/interdição (tese 6)

- [ ] O polígono embargado é maior que a área da infração? Mapa no QGIS separando.
- [ ] Dá para regularizar (licença, ASV, outorga, TC) e pedir desembargo?

## 8. Dosimetria (tese 7)

- [ ] O auto justificou o valor com os critérios do art. 249? Considerou atenuantes, porte, condição socioeconômica?
- [ ] Reincidência aplicada sem auto anterior confirmado em julgamento nos 3 anos?
- [ ] Cabe advertência (leve/grave) ou conversão em advertência?

## 9. Decidir a estratégia

1. Tese forte de prescrição ou nulidade → defesa/recurso pedindo anulação (sem assinar conversão).
2. Teses médias → defesa com pedido principal de anulação e **subsidiário** de redução/advertência.
3. Teses fracas e multa relevante → pedir **conversão no prazo de defesa** (maior desconto: 90/60/30%) ou parcelamento.
4. Embargo → pedido de desembargo/delimitação em paralelo (não esperar o julgamento do auto).
5. Cobrança já em execução → advogado: embargos à execução / exceção de pré-executividade (só matéria de direito).
6. Multa do **IBAMA** já em dívida ativa (inscrita até 01/06/2025, até R$ 97,2 mil, pessoa física, ME ou EPP) e sem tese
   forte → transação por adesão da AGU/PGF (até 50% de desconto à vista), **pedido até 30/11/2026** na plataforma
   Resolve Dívidas AGU; exige desistir de recursos e ações (teses, seção 8).

## 10. Documentos a juntar

Procuração (art. 266); documentos pessoais/CNPJ e enquadramento ME/EPP; matrícula, CCIR, CAR/CEFIR, licenças, ASV,
outorgas; contrato de compra/arrendamento; laudo multitemporal e mapas (QGIS, SIRGAS 2000); fotos com coordenadas;
cópia integral do processo administrativo (ver `acesso_processos.md`).
