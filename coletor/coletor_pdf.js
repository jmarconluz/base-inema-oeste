// Exportador de PDFs públicos (pautas da CT Recursal, resoluções do CEPRAM, normas) do navegador embutido para o
// ambiente de nuvem, em envelopes {chave, parte, partes, n, dados, pad} lidos por scripts/decodificar_partes.py.
// Rodar numa aba aberta na MESMA origem dos PDFs (ex.: https://www.ba.gov.br/meioambiente/404/pautas-da-camara-tecnica-recursal
// ou https://gestor.meioambiente.ba.gov.br/Consultas/ConsultaPublicacao/).
// Uso:
//   PDF.links()                                   // PDFs linkados na página atual ([{texto, url}])
//   await PDF.pacote(urls, 'pdf_ct_pautas_2021')  // baixa e empacota (gzip + base64); devolve {partes, bytes}
//   PDF.parte(0), PDF.parte(1) ...                // um envelope por chamada (480 mil caracteres: o canal corta acima de ~500 mil)
//   (depois: python scripts/decodificar_partes.py /tmp/pacotes <arquivos salvos>  →  /tmp/pacotes/<chave>.json
//    com [{id, res, pdfs: [{url, bytes, b64}]}]; grave os PDFs e rode pdftotext ou scripts/extrair_pautas_ct.py)
window.PDF = {
  P: 480000,
  links() {
    return [...new Set([...document.querySelectorAll('a')].map(a => a.href).filter(h => /\.pdf(\?|#|$)/i.test(h)))]
      .map(url => ({ texto: decodeURIComponent(url.split('/').pop()), url }));
  },
  b64(u8) { let s = ''; for (let i = 0; i < u8.length; i += 0x8000) s += String.fromCharCode.apply(null, u8.subarray(i, i + 0x8000)); return btoa(s); },
  async pacote(urls, chave) {
    const pdfs = [], erros = [];
    for (const url of [...new Set(urls)]) {
      try { const r = await fetch(url); if (!r.ok) throw new Error('HTTP ' + r.status); const b = new Uint8Array(await r.arrayBuffer()); pdfs.push({ url, bytes: b.length, b64: this.b64(b) }); }
      catch (e) { erros.push({ url, erro: String(e) }); }
    }
    const json = JSON.stringify([{ id: chave, res: chave, pdfs }]);
    const gz = new Uint8Array(await new Response(new Blob([json]).stream().pipeThrough(new CompressionStream('gzip'))).arrayBuffer());
    this.dados = this.b64(gz); this.chave = chave; this.n = pdfs.length;
    return { chave, n: pdfs.length, bytes: pdfs.reduce((s, p) => s + p.bytes, 0), partes: Math.ceil(this.dados.length / this.P), erros };
  },
  parte(i) {
    const d = this.dados.slice(i * this.P, (i + 1) * this.P);
    return { chave: this.chave, parte: i, partes: Math.ceil(this.dados.length / this.P), n: this.n, dados: d, pad: '#'.repeat(Math.max(0, 120000 - d.length)) };
  }
};
