# Como obter a cópia integral dos processos de multa

Resposta curta: **sim, é possível**, mas o caminho depende de quem pede e de onde o processo está.
O DOE publica só o resumo (edital, homologação, decisão do CEPRAM). Votos, pareceres, relatórios de fiscalização e
mapas ficam no processo.

## Base legal do acesso

- **Lei 10.650/2003** — órgãos do SISNAMA devem dar acesso a documentos, expedientes e processos administrativos sobre
  matéria ambiental (art. 2º) e publicar no Diário Oficial as listas de **autos de infração e penalidades** (art. 4º, III).
- **LAI federal (Lei 12.527/2011)** e **LAI da Bahia (Lei 12.618/2012)**: qualquer pessoa pede, sem justificar
  (art. 8º da lei baiana exige só identificação e especificação); resposta em até 20 dias, prorrogáveis por mais 10
  (art. 9º, §§1º e 2º); serviço gratuito, salvo custo de reprodução (art. 10); recurso em 10 dias (art. 13) e, em
  última instância, ao Comitê Gestor de Acesso à Informação – CGAI (art. 14); não se nega informação necessária à tutela
  de direitos fundamentais (art. 16). Regulamento atual: Decreto BA 24.375/2026.
- **Autuado/representante:** direito de vista, cópia e de conhecer as decisões (Lei 9.784/1999, art. 3º, II, aplicada
  subsidiariamente; Lei BA 12.209/2011). Dados pessoais de terceiros podem vir tarjados (LGPD).

## Caminhos, do mais rápido ao mais formal

| Situação | Onde | Como |
|---|---|---|
| Processo de licença/outorga/ASV (INEMA, formato `AAAA.001.NNNNNN/INEMA/LIC-…`) | **SEIA – consulta pública** (`sistema.seia.ba.gov.br`, logado) | já em uso: `coletor/seia_worker.js` baixa os documentos |
| Processo de auto de infração do INEMA (`AAAA-NNNNNN/TEC/AIMU-…`) | SEIA (a testar) ou pedido ao INEMA | se não aparecer no SEIA: pedido de vista/cópia (autuado) ou LAI (terceiro) |
| Processos novos do Estado (formato SEI `NNN.NNNN.AAAA.NNNNNNN-DV`) | **SEI Bahia** — usuário externo em `portalseibahia.saeb.ba.gov.br` (Acesso Externo) | o cadastro é pessoal; o acesso a cada processo é liberado pelo órgão (integral ou parcial); peticionamento intercorrente permite juntar documentos com o nº do processo |
| Decisões do CEPRAM (CT Recursal) | **site da SEMA** (`ba.gov.br/meioambiente`) — pautas e atas em PDF; resoluções no DOE | pautas trazem tipo, valor, município, fato gerador, pedido, relator e histórico; base já coletada em `multas/bahia_doe/cepram_recursos.csv` |
| Qualquer processo estadual, como terceiro | **LAI** — Ouvidoria Geral do Estado (sistema TAG / Fala.BR-Bahia, link "Ouvidoria" em `ba.gov.br`) ou SIC do INEMA | modelo abaixo; pedir em lotes pequenos (10 a 20 processos) |
| Processo do IBAMA | **SEI-IBAMA** — Pesquisa Pública (`sei.ibama.gov.br`) e usuário externo; formulário de Pedido de Vista em Processo Administrativo; LAI pelo **Fala.BR** | o nº vem em `multas/ibama` (`NU_PROCESSO_FORMATADO`) |
| Ações judiciais | PJe do TJBA/TRF1 (consulta pública) e portal de jurisprudência (inteiro teor) | `juridico/jurisprudencia/tjba` traz o link do inteiro teor |

## Estratégia para a base de decisões favoráveis

1. A base já identifica **156 decisões favoráveis do CEPRAM** (anulação, redução, advertência, prescrição) com o nº do processo.
2. Pedir cópia **desses processos** primeiro (são os que mostram o argumento que venceu): relatório de fiscalização,
   defesa, parecer jurídico, voto do relator e resolução.
3. Em paralelo, baixar as pautas e atas da CT Recursal no site da SEMA (públicas).
4. Guardar cada processo em `E:\Downloads\processos\<processo>\` como já é feito com o SEIA, e registrar os
   fundamentos em `juridico/precedentes_cepram.md`.

## Modelo 1 — Pedido pela LAI (terceiro interessado)

> À Ouvidoria Geral do Estado da Bahia / Serviço de Informação ao Cidadão do INEMA
>
> [Nome], [CPF/CNPJ], [e-mail], com fundamento no art. 5º, XXXIII, da Constituição, na Lei 12.527/2011, na
> Lei Estadual 12.618/2012 (arts. 8º e 9º) e no art. 2º da Lei 10.650/2003, requer **cópia digital** dos seguintes
> documentos dos processos administrativos de auto de infração abaixo, já decididos e com resolução publicada no DOE:
> (a) auto de infração e relatório de fiscalização; (b) defesa e recurso; (c) pareceres técnicos e jurídicos;
> (d) decisão de 1ª instância; (e) voto do relator e resolução do CEPRAM.
>
> Processos: [lista de 10 a 20 números, ex.: 2012-012800/TEC/AIMU-0327; 2015-002131/TEC/AIMU-0179 …]
>
> Os dados pessoais de terceiros podem ser tarjados (LGPD). Requer o envio em formato digital (art. 9º, §5º).
> Caso algum documento seja sigiloso, requer a indicação do fundamento e o fornecimento da parte não sigilosa.

## Modelo 2 — Vista e cópia integral (autuado ou procurador)

> Ilmo(a). Sr(a). Diretor(a) Geral do Instituto do Meio Ambiente e Recursos Hídricos – INEMA
>
> [Autuado], [qualificação], por seu procurador [nome] (procuração anexa – Decreto 14.024/2012, art. 266), nos autos
> do processo [nº], requer **vista e cópia integral, em formato digital**, de todo o processo administrativo,
> incluindo relatório de fiscalização, fotos, coordenadas/polígonos, laudos, comprovantes de notificação (AR, editais
> no DOE e no SEIA), pareceres e decisões, com fundamento nos arts. 3º, II, da Lei 9.784/1999 e 49 da Lei Estadual
> 12.209/2011, e requer a **devolução do prazo de defesa/recurso** caso a cópia não seja entregue a tempo.

O formulário oficial do INEMA para retirada de cópia é o **F-ATD-071-00 – Requerimento para Retirada de Cópia de
Processo Administrativo** (texto em `modelos_inema/_texto/`).

## O que não dá para conseguir

- Documentos legalmente sigilosos (dados fiscais, segredo industrial) e dados pessoais sensíveis de terceiros.
- Cópia em massa de todos os processos de multa de 10 anos de uma vez: o pedido pode ser recusado como
  desproporcional. Por isso o caminho é por lotes, priorizando os processos com decisão favorável.
