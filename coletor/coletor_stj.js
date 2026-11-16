// Coletor de acórdãos do STJ a partir do PORTAL DE DADOS ABERTOS do STJ (canal oficial para coleta em volume;
// a pesquisa scon.stj.jus.br tem verificação contra robôs e NÃO deve ser usada para coleta automática).
// Rodar numa aba aberta em https://dadosabertos.web.stj.jus.br/
// Uso:
//   await STJ.colher()                    // espelhos de acórdãos mensais (JSON, de jun/2022 em diante) das turmas e
//                                         // seções de Direito Público; guarda só os ambientais/sancionadores
//   await STJ.colher(undefined, '20261001') // atualização: só os arquivos mensais a partir dessa data
//   await STJ.historico(pacote)           // acervo anterior a mai/2022 (arquivo ZIP inicial de cada pacote)
//   await STJ.temas()                     // precedentes qualificados (repetitivos) ambientais
//   await STJ.preparar(); STJ.parte(0)... // envelopes {chave:'stj', parte, partes, n, dados, pad}
//   (depois: python scripts/decodificar_partes.py /tmp/pacotes && python scripts/incorporar_stj.py /tmp/pacotes/stj.json)
window.STJ = {
  PACOTES: ['espelhos-de-acordaos-primeira-turma', 'espelhos-de-acordaos-segunda-turma',
    'espelhos-de-acordaos-primeira-secao', 'espelhos-de-acordaos-corte-especial'],
  // normas cuja citação no espelho torna o acórdão relevante (código usado pelo STJ nas referências legislativas)
  NORMAS: ['LEI:009605', 'DEC:006514', 'DEL:006514', 'DEC:003179', 'DEL:003179', 'LEI:009873', 'LEI:012651',
    'LEI:004771', 'LCP:000140', 'LEI:006938'],
  AMB: /ambient|florest|ibama|icmbio|desmat|supress[ãa]o de vegeta|reserva legal|preserva[çc][ãa]o permanente|unidade de conserva|recursos h[íi]dricos|fauna|flora|polui/i,
  SANC: /multa|infra[çc][ãa]o|auto de|embargo|interdi|san[çc][ãa]o|prescri|poder de pol[íi]cia|termo de (ajustamento|compromisso)|licen[çc]|responsabilidade administrativa/i,
  store: new Map(),
  log: [],
  async recursos(pacote) {
    const j = await (await fetch('/api/3/action/package_show?id=' + pacote)).json();
    return j.result.resources.map(r => ({ nome: r.name, url: r.url.replace(/^https?:\/\/[^/]+/, ''), formato: r.format, tamanho: r.size }));
  },
  refs(x) { return (x.referenciasLegislativas || []).map(r => r.replace(/\s+/g, ' ').trim()); },
  motivo(x) {
    const refs = this.refs(x).join(' | ');
    if (this.NORMAS.some(n => refs.includes(n))) return 'norma';
    if (/LEG:EST/.test(refs) && /UF:BA|BAHIA/i.test(refs) && this.AMB.test([x.ementa, x.teseJuridica].join(' '))) return 'norma_ba';
    const t = [x.ementa, x.teseJuridica, x.termosAuxiliares, x.informacoesComplementares].join(' ');
    if (this.AMB.test(t) && this.SANC.test(t)) return 'ementa';
    return null;
  },
  curto(s, n) { s = (s || '').replace(/[ \t]*\n[ \t]*/g, ' ').replace(/\s{2,}/g, ' ').trim(); return s.length > n ? s.slice(0, n) + '…' : s; },
  guardar(x, origem) {
    const m = this.motivo(x); if (!m) return false;
    const id = String(x.id || x.numeroRegistro + '-' + x.dataDecisao);
    if (this.store.has(id)) return false;
    this.store.set(id, {
      id, registro: x.numeroRegistro, classe: x.siglaClasse, numero: x.numeroProcesso, descricao_classe: x.descricaoClasse,
      orgao: x.nomeOrgaoJulgador, relator: x.ministroRelator, data_decisao: x.dataDecisao,
      publicacao: this.curto(x.dataPublicacao, 60), ementa: this.curto(x.ementa, 6000),
      tese: this.curto(x.teseJuridica, 2000), tema: x.tema || null, termos: this.curto(x.termosAuxiliares, 600),
      info: this.curto(x.informacoesComplementares, 1500), jurisprudencia_citada: this.curto(x.jurisprudenciaCitada, 800),
      normas: this.refs(x), motivo: m, origem
    });
    return true;
  },
  // Arquivos mensais (JSON). desde = 'AAAAMMDD' (opcional) compara com o nome do arquivo.
  async colher(pacotes = this.PACOTES, desde = '') {
    for (const p of pacotes) {
      const rs = (await this.recursos(p)).filter(r => /^\d{8}\.json$/i.test(r.nome) && r.nome.slice(0, 8) >= desde);
      let lidos = 0, novos = 0, docs = 0;
      for (const r of rs) {
        try {
          const arr = await (await fetch(r.url)).json();
          docs += arr.length;
          for (const x of arr) if (this.guardar(x, p + '/' + r.nome)) novos++;
          lidos++;
        } catch (e) { this.log.push({ pacote: p, arquivo: r.nome, erro: String(e) }); }
      }
      this.log.push({ pacote: p, arquivos: rs.length, lidos, documentos: docs, guardados: novos });
    }
    return { acervo: this.store.size, log: this.log.slice(-pacotes.length) };
  },
  // Acervo anterior a mai/2022: o pacote traz um ZIP inicial com arquivos JSON. Lê o diretório central do ZIP e
  // descompacta entrada por entrada (DecompressionStream 'deflate-raw').
  async historico(pacote) {
    const zipRes = (await this.recursos(pacote)).find(r => /\.zip$/i.test(r.nome) || /zip/i.test(r.formato));
    if (!zipRes) return { pacote, erro: 'sem ZIP' };
    const buf = new Uint8Array(await (await fetch(zipRes.url)).arrayBuffer());
    const dv = new DataView(buf.buffer);
    let eocd = -1;
    for (let i = buf.length - 22; i >= Math.max(0, buf.length - 70000); i--) if (dv.getUint32(i, true) === 0x06054b50) { eocd = i; break; }
    if (eocd < 0) return { pacote, erro: 'ZIP sem diretório central' };
    let off = dv.getUint32(eocd + 16, true); const total = dv.getUint16(eocd + 10, true);
    let novos = 0, docs = 0, entradas = 0; const erros = [];
    for (let k = 0; k < total; k++) {
      const metodo = dv.getUint16(off + 10, true), csize = dv.getUint32(off + 20, true);
      const nlen = dv.getUint16(off + 28, true), xlen = dv.getUint16(off + 30, true), clen = dv.getUint16(off + 32, true);
      const lho = dv.getUint32(off + 42, true);
      const nome = new TextDecoder().decode(buf.subarray(off + 46, off + 46 + nlen));
      off += 46 + nlen + xlen + clen;
      if (!/\.json$/i.test(nome)) continue;
      const ini = lho + 30 + dv.getUint16(lho + 26, true) + dv.getUint16(lho + 28, true);
      const dados = buf.subarray(ini, ini + csize);
      try {
        const txt = metodo === 0 ? new TextDecoder().decode(dados)
          : await new Response(new Blob([dados]).stream().pipeThrough(new DecompressionStream('deflate-raw'))).text();
        const arr = JSON.parse(txt); docs += arr.length; entradas++;
        for (const x of arr) if (this.guardar(x, pacote + '/' + zipRes.nome + ':' + nome)) novos++;
      } catch (e) { erros.push(nome + ': ' + e); }
    }
    const r = { pacote, zip: zipRes.nome, entradas, documentos: docs, guardados: novos, erros: erros.slice(0, 5) };
    this.log.push(r); return r;
  },
  // Precedentes qualificados (temas repetitivos etc.): exporta o CSV oficial INTEIRO. Os campos têm quebras de
  // linha dentro das aspas, então filtrar linha a linha aqui quebrava os registros (16/11/2026); a seleção dos
  // temas ambientais é feita em Python (scripts/incorporar_stj.py, csv.DictReader + AMB_TEMA).
  async temas() {
    const rs = await this.recursos('precedentes-qualificados');
    const t = rs.filter(r => /^temas\.csv$/i.test(r.nome)).pop();
    const txt = await (await fetch(t.url)).text();
    this.temasCsv = txt;
    return { url: t.url, chars: txt.length, cabecalho: txt.split(/\r?\n/, 1)[0].slice(0, 300) };
  },
  async preparar(chave = 'stj') {
    const obj = { acordaos: [...this.store.values()], temas_csv: this.temasCsv || null, log: this.log };
    const gz = await new Response(new Blob([JSON.stringify(obj)]).stream().pipeThrough(new CompressionStream('gzip'))).arrayBuffer();
    const u8 = new Uint8Array(gz); let bin = '';
    for (let i = 0; i < u8.length; i += 0x8000) bin += String.fromCharCode.apply(null, u8.subarray(i, i + 0x8000));
    this.b64 = btoa(bin); this.chave = chave; this.n = obj.acordaos.length;
    return { chave, n: this.n, partes: Math.ceil(this.b64.length / 180000) || 1 };
  },
  parte(i) {
    const d = this.b64.slice(i * 180000, (i + 1) * 180000);
    return { chave: this.chave, parte: i, partes: Math.ceil(this.b64.length / 180000) || 1, dados: d, pad: '#'.repeat(Math.max(0, 120000 - d.length)) };
  }
};
