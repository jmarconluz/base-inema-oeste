// Coletor de jurisprudência do TJBA (API GraphQL pública do portal jurisprudencia.tjba.jus.br).
// Rodar numa aba aberta em https://jurisprudencia.tjba.jus.br/
// Uso:
//   await TJ.colher('"INEMA"');                 // todas as decisões do termo (busca entre aspas = expressão exata;
//                                               // sem aspas o portal usa OU entre as palavras)
//   await TJ.novas('2026-09-01');               // atualização: só as decisões publicadas desde a data, em TJ.TERMOS
//   await TJ.preparar(); TJ.parte(0) ...        // exporta o acervo da aba em envelopes {chave, parte, partes, n, dados, pad}
//   (depois: python scripts/decodificar_partes.py /tmp/pacotes && python scripts/incorporar_tjba.py /tmp/pacotes/tjba.json)
// ATENÇÃO: pageNumber da API começa em 0 (a página 1 é a SEGUNDA). Versões antigas deste coletor começavam em 1
// e perdiam as decisões mais recentes de cada termo.
window.TJ = {
  store: new Map(),
  TERMOS: ['"INEMA"', '"multa ambiental"', '"IBAMA"', '"CEPRAM"', '"10.431/2006"', '"Lei 10.431"', '"14.024/2012"',
    '"Decreto 14.024"', '"Lei 12.209"', '"12.209/2011"', '"Lei 9.605"', '"Decreto 6.514"', '"Secretaria do Meio Ambiente"',
    '"SEMA"', '"infração ambiental"', '"auto de infração ambiental"', '"embargo ambiental"'],
  CAMPOS: 'dataPublicacao relator { nome } orgaoJulgador { nome } classe { descricao } tipoDecisao ementa conteudo hash numeroProcesso',
  async busca(assunto, page = 0, n = 10, campos = 'dataPublicacao relator { nome } orgaoJulgador { nome } classe { descricao } tipoDecisao ementa hash numeroProcesso') {
    const query = 'query filter($decisaoFilter: DecisaoFilter!,$pageNumber: Int!,$itemsPerPage: Int!) { filter(decisaoFilter: $decisaoFilter,pageNumber: $pageNumber,itemsPerPage: $itemsPerPage) { decisoes { ' + campos + ' } pageCount itemCount } }';
    const variables = { decisaoFilter: { assunto, segundoGrau: true, turmasRecursais: false, tipoAcordaos: true, tipoDecisoesMonocraticas: true, ordenadoPor: 'dataPublicacao' }, pageNumber: page, itemsPerPage: n };
    let ult;
    for (let k = 0; k < 4; k++) {
      try {
        const r = await fetch('https://jurisprudenciaws.tjba.jus.br/graphql', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query, variables }) });
        const j = await r.json(); if (j.data) return j.data.filter; ult = JSON.stringify(j).slice(0, 200);
      } catch (e) { ult = e.message; }
      await new Promise(r => setTimeout(r, 1500 * (k + 1)));
    }
    throw new Error('TJBA sem resposta: ' + ult);
  },
  txt(h) { const d = new DOMParser().parseFromString(h || '', 'text/html'); d.querySelectorAll('p,br,div,li,tr').forEach(e => e.append('\n')); return (d.body ? d.body.textContent : '').replace(/\u00a0/g, ' ').replace(/[ \t]+/g, ' ').replace(/ *\n[ \n]*/g, '\n').trim(); },
  KW: /prescri|nulidade|nulo|notifica|edital|12\.209|10\.431|14\.024|CEPRAM|auto de infra|responsabilidade administrativa|subjetiva|dolo|culpa|intranscend|bis in idem|compet[eê]ncia|Complementar 140|dupla visita|embargo|propor|razoab|motiva|contradit|ampla defesa|cerceamento|reduç|advert|conversão|termo de compromisso|dívida ativa|execução fiscal|CDA/i,
  trechos(t) { let s = ''; for (const p of t.split('\n').filter(p => p.length > 60 && this.KW.test(p))) { if (s.length + p.length > 6000) break; s += p + '\n'; } return s; },
  guardar(d, termo) {
    const ant = this.store.get(d.hash);
    if (ant) { if (!ant.termos.includes(termo)) ant.termos.push(termo); return false; }
    const t = this.txt(d.conteudo);
    this.store.set(d.hash, { hash: d.hash, processo: d.numeroProcesso, data: d.dataPublicacao, relator: d.relator && d.relator.nome, orgao: d.orgaoJulgador && d.orgaoJulgador.nome, classe: d.classe && d.classe.descricao, tipo: d.tipoDecisao, ementa: this.txt(d.ementa), trechos: this.trechos(t), chars_inteiro_teor: t.length, termos: [termo] });
    return true;
  },
  // Todas as decisões de um termo (páginas 0 .. pageCount-1).
  async colher(termo, max = 5000) {
    let page = 0, novos = 0, pages = 1;
    do {
      const r = await this.busca(termo, page, 50, this.CAMPOS);
      pages = r.pageCount;
      for (const d of r.decisoes) if (this.guardar(d, termo)) novos++;
      page++;
    } while (page < pages && novos < max);
    return { termo, novos, paginas: pages, acervo: this.store.size };
  },
  // Atualização: para cada termo, lê da decisão mais recente para trás até passar da data 'desde' (AAAA-MM-DD).
  async novas(desde, termos = this.TERMOS) {
    const out = [];
    for (const termo of termos) {
      let page = 0, pages = 1, novos = 0, parar = false;
      do {
        const r = await this.busca(termo, page, 50, this.CAMPOS);
        pages = r.pageCount;
        for (const d of r.decisoes) {
          if ((d.dataPublicacao || '') >= desde) { if (this.guardar(d, termo)) novos++; }
          else if (d.dataPublicacao) parar = true;
        }
        page++;
      } while (!parar && page < pages);
      out.push({ termo, novos, paginasLidas: page });
    }
    return { desde, termos: out, acervo: this.store.size };
  },
  async preparar(chave = 'tjba') {
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
// Inteiro teor: https://jurisprudenciaws.tjba.jus.br/inteiroTeor/<hash>
