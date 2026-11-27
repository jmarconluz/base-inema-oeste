// Coletor de publicações de FISCALIZAÇÃO AMBIENTAL no Diário Oficial do Estado da Bahia (DOOL/EGBA):
// autos de infração (multa, advertência, embargo, interdição...), notificações, homologações,
// decisões do CEPRAM sobre recursos, termos de compromisso e conversões de multa.
// Roda na página https://dool.egba.ba.gov.br (o site só responde a conexões do Brasil).
// Guarda o texto integral de cada matéria relevante no IndexedDB 'eco_multas' (sobrevive a recarga da aba).
//
// Uso (console da página do DOOL):
//   MUL.rodar('2016-11-14', '2026-11-14');      // coleta (da data mais recente para a mais antiga; pula datas já feitas)
//   MUL.rodar('2026-11-01', '2026-11-16', 3, true); // refaz o intervalo mesmo que já coletado (atualização semanal)
//   await MUL.status();                         // andamento
//   await MUL.exportar({ano: 2025, parte: 0});  // devolve o ano em JSON gzip+base64, em partes de 200 mil caracteres
//   await MUL.p({desde: '2026-11-08'}, 0);       // só as matérias publicadas a partir da data, ENXUTAS (só os trechos
//                                                // de fiscalização), em envelope {chave, parte, partes, n, dados, pad}
//                                                // com enchimento '#' até 120 mil caracteres: o resultado do
//                                                // javascript_tool fica grande e vai para arquivo, sem poluir a conversa.
//                                                // Depois: python scripts/decodificar_partes.py + scripts/incorporar_doe.py
// Para retomar depois de recarregar a aba: injete de novo este arquivo inteiro (ele é a versão de referência).
window.MUL = (function () {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const strip = h => h.replace(/<style[\s\S]*?<\/style>/gi, '').replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/(p|div|tr|li|h\d)>/gi, '\n').replace(/<[^>]+>/g, ' ').replace(/&nbsp;/g, ' ')
    .replace(/&quot;/g, '"').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&#(\d+);/g, (m, c) => String.fromCharCode(c)).replace(/\r/g, '').replace(/[ \t]+/g, ' ')
    .replace(/ *\n[ \n]*/g, '\n').trim();
  // Pastas do DOE que interessam (INEMA, SEMA, CEPRAM, CONERH, FERFA)
  const PASTA = /INEMA|Instituto do Meio Ambiente|Secretaria do Meio Ambiente|CEPRAM|Conselho Estadual d[eo] Meio Ambiente|Conselho Estadual de Recursos H[ií]dricos|CONERH|FERFA|Fundo Estadual de Recursos para o Meio Ambiente/i;
  const PULA_TITULO = /RHBAHIA|Integracao_RH/i;
  // Conteúdo de fiscalização / processo sancionador.
  // Desde 27/11/2026 também o termo de compromisso do INEMA com cláusula penal de multa (ex.: regularização da operação
  // de fazenda sem licença), que sai em matéria própria sem citar auto de infração e ficava de fora (visto no DOE de
  // 27/11/2026). O termo de compensação ambiental (TCCA, do licenciamento) não tem cláusula penal e continua fora.
  const RELEVANTE = /auto\s+de\s+infra[çc][ãa]o|TEC\s*\/\s*(?:AI[A-Z]{0,4}|NOT)\s*-|infra[çc][ãa]o\s+ambiental|homologad[oa]\s+o\s+auto|convers[ãa]o\s+d[ae]\s+multa|CEPRAM[\s\S]{0,400}recurso|recurso[\s\S]{0,400}CEPRAM|termo\s+de\s+embargo|interdi[çc][ãa]o\s+tempor[áa]ria|termo\s+de\s+compromisso[\s\S]{0,1500}?cl[áa]usula\s+penal/i;

  let db;
  function abrir() {
    if (db) return Promise.resolve(db);
    return new Promise((res, rej) => {
      const r = indexedDB.open('eco_multas', 1);
      r.onupgradeneeded = () => {
        const d = r.result;
        d.createObjectStore('materias', { keyPath: 'mid' });
        d.createObjectStore('datas', { keyPath: 'data' });
      };
      r.onsuccess = () => { db = r.result; res(db); };
      r.onerror = () => rej(r.error);
    });
  }
  async function put(store, obj) {
    const d = await abrir();
    return new Promise((res, rej) => {
      const tx = d.transaction(store, 'readwrite'); tx.objectStore(store).put(obj);
      tx.oncomplete = res; tx.onerror = () => rej(tx.error);
    });
  }
  async function all(store) {
    const d = await abrir();
    return new Promise((res, rej) => { const q = d.transaction(store).objectStore(store).getAll(); q.onsuccess = () => res(q.result); q.onerror = () => rej(q.error); });
  }
  async function keys(store) {
    const d = await abrir();
    return new Promise((res, rej) => { const q = d.transaction(store).objectStore(store).getAllKeys(); q.onsuccess = () => res(q.result); q.onerror = () => rej(q.error); });
  }
  async function getText(url) {
    let ult;
    for (let k = 0; k < 5; k++) {
      try { const r = await fetch(url); if (!r.ok) throw new Error('HTTP ' + r.status); return await r.text(); }
      catch (e) { ult = e; await sleep(2000 * (k + 1)); }
    }
    throw new Error('falha ' + url + ' (' + (ult && ult.message) + ')');
  }

  const state = { rodando: false, total: 0, feitas: 0, vistas: 0, relevantes: 0, erros: [], ultima: null, inicio: null, fim: null };

  async function processarData(d) {
    const j = JSON.parse(await getText('/apifront/portal/edicoes/edicoes_from_data/' + d));
    const eds = (j.itens || []).filter(i => /Estado da Bahia/i.test(i.tipo_edicao_nome || ''));
    let rel = 0, vistas = 0; const falhas = [];
    for (const ed of eds) {
      const h = await getText('/html/' + ed.id + '.html');
      const doc = new DOMParser().parseFromString(h, 'text/html');
      const lista = new Map();
      for (const f of doc.querySelectorAll('span.folder')) {
        const pasta = f.textContent.trim();
        if (!PASTA.test(pasta)) continue;
        for (const a of f.parentElement.querySelectorAll('a.linkMateria')) {
          const mid = a.getAttribute('data-materia-id');
          if (!mid || lista.has(mid)) continue;
          const ul = a.closest('ul');
          const fp = ul && ul.parentElement ? ul.parentElement.querySelector(':scope > span.folder') : null;
          lista.set(mid, { titulo: a.textContent.trim(), pasta: (fp ? fp.textContent.trim() : pasta) });
        }
      }
      for (const [mid, info] of lista) {
        if (PULA_TITULO.test(info.titulo)) continue;
        vistas++;
        let t;
        try { t = strip(await getText('/apifront/portal/edicoes/publicacoes_ver_conteudo/' + mid)); }
        catch (e) { falhas.push(mid); continue; }
        if (!RELEVANTE.test(t)) continue;
        rel++;
        await put('materias', { mid: String(mid), edicao_id: String(ed.id), data: d, pasta: info.pasta, titulo: info.titulo, texto: t });
      }
    }
    state.vistas += vistas; state.relevantes += rel;
    if (falhas.length) { state.erros.push(d + ': materias ' + falhas.join(',')); return false; }
    await put('datas', { data: d, edicoes: eds.length, vistas, relevantes: rel, em: new Date().toISOString() });
    return true;
  }

  // Coleta de um intervalo de datas (AAAA-MM-DD), da mais recente para a mais antiga.
  // forcar = true refaz também as datas já coletadas (útil na atualização semanal: pega edição que saiu atrasada
  // ou matéria publicada depois da primeira leitura do dia; as matérias são gravadas por id, sem duplicar).
  async function rodar(inicio, fim, workers = 3, forcar = false) {
    if (state.rodando) return 'já está rodando';
    state.rodando = true; state.inicio = new Date().toISOString(); state.fim = null; state.erros = [];
    try { navigator.locks.request('eco_vivo_multas', () => new Promise(() => { })); } catch (e) { }
    const feitas = new Set(await keys('datas'));
    const datas = [];
    for (let d = new Date(fim + 'T12:00:00'); d >= new Date(inicio + 'T12:00:00'); d.setDate(d.getDate() - 1)) {
      const s = d.toISOString().slice(0, 10);
      if (d.getDay() !== 0 && (forcar || !feitas.has(s))) datas.push(s);
    }
    state.total = datas.length; state.feitas = 0;
    let idx = 0;
    async function worker() {
      while (state.rodando && idx < datas.length) {
        const d = datas[idx++];
        try { await processarData(d); } catch (e) { state.erros.push(d + ': ' + e.message); }
        state.feitas++; state.ultima = d;
      }
    }
    await Promise.all(Array.from({ length: workers }, worker));
    state.rodando = false; state.fim = new Date().toISOString();
    return status();
  }
  function parar() { state.rodando = false; }

  async function status() {
    const ds = await keys('datas'); const ms = await keys('materias');
    return Object.assign({}, state, { erros: state.erros.slice(-15), nErros: state.erros.length, datasNoBanco: ds.length, materiasNoBanco: ms.length });
  }

  // Exporta as matérias (filtro opcional por ano) em JSON comprimido (gzip) e base64, em partes.
  async function exportar(op = {}) {
    const ano = op.ano ? String(op.ano) : null; const parte = op.parte || 0; const tam = op.tam || 200000;
    const chave = 'exp_' + (ano || 'tudo');
    window.__mulExp = window.__mulExp || {};
    if (!window.__mulExp[chave] || parte === 0) {
      const regs = (await all('materias')).filter(r => !ano || r.data.startsWith(ano))
        .sort((a, b) => (a.data + a.mid).localeCompare(b.data + b.mid));
      const gz = await new Response(new Blob([JSON.stringify(regs)]).stream().pipeThrough(new CompressionStream('gzip'))).arrayBuffer();
      const u8 = new Uint8Array(gz); let bin = '';
      for (let i = 0; i < u8.length; i += 0x8000) bin += String.fromCharCode.apply(null, u8.subarray(i, i + 0x8000));
      window.__mulExp[chave] = { b64: btoa(bin), n: regs.length };
    }
    const e = window.__mulExp[chave]; const partes = Math.ceil(e.b64.length / tam) || 1;
    return { ano, parte, partes, n: e.n, dados: e.b64.slice(parte * tam, (parte + 1) * tam) };
  }
  async function datas() { return (await all('datas')).sort((a, b) => a.data.localeCompare(b.data)); }

  // Mantém só os blocos da matéria que tratam de fiscalização (editais, portarias, resoluções, termos, extratos,
  // decisões e avisos que casam com RELEVANTE); os demais blocos viram '[...]'.
  function enxugar(t) {
    const partes = t.split(/\n(?=(?:EDITAL\s+DE\s+NOTIFICA|EDITAL\s*\n|PORTARIA\s*(?:INEMA\s*)?N|RESOLU[ÇC][ÃA]O|TERMO\s+DE\s+COMPROMISSO|EXTRATO|DECIS[ÃA]O|AVISO))/);
    return partes.filter(p => RELEVANTE.test(p)).join('\n[...]\n');
  }

  // Exporta as matérias ENXUTAS (filtros opcionais: ano 'AAAA' e/ou desde 'AAAA-MM-DD'), gzip+base64, em partes.
  async function exportarEnxuto(op = {}) {
    const ano = op.ano ? String(op.ano) : null; const desde = op.desde || null;
    const parte = op.parte || 0; const tam = op.tam || 200000;
    const chave = 'doe_enx_' + (ano || 'tudo') + (desde ? '_desde_' + desde : '');
    window.__mulExp = window.__mulExp || {};
    if (!window.__mulExp[chave] || parte === 0) {
      const sel = (await all('materias')).filter(r => (!ano || r.data.startsWith(ano)) && (!desde || r.data >= desde))
        .sort((a, b) => (a.data + a.mid).localeCompare(b.data + b.mid))
        .map(r => Object.assign({}, r, { texto: enxugar(r.texto), chars_original: r.texto.length }));
      const gz = await new Response(new Blob([JSON.stringify(sel)]).stream().pipeThrough(new CompressionStream('gzip'))).arrayBuffer();
      const u8 = new Uint8Array(gz); let bin = '';
      for (let i = 0; i < u8.length; i += 0x8000) bin += String.fromCharCode.apply(null, u8.subarray(i, i + 0x8000));
      window.__mulExp[chave] = { b64: btoa(bin), n: sel.length, chars: sel.reduce((s, r) => s + r.texto.length, 0),
        datas: [...new Set(sel.map(r => r.data))].sort() };
    }
    const e = window.__mulExp[chave]; const partes = Math.ceil(e.b64.length / tam) || 1;
    return { chave, ano, desde, parte, partes, n: e.n, chars: e.chars, datas: e.datas.length,
      primeira: e.datas[0] || null, ultima: e.datas[e.datas.length - 1] || null, dados: e.b64.slice(parte * tam, (parte + 1) * tam) };
  }

  // Igual a exportarEnxuto, com enchimento '#' até 120 mil caracteres (resultado grande => vai para arquivo).
  // Aceita p(2025, 0) (ano) ou p({desde: '2026-11-08'}, 0).
  async function p(filtro, parte = 0) {
    const op = (filtro && typeof filtro === 'object') ? Object.assign({}, filtro) : { ano: filtro };
    op.parte = parte; op.tam = op.tam || 200000;
    const r = await exportarEnxuto(op);
    const falta = 120000 - r.dados.length;
    if (falta > 0) r.pad = '#'.repeat(falta);
    return r;
  }

  return { rodar, parar, status, exportar, exportarEnxuto, enxugar, p, datas, processarData, state, RELEVANTE, PASTA };
})();
