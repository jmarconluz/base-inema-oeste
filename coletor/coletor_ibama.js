// Coletor dos dados abertos do IBAMA (autos de infração e termos de embargo).
// Rodar numa aba aberta em https://stibamadadosabertosprd.blob.core.windows.net/dados-abertos?restype=container&comp=list
// Uso: await IB.rodar(1977); await EMB.rodar(); await PK.preparar(); PK.parte('ibama_autos_ba', 0) ...
window.ZIP = {
  async rng(url, a, b) { const r = await fetch(url, { headers: { Range: `bytes=${a}-${b}` } }); return new Uint8Array(await r.arrayBuffer()); },
  async listar(url) {
    const h = await fetch(url, { method: 'HEAD' }); const tam = +h.headers.get('content-length');
    const tail = await this.rng(url, Math.max(0, tam - 70000), tam - 1); const dv = new DataView(tail.buffer);
    let e = -1; for (let i = tail.length - 22; i >= 0; i--) if (dv.getUint32(i, true) === 0x06054b50) { e = i; break; }
    let n = dv.getUint16(e + 10, true), cdSize = dv.getUint32(e + 12, true), cdOff = dv.getUint32(e + 16, true);
    const cd = await this.rng(url, cdOff, cdOff + cdSize - 1); const dc = new DataView(cd.buffer);
    const ents = []; let p = 0;
    for (let k = 0; k < n; k++) {
      const met = dc.getUint16(p + 10, true), csz = dc.getUint32(p + 20, true), usz = dc.getUint32(p + 24, true);
      const fl = dc.getUint16(p + 28, true), xl = dc.getUint16(p + 30, true), cl = dc.getUint16(p + 32, true), off = dc.getUint32(p + 42, true);
      ents.push({ nome: new TextDecoder().decode(cd.slice(p + 46, p + 46 + fl)), met, csz, usz, off }); p += 46 + fl + xl + cl;
    }
    return { tam, ents };
  },
  async dados(url, ent) {
    const lh = await this.rng(url, ent.off, ent.off + 29); const dv = new DataView(lh.buffer);
    const ini = ent.off + 30 + dv.getUint16(26, true) + dv.getUint16(28, true);
    const r = await fetch(url, { headers: { Range: `bytes=${ini}-${ini + ent.csz - 1}` } });
    return r.body.pipeThrough(new DecompressionStream('deflate-raw'));
  }
};
function parseLinha(l) { if (l.indexOf('"') < 0) return l.split(';'); const out = []; let f = '', q = false; for (let i = 0; i < l.length; i++) { const c = l[i]; if (q) { if (c === '"') { if (l[i + 1] === '"') { f += '"'; i++; } else q = false; } else f += c; } else if (c === '"') q = true; else if (c === ';') { out.push(f); f = ''; } else f += c; } out.push(f); return out; }
async function linhas(stream, proc) {
  const rd = stream.pipeThrough(new TextDecoderStream('utf-8')).getReader(); let resto = '', pend = '';
  while (true) {
    const { value, done } = await rd.read(); if (done) break;
    const ls = (resto + value).split('\n'); resto = ls.pop();
    for (let l of ls) { if (l.endsWith('\r')) l = l.slice(0, -1); pend = pend ? pend + '\n' + l : l; if (((pend.match(/"/g) || []).length % 2) === 0) { proc(pend); pend = ''; } }
  }
  if (resto) pend = pend ? pend + '\n' + resto : resto; if (pend) proc(pend);
}
window.IB = {
  st: { fase: 'parado', linhas: 0, ba: 0, erros: [] }, agg: {}, ba: [],
  KEEP: ['SEQ_AUTO_INFRACAO', 'DES_STATUS_FORMULARIO', 'DS_SIT_AUTO_AIE', 'SIT_CANCELADO', 'NUM_AUTO_INFRACAO', 'SER_AUTO_INFRACAO', 'TIPO_AUTO', 'TIPO_MULTA', 'VAL_AUTO_INFRACAO', 'GRAVIDADE_INFRACAO', 'MOTIVACAO_CONDUTA', 'EFEITO_MEIO_AMBIENTE', 'DES_AUTO_INFRACAO', 'DAT_HORA_AUTO_INFRACAO', 'FORMA_ENTREGA', 'DAT_CIENCIA_AUTUACAO', 'DT_FATO_INFRACIONAL', 'MUNICIPIO', 'UF', 'NU_PROCESSO_FORMATADO', 'DES_INFRACAO', 'TIPO_INFRACAO', 'TP_PESSOA_INFRATOR', 'NOME_INFRATOR', 'CPF_CNPJ_INFRATOR', 'QT_AREA', 'CLASSIFICACAO_AREA', 'NUM_LONGITUDE_AUTO', 'NUM_LATITUDE_AUTO', 'DES_LOCAL_INFRACAO', 'DS_BIOMAS_ATINGIDOS', 'OPERACAO', 'SOLICITACAO_RECURSO', 'DS_ENQUADRAMENTO_ADMINISTRATIVO', 'DS_ENQUADRAMENTO_NAO_ADMINISTRATIVO', 'CD_TERMOS_EMBARGOS', 'FUNDAMENTACAO_MULTA'],
  async rodar(desde = 1977, uf = 'BA') {
    const url = '/dados-abertos/dados/SIFISC/auto_infracao/auto_infracao/auto_infracao_csv.zip';
    this.st.fase = 'rodando'; const lst = await ZIP.listar(url);
    for (const e of lst.ents) {
      const a = +(e.nome.match(/\d{4}/) || [0])[0]; if (a < desde) continue; let idx = null;
      try {
        await linhas(await ZIP.dados(url, e), (linha) => {
          const r = parseLinha(linha); if (!idx) { idx = Object.fromEntries(r.map((c, i) => [c, i])); return; }
          this.st.linhas++; const u = r[idx.UF] || '?'; const ano = (r[idx.DAT_HORA_AUTO_INFRACAO] || '').slice(0, 4) || String(a);
          const k = [u, ano, r[idx.DES_STATUS_FORMULARIO] || '', r[idx.SIT_CANCELADO] || '', r[idx.TIPO_INFRACAO] || ''].join('|');
          const v = parseFloat((r[idx.VAL_AUTO_INFRACAO] || '0').replace(/\./g, '').replace(',', '.')) || 0;
          const g = this.agg[k] || (this.agg[k] = [0, 0]); g[0]++; g[1] += v;
          if (u === uf) { this.ba.push(this.KEEP.map(c => { let x = r[idx[c]] || ''; if (c === 'CPF_CNPJ_INFRATOR' && /^\d{3}\.\d{3}\.\d{3}-\d{2}$/.test(x)) x = '***.***.***-**'; if (c === 'FUNDAMENTACAO_MULTA') x = x.slice(0, 600); return x; })); this.st.ba++; }
        });
      } catch (err) { this.st.erros.push(e.nome + ': ' + err.message); }
    }
    this.st.fase = 'fim'; return this.st;
  }
};
window.EMB = {
  st: { fase: 'parado', linhas: 0, ba: 0 }, agg: {}, ba: [], cab: null,
  async rodar(uf = 'BA') {
    this.st.fase = 'rodando'; let idx = null;
    const r = await fetch('/dados-abertos/dados/TERMOS_DE_EMBARGO/TERMO_EMBARGO/termo_de_embargo.csv');
    await linhas(r.body, (linha) => {
      const c = parseLinha(linha); if (!idx) { this.cab = c; idx = Object.fromEntries(c.map((x, i) => [x, i])); return; }
      this.st.linhas++; const u = c[idx.UF] || '?';
      const k = [u, (c[idx.DAT_EMBARGO] || '').slice(0, 4), c[idx.DES_STATUS_FORMULARIO] || '', c[idx.SIT_DESEMBARGO] || ''].join('|');
      const area = parseFloat((c[idx.QTD_AREA_EMBARGADA] || '0').replace(/\./g, '').replace(',', '.')) || 0;
      const g = this.agg[k] || (this.agg[k] = [0, 0]); g[0]++; g[1] += area;
      if (u === uf) { if (/^\d{11}$/.test(c[idx.CPF_CNPJ_EMBARGADO] || '')) c[idx.CPF_CNPJ_EMBARGADO] = '***********'; this.ba.push(c); this.st.ba++; }
    });
    this.st.fase = 'fim'; return this.st;
  }
};
window.PK = {
  pacotes: {},
  async gz(obj) { const gz = await new Response(new Blob([JSON.stringify(obj)]).stream().pipeThrough(new CompressionStream('gzip'))).arrayBuffer(); const u8 = new Uint8Array(gz); let bin = ''; for (let i = 0; i < u8.length; i += 0x8000) bin += String.fromCharCode.apply(null, u8.subarray(i, i + 0x8000)); return btoa(bin); },
  async preparar() {
    this.pacotes.ibama_autos_ba = await this.gz({ cab: IB.KEEP, linhas: IB.ba });
    this.pacotes.ibama_agg = await this.gz({ chave: 'UF|ANO|STATUS|SIT_CANCELADO|TIPO_INFRACAO', agg: IB.agg });
    this.pacotes.ibama_embargos_ba = await this.gz({ cab: EMB.cab, linhas: EMB.ba });
    this.pacotes.ibama_embargos_agg = await this.gz({ chave: 'UF|ANO|STATUS|SIT_DESEMBARGO', agg: EMB.agg });
    return Object.fromEntries(Object.entries(this.pacotes).map(([k, v]) => [k, Math.ceil(v.length / 180000)]));
  },
  // cada parte vai com enchimento para ultrapassar o limite de exibição e ser gravada em arquivo
  parte(nome, i) { const d = this.pacotes[nome].slice(i * 180000, (i + 1) * 180000); return { tipo: 'pk', nome, i, partes: Math.ceil(this.pacotes[nome].length / 180000), dados: d, pad: '#'.repeat(Math.max(0, 120000 - d.length)) }; }
};
