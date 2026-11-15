// Coletor de jurisprudência do TJBA (API GraphQL pública do portal jurisprudencia.tjba.jus.br).
// Rodar numa aba aberta em https://jurisprudencia.tjba.jus.br/
// Uso: await TJ.colher('"INEMA"'); await TJ.colher('"multa ambiental"'); await TJ.preparar(); TJ.parte(0) ...
// Busca entre aspas = expressão exata (sem aspas o portal usa OU entre as palavras e devolve milhões de resultados).
window.TJ = {
  store: new Map(),
  async busca(assunto, page = 1, n = 10, campos = 'dataPublicacao relator { nome } orgaoJulgador { nome } classe { descricao } tipoDecisao ementa hash numeroProcesso') {
    const query = 'query filter($decisaoFilter: DecisaoFilter!,$pageNumber: Int!,$itemsPerPage: Int!) { filter(decisaoFilter: $decisaoFilter,pageNumber: $pageNumber,itemsPerPage: $itemsPerPage) { decisoes { ' + campos + ' } pageCount itemCount } }';
    const variables = { decisaoFilter: { assunto, segundoGrau: true, turmasRecursais: false, tipoAcordaos: true, tipoDecisoesMonocraticas: true, ordenadoPor: 'dataPublicacao' }, pageNumber: page, itemsPerPage: n };
    const r = await fetch('https://jurisprudenciaws.tjba.jus.br/graphql', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query, variables }) });
    const j = await r.json(); return j.data ? j.data.filter : j;
  },
  txt(h) { const d = new DOMParser().parseFromString(h || '', 'text/html'); d.querySelectorAll('p,br,div,li,tr').forEach(e => e.append('\n')); return (d.body ? d.body.textContent : '').replace(/ /g, ' ').replace(/[ \t]+/g, ' ').replace(/ *\n[ \n]*/g, '\n').trim(); },
  KW: /prescri|nulidade|nulo|notifica|edital|12\.209|10\.431|14\.024|CEPRAM|auto de infra|responsabilidade administrativa|subjetiva|dolo|culpa|intranscend|bis in idem|compet[eê]ncia|Complementar 140|dupla visita|embargo|propor|razoab|motiva|contradit|ampla defesa|cerceamento|reduç|advert|conversão|termo de compromisso|dívida ativa|execução fiscal|CDA/i,
  trechos(t) { let s = ''; for (const p of t.split('\n').filter(p => p.length > 60 && this.KW.test(p))) { if (s.length + p.length > 6000) break; s += p + '\n'; } return s; },
  async colher(termo, max = 3000) {
    let page = 1, novos = 0, pages = 1;
    do {
      const r = await this.busca(termo, page, 50, 'dataPublicacao relator { nome } orgaoJulgador { nome } classe { descricao } tipoDecisao ementa conteudo hash numeroProcesso');
      pages = r.pageCount;
      for (const d of r.decisoes) {
        const ant = this.store.get(d.hash); if (ant) { ant.termos.push(termo); continue; }
        const t = this.txt(d.conteudo);
        this.store.set(d.hash, { hash: d.hash, processo: d.numeroProcesso, data: d.dataPublicacao, relator: d.relator && d.relator.nome, orgao: d.orgaoJulgador && d.orgaoJulgador.nome, classe: d.classe && d.classe.descricao, tipo: d.tipoDecisao, ementa: this.txt(d.ementa), trechos: this.trechos(t), chars_inteiro_teor: t.length, termos: [termo] });
        novos++;
      }
      page++;
    } while (page <= pages && novos < max);
    return { termo, novos, paginas: pages, acervo: this.store.size };
  },
  async preparar() {
    const arr = [...this.store.values()].sort((a, b) => (b.data || '').localeCompare(a.data || ''));
    const gz = await new Response(new Blob([JSON.stringify(arr)]).stream().pipeThrough(new CompressionStream('gzip'))).arrayBuffer();
    const u8 = new Uint8Array(gz); let bin = ''; for (let i = 0; i < u8.length; i += 0x8000) bin += String.fromCharCode.apply(null, u8.subarray(i, i + 0x8000));
    this.b64 = btoa(bin); return { n: arr.length, partes: Math.ceil(this.b64.length / 180000) };
  },
  parte(i) { const d = this.b64.slice(i * 180000, (i + 1) * 180000); return { tipo: 'tjba', i, dados: d, pad: '#'.repeat(Math.max(0, 120000 - d.length)) }; }
};
// Inteiro teor: https://jurisprudenciaws.tjba.jus.br/inteiroTeor/<hash>
