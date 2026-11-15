# Atualizar os dados do IBAMA pelo navegador

O IBAMA guarda os arquivos em `https://stibamadadosabertosprd.blob.core.windows.net/dados-abertos/...`.
O servidor da nuvem do Claude não acessa esse endereço; o navegador do app acessa.

1. Abrir uma aba em `https://stibamadadosabertosprd.blob.core.windows.net/dados-abertos?restype=container&comp=list`
   (a página dá 404, mas serve para o navegador ficar "dentro" do site e poder baixar os arquivos dele).
2. Colar no console o código de `coletor/coletor_ibama.js` e rodar:
   ```js
   await IB.rodar(1977);   // autos de infração: lê os 50 CSVs anuais do zip, guarda BA inteiro e o resumo do Brasil
   await EMB.rodar();      // termos de embargo (CSV de ~214 MB): guarda BA inteiro e o resumo do Brasil
   await PK.preparar();    // compacta (gzip + base64) para transferir em partes de 180 mil caracteres
   PK.parte('ibama_autos_ba', 0) ... // uma chamada por parte
   ```
3. Juntar as partes e gravar com o trecho Python do commit "Dados do IBAMA" (função de decodificação
   igual a `scripts/juntar_partes_navegador.py`).

Endereços usados:
- Autos: `.../dados/SIFISC/auto_infracao/auto_infracao/auto_infracao_csv.zip` (um CSV por ano, `;`, UTF-8)
- Embargos: `.../dados/TERMOS_DE_EMBARGO/TERMO_EMBARGO/termo_de_embargo.csv`
- Outros conjuntos (enquadramento, coordenadas, anexos, notificações, apreensões, suspensões):
  ver `https://dadosabertos.ibama.gov.br/api/3/action/package_show?id=fiscalizacao-auto-de-infracao`
