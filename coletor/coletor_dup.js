// Coletor de decretos estaduais de UTILIDADE PÚBLICA e INTERESSE SOCIAL para desapropriação, servidão administrativa
// ou ocupação (Bahia), pelo Legisla Bahia (Casa Civil): Pesquisa Avançada, categoria "Decretos Numerados", ementa
// "utilidade pública". Rodar numa aba aberta em https://www.legislabahia.ba.gov.br/ (o site só responde do Brasil e não
// libera CORS). Não pede login nem tem captcha.
// Uso:
//   await DUP.colher('2024-01-01');       // do decreto mais recente para trás, até a data (AAAA-MM-DD)
//   await DUP.preparar(); DUP.parte(0)…   // envelopes {chave: 'dup_ba', parte, partes, n, dados, pad}
//   (depois: python scripts/decodificar_partes.py /tmp/pacotes && python scripts/processar_dup.py /tmp/pacotes/dup_ba.json)
// Só entram os decretos cuja ementa fala em desapropriação, servidão, interesse social ou ocupação: "declara de utilidade
// pública a associação X" (título de entidade) fica de fora. O texto vai inteiro quando cita município do Oeste e
// cortado em 3.500 caracteres nos demais (o resto são vértices; o endereço oficial fica no registro).
window.DUP = {
  store: new Map(),
  estado: { paginas: 0, lidos: 0, erros: [], rodando: false, fim: null },
  MESES: { janeiro: 1, fevereiro: 2, marco: 3, abril: 4, maio: 5, junho: 6, julho: 7, agosto: 8, setembro: 9, outubro: 10, novembro: 11, dezembro: 12 },
  RE_FIM: /desapropria|servid[ãa]o|interesse social|ocupa[çc][ãa]o tempor[áa]ria|imiss[ãa]o/i,
  OESTE: /Barreiras|Lu[íi]s Eduardo Magalh[ãa]es|S[ãa]o Desid[ée]rio|Formosa do Rio Preto|Riach[ãa]o das Neves|Correntina|Jaborandi|Cocos|Santa Maria da Vit[óo]ria|Santa Rita de C[áa]ssia|Wanderley|Cotegipe|Baian[óo]polis|Mansid[ãa]o|Catol[âa]ndia|Angical|Crist[óo]polis|Brejol[âa]ndia|Muqu[ée]m d[oe] S[ãa]o Francisco|Tabocas do Brejo Velho|S[ãa]o F[ée]lix do Coribe|Coribe|Serra Dourada|Santana|Can[áa]polis|Serra do Ramalho|Ibotirama|Bom Jesus da Lapa|S[íi]tio do Mato|Buritirama|Barra\b/,
  sleep: ms => new Promise(r => setTimeout(r, ms)),
  async doc(u) {
    let ult;
    for (let k = 0; k < 4; k++) {
      try {
        const r = await fetch(u); if (!r.ok) throw new Error('HTTP ' + r.status);
        return new DOMParser().parseFromString(await r.text(), 'text/html');
      } catch (e) { ult = e; await this.sleep(1500 * (k + 1)); }
    }
    throw new Error('falha ' + u + ' (' + (ult && ult.message) + ')');
  },
  dataDe(titulo) {
    const m = String(titulo).normalize('NFD').replace(/[̀-ͯ]/g, '').match(/DE\s+(\d{1,2})[ºo]?\s+DE\s+([A-Za-z]+)\s+DE\s+(\d{4})/i);
    if (!m) return '';
    const mes = this.MESES[m[2].toLowerCase()];
    return mes ? `${m[3]}-${String(mes).padStart(2, '0')}-${m[1].padStart(2, '0')}` : '';
  },
  // Uma página da pesquisa (20 atos, do mais recente para o mais antigo).
  async pagina(p) {
    const d = await this.doc('/documentos?categoria%5B0%5D=2&ementa=' + encodeURIComponent('utilidade pública') + '&page=' + p);
    const out = [];
    for (const a of d.querySelectorAll('a[href^="/documentos/"]')) {
      const titulo = a.textContent.replace(/\s+/g, ' ').trim();
      if (!/^DECRETO/i.test(titulo)) continue;
      const tr = a.closest('tr') || a.parentElement;
      const cel = a.closest('td') || tr;
      const ementa = cel.textContent.replace(/\s+/g, ' ').trim().replace(titulo, '').trim();
      out.push({ titulo, ementa, url: a.getAttribute('href'), data: this.dataDe(titulo) });
    }
    return out;
  },
  async texto(u) {
    const d = await this.doc(u);
    d.querySelectorAll('script,style,strike,s,del,[style*="line-through"],header,footer,nav').forEach(e => e.remove());
    const main = d.querySelector('.field--name-body, .node__content, article, main, #content') || d.body;
    main.querySelectorAll('p,br,div,tr,h1,h2,h3,h4,li,table').forEach(e => e.append('\n'));
    return (main.textContent || '').replace(/ /g, ' ').replace(/[ \t]+/g, ' ').replace(/ *\n[ \n]*/g, '\n').trim();
  },
  async colher(desde, maxPaginas = 200) {
    const E = this.estado; E.rodando = true; E.erros = []; E.fim = null;
    let antigas = 0;
    for (let p = 0; p < maxPaginas && antigas < 2; p++) {
      let linhas;
      try { linhas = await this.pagina(p); } catch (e) { E.erros.push('página ' + p + ': ' + e.message); break; }
      E.paginas = p + 1;
      if (!linhas.length) break;
      let novas = 0;
      for (const r of linhas) {
        if (r.data && r.data < desde) continue;
        novas++;
        if (!this.RE_FIM.test(r.ementa) || this.store.has(r.url)) continue;
        try {
          const t = await this.texto(r.url);
          const oeste = this.OESTE.test(t);
          this.store.set(r.url, { numero: (r.titulo.match(/N[ºo°]\s*([\d.]+)/i) || [])[1] || '', data: r.data, titulo: r.titulo, ementa: r.ementa,
            url: 'https://www.legislabahia.ba.gov.br' + r.url, oeste_no_texto: oeste, chars_original: t.length, texto: oeste ? t.slice(0, 40000) : t.slice(0, 3500) });
          E.lidos++;
        } catch (e) { E.erros.push(r.url + ': ' + e.message); }
        await this.sleep(250);
      }
      antigas = novas ? 0 : antigas + 1;
    }
    E.rodando = false; E.fim = new Date().toISOString();
    return { desde, paginas: E.paginas, decretos: this.store.size, erros: E.erros.slice(-5) };
  },
  async preparar(chave = 'dup_ba') {
    const arr = [...this.store.values()].sort((a, b) => (b.data || '').localeCompare(a.data || ''));
    const gz = await new Response(new Blob([JSON.stringify(arr)]).stream().pipeThrough(new CompressionStream('gzip'))).arrayBuffer();
    const u8 = new Uint8Array(gz); let bin = ''; for (let i = 0; i < u8.length; i += 0x8000) bin += String.fromCharCode.apply(null, u8.subarray(i, i + 0x8000));
    this.b64 = btoa(bin); this.chave = chave; this.n = arr.length;
    return { chave, n: arr.length, partes: Math.ceil(this.b64.length / 180000) || 1 };
  },
  parte(i) {
    const d = this.b64.slice(i * 180000, (i + 1) * 180000);
    return { chave: this.chave, parte: i, partes: Math.ceil(this.b64.length / 180000) || 1, n: this.n, dados: d, pad: '#'.repeat(Math.max(0, 120000 - d.length)) };
  }
};
