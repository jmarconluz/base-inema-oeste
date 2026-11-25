// Coletor dos DIÁRIOS OFICIAIS MUNICIPAIS do Oeste da Bahia, por tema (nunca por nome de pessoa): desapropriação e
// utilidade pública, plano diretor, perímetro urbano, zoneamento e loteamento, IPTU/ITBI e código tributário,
// licenciamento e fiscalização ambiental municipal. Só usa a busca pública de cada plataforma, sem login nem captcha.
// Roda numa aba aberta no próprio site (os sites não liberam CORS):
//   * https://doem.org.br/ba/formosadoriopreto/pesquisar   (DOEM/IBDM: todos os municípios de DOM.DOEM, numa aba só)
//   * https://pmbarreiras.diariomtransparente.com.br/publicacoes   (Diário Mtransparente: o município do subdomínio)
// Uso:
//   await DOM.colher('2024-01-01');       // todos os termos de DOM.TERMOS, do ato mais recente para trás, até a data
//   await DOM.preparar(); DOM.parte(0)…   // envelopes {chave: 'diarios_<plataforma>', parte, partes, n, dados, pad}
//   (depois: python scripts/decodificar_partes.py /tmp/pacotes && python scripts/processar_diarios.py /tmp/pacotes/diarios_*.json)
// Cada registro é um ato (ou edição) achado por um ou mais termos: município, plataforma, edição, data, caderno, título,
// resumo e endereço oficial. O texto integral fica no PDF da edição: ler o PDF só dos atos que importam.
window.DOM = {
  store: new Map(),
  estado: { consultas: 0, erros: [], rodando: false, fim: null },
  TERMOS: ['desapropriação', 'utilidade pública', 'servidão administrativa', 'plano diretor', 'perímetro urbano', 'zoneamento',
    'uso e ocupação do solo', 'parcelamento do solo', 'loteamento', 'expansão urbana', 'IPTU', 'ITBI', 'código tributário',
    'planta genérica de valores', 'licença ambiental', 'código de meio ambiente', 'auto de infração ambiental',
    'supressão de vegetação', 'conselho municipal de meio ambiente', 'audiência pública', 'estrada vicinal'],
  DOEM: { formosadoriopreto: 'Formosa do Rio Preto', riachaodasneves: 'Riachão das Neves', correntina: 'Correntina',
    santaritadecassia: 'Santa Rita de Cássia', cotegipe: 'Cotegipe', cristopolis: 'Cristópolis' },
  MTRANSPARENTE: { pmbarreiras: 'Barreiras' },
  MESES: { janeiro: 1, fevereiro: 2, marco: 3, abril: 4, maio: 5, junho: 6, julho: 7, agosto: 8, setembro: 9, outubro: 10, novembro: 11, dezembro: 12 },
  PESSOAL: /REURB|Regulariza[çc][ãa]o Fundi[áa]ria de Interesse|aposentadoria|pens[ãa]o por morte|exonera|nomeia|licen[çc]a[- ]pr[êe]mio|licen[çc]a maternidade/i,
  sleep: ms => new Promise(r => setTimeout(r, ms)),
  plataforma() { return /doem\.org\.br$/.test(location.host) ? 'doem' : /diariomtransparente\.com\.br$/.test(location.host) ? 'mtransparente' : ''; },
  async html(u) {
    let ult;
    for (let k = 0; k < 4; k++) {
      try { const r = await fetch(u); if (!r.ok) throw new Error('HTTP ' + r.status); this.estado.consultas++; return await r.text(); }
      catch (e) { ult = e; await this.sleep(1500 * (k + 1)); }
    }
    throw new Error('falha ' + u + ' (' + (ult && ult.message) + ')');
  },
  limpo: s => String(s || '').replace(/\s+/g, ' ').trim(),
  dataExtenso(s) {
    const m = String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').match(/(\d{1,2})\s+de\s+([A-Za-z]+)\s+de\s+(\d{4})/i);
    const mes = m && this.MESES[m[2].toLowerCase()];
    return mes ? `${m[3]}-${String(mes).padStart(2, '0')}-${m[1].padStart(2, '0')}` : '';
  },
  dataBr(s) { const m = String(s).match(/(\d{2})\/(\d{2})\/(\d{4})/); return m ? `${m[3]}-${m[2]}-${m[1]}` : ''; },
  guardar(r, termo) {
    const k = [r.municipio, r.link, r.titulo].join('|');
    const ant = this.store.get(k);
    if (ant) { if (!ant.termos.includes(termo)) ant.termos.push(termo); return false; }
    this.store.set(k, Object.assign(r, { termos: [termo] }));
    return true;
  },
  // DOEM (IBDM): /ba/<slug>/pesquisar?keyword=…&page=N – busca no texto das edições, da mais recente para a mais antiga.
  async doem(slug, termo, desde, maxPag = 15) {
    let novos = 0;
    for (let p = 1; p <= maxPag; p++) {
      const d = new DOMParser().parseFromString(await this.html(`/ba/${slug}/pesquisar?keyword=${encodeURIComponent(termo)}&page=${p}`), 'text/html');
      const caixas = [...d.querySelectorAll('.search-results .box-diario')];
      if (!caixas.length) break;
      let dentro = 0;
      for (const c of caixas) {
        const h2 = this.limpo((c.querySelector('h2') || {}).textContent);
        const data = this.dataExtenso(this.limpo((c.querySelector('.data-diario') || {}).textContent));
        if (data && data < desde) continue;
        dentro++;
        const edicao = (h2.match(/Edi[çc][ãa]o\s+([\d.]+)/i) || [])[1] || '';
        for (const ul of c.querySelectorAll('ul.caderno-assuntos-list')) {
          const cad = c.querySelector(`[data-toggle="${ul.id}"]`);
          for (const a of ul.querySelectorAll('li a')) {
            const titulo = this.limpo(a.textContent);
            if (!titulo || this.PESSOAL.test(titulo)) continue;
            if (this.guardar({ municipio: this.DOEM[slug], plataforma: 'DOEM', edicao, data, caderno: this.limpo(cad && cad.textContent),
              titulo, resumo: '', link: a.getAttribute('href') }, termo)) novos++;
          }
        }
      }
      if (!dentro || !d.querySelector(`.pagination a[href*="page=${p + 1}"]`)) break;
      await this.sleep(300);
    }
    return novos;
  },
  // Diário Mtransparente: /publicacoes?palavrachave=…&pagina=N – busca no resumo (índice de atos) de cada edição.
  async mtransparente(termo, desde, maxPag = 10) {
    const sub = location.host.split('.')[0], mun = this.MTRANSPARENTE[sub] || sub;
    const semAcento = s => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
    let novos = 0;
    for (let p = 1; p <= maxPag; p++) {
      const d = new DOMParser().parseFromString(await this.html(`/publicacoes/?pagina=${p}&edicao=&palavrachave=${encodeURIComponent(termo)}&data_inicial=&data_final=&filtered=1`), 'text/html');
      const linhas = [...d.querySelectorAll('table.listing-table tbody tr')].filter(tr => tr.querySelector('a[href*="referencia"]'));
      if (!linhas.length) break;
      let dentro = 0;
      for (const tr of linhas) {
        const c = [...tr.querySelectorAll('.fake-table-data')].map(x => this.limpo(x.textContent));
        const data = this.dataBr(c[4] || '');
        if (data && data < desde) continue;
        dentro++;
        const ref = tr.querySelector('a[href*="referencia"]').getAttribute('href');
        const id = (ref.match(/referencia=(\d+)/) || [])[1];
        let atos = [];
        try {
          const h = await this.html('/_core/_ajax/resumo.php?id=' + id);
          const x = new DOMParser().parseFromString(h.replace(/<br\s*\/?>\s*<br\s*\/?>/gi, '\u0001').replace(/<br\s*\/?>/gi, ' '), 'text/html');
          atos = (x.body.textContent || '').split('\u0001').map(this.limpo).filter(Boolean);
        } catch (e) { this.estado.erros.push('resumo ' + id + ': ' + e.message); }
        const alvo = semAcento(termo);
        for (const ato of atos.filter(a => semAcento(a).includes(alvo) && !this.PESSOAL.test(a))) {
          if (this.guardar({ municipio: mun, plataforma: 'Diário Mtransparente', edicao: c[1] || '', data, caderno: (ato.match(/^([A-ZÀ-Ú][A-Za-zÀ-ú ]{2,30}?)(?:\s+N[º°o]|\s*:|\s+\d)/) || [])[1] || '',
            titulo: ato.slice(0, 400), resumo: '', link: location.origin + ref }, termo)) novos++;
        }
        await this.sleep(200);
      }
      if (!dentro || linhas.length < 10) break;
      await this.sleep(300);
    }
    return novos;
  },
  async colher(desde, termos = this.TERMOS) {
    const E = this.estado; E.rodando = true; E.erros = []; E.fim = null;
    const pl = this.plataforma(), out = [];
    if (!pl) { E.rodando = false; throw new Error('abra a aba em doem.org.br ou num subdomínio de diariomtransparente.com.br'); }
    for (const termo of termos) {
      if (pl === 'doem') {
        for (const slug of Object.keys(this.DOEM)) {
          try { out.push([slug, termo, await this.doem(slug, termo, desde)]); } catch (e) { E.erros.push(slug + ' / ' + termo + ': ' + e.message); }
          await this.sleep(300);
        }
      } else {
        try { out.push([location.host.split('.')[0], termo, await this.mtransparente(termo, desde)]); } catch (e) { E.erros.push(termo + ': ' + e.message); }
      }
    }
    E.rodando = false; E.fim = new Date().toISOString();
    return { desde, plataforma: pl, atos: this.store.size, consultas: E.consultas, erros: E.erros.slice(-8), por_busca: out.filter(x => x[2]) };
  },
  async preparar(chave = 'diarios_' + this.plataforma()) {
    const arr = [...this.store.values()].sort((a, b) => (b.data || '').localeCompare(a.data || '') || a.municipio.localeCompare(b.municipio));
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
