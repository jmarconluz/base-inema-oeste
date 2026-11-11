// Aba "bomba": baixa a fila de processos do SEIA (IndexedDB 'eco_fila') em lotes.
// O app só deixa baixar vários arquivos seguidos logo depois que a aba é (re)carregada; por isso o Claude:
//   1) recarrega a aba bomba;  2) eval(localStorage.getItem('eco_bomba')); await BOMBA.disparar()
//   3) copia os lotes SEIA_lote_*.zip do C: para o E: (drenar.py);  4) BOMBA.confirmar(lote, itens, bytes)
window.BOMBA = (function () {
  const fila = () => new Promise((res, rej) => { const r = indexedDB.open('eco_fila', 1); r.onupgradeneeded = () => r.result.createObjectStore('q'); r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error); });
  async function todos() {
    const db = await fila();
    const v = await new Promise((res, rej) => { const q = db.transaction('q').objectStore('q').getAll(); q.onsuccess = () => res(q.result); q.onerror = () => rej(q.error); });
    db.close(); return v;
  }
  async function apagar(nomes) {
    const db = await fila();
    await new Promise((res, rej) => { const t = db.transaction('q', 'readwrite'); const st = t.objectStore('q'); for (const n of nomes) st.delete(n); t.oncomplete = res; t.onerror = () => rej(t.error); });
    db.close();
  }
  const CRC = (() => { const t = new Uint32Array(256); for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
  function crc32(u8) { let c = 0xFFFFFFFF; for (let i = 0; i < u8.length; i++) c = CRC[(c ^ u8[i]) & 0xFF] ^ (c >>> 8); return (c ^ 0xFFFFFFFF) >>> 0; }
  function zip(entradas) {
    const enc = new TextEncoder(); const partes = [], central = []; let off = 0;
    for (const e of entradas) {
      const nome = enc.encode(e.nome), dados = e.dados, crc = crc32(dados);
      const lh = new DataView(new ArrayBuffer(30));
      lh.setUint32(0, 0x04034b50, true); lh.setUint16(4, 20, true); lh.setUint16(6, 0x0800, true);
      lh.setUint32(14, crc, true); lh.setUint32(18, dados.length, true); lh.setUint32(22, dados.length, true); lh.setUint16(26, nome.length, true);
      partes.push(lh.buffer, nome, dados);
      const ch = new DataView(new ArrayBuffer(46));
      ch.setUint32(0, 0x02014b50, true); ch.setUint16(4, 20, true); ch.setUint16(6, 20, true); ch.setUint16(8, 0x0800, true);
      ch.setUint32(16, crc, true); ch.setUint32(20, dados.length, true); ch.setUint32(24, dados.length, true); ch.setUint16(28, nome.length, true); ch.setUint32(42, off, true);
      central.push(ch.buffer, nome); off += 30 + nome.length + dados.length;
    }
    const tc = central.reduce((s, b) => s + (b.byteLength || b.length), 0);
    const fim = new DataView(new ArrayBuffer(22));
    fim.setUint32(0, 0x06054b50, true); fim.setUint16(8, entradas.length, true); fim.setUint16(10, entradas.length, true); fim.setUint32(12, tc, true); fim.setUint32(16, off, true);
    return new Blob([...partes, ...central, fim.buffer], { type: 'application/zip' });
  }
  function baixar(blob, nome) { const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = nome; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 600000); }

  // Monta até `maxLotes` lotes de até `maxTam` bytes com os itens da fila ainda não disparados (ou disparados há > 20 min).
  async function disparar(maxLotes = 3, maxTam = 2.4e8) {
    const ag = Date.now();
    const its = (await todos()).filter(x => { const d = Number(localStorage.getItem('eco_disp:' + x.nome) || 0); return !d || ag - d > 20 * 60000; }).sort((a, b) => a.ts - b.ts);
    // empacota em ordem de chegada, encaixando itens menores onde ainda couber (menos lotes = menos downloads)
    const grupos = [], tams = [];
    for (const x of its) {
      let k = tams.findIndex(t => t + x.tam <= maxTam);
      if (k < 0) { if (grupos.length >= maxLotes) continue; grupos.push([]); tams.push(0); k = grupos.length - 1; }
      grupos[k].push(x); tams[k] += x.tam;
    }
    const blobs = [];
    for (let k = 0; k < grupos.length; k++) {
      const ent = []; for (const x of grupos[k]) ent.push({ nome: x.nome, dados: new Uint8Array(await x.blob.arrayBuffer()) });
      const nome = 'SEIA_lote_' + ag + '_' + (k + 1) + '.zip'; const b = zip(ent);
      blobs.push({ nome, b, itens: grupos[k].map(x => x.nome) });
    }
    const out = [];
    for (const l of blobs) {
      baixar(l.b, l.nome);
      localStorage.setItem('eco_lote:' + l.nome, JSON.stringify({ itens: l.itens, tam: l.b.size, ts: ag }));
      for (const n of l.itens) localStorage.setItem('eco_disp:' + n, String(ag));
      out.push({ nome: l.nome, tam: l.b.size, n: l.itens.length });
    }
    return out;
  }
  // Lote copiado para o E:: tira da fila os itens gravados e soma os bytes drenados.
  async function confirmar(lote, itensOk, bytes) {
    await apagar(itensOk);
    for (const n of itensOk) localStorage.removeItem('eco_disp:' + n);
    localStorage.removeItem('eco_lote:' + lote);
    localStorage.setItem('eco_drenado', String(Number(localStorage.getItem('eco_drenado') || 0) + bytes));
    return status();
  }
  // Lote que não apareceu no C:: libera os itens para o próximo disparo.
  function falhou(lote) {
    const l = JSON.parse(localStorage.getItem('eco_lote:' + lote) || '{"itens":[]}');
    for (const n of l.itens) localStorage.removeItem('eco_disp:' + n);
    localStorage.removeItem('eco_lote:' + lote);
  }
  function lotes() { return Object.keys(localStorage).filter(k => k.startsWith('eco_lote:')).map(k => Object.assign({ nome: k.slice(9) }, JSON.parse(localStorage.getItem(k)))); }
  async function status() {
    const v = await todos();
    return { fila: v.length, fila_mb: Math.round(v.reduce((s, x) => s + x.tam, 0) / 1e6), lotes_pendentes: lotes().length,
      baixados: Object.keys(localStorage).filter(k => k.startsWith('eco_dl:')).length };
  }
  return { disparar, confirmar, falhou, lotes, status, todos };
})();
