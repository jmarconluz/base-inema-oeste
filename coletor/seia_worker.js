// Trabalhador paralelo do SEIA (consulta pública, HTTPS, logado). Várias abas, sem repetir processos.
// localStorage (origem sistema.seia.ba.gov.br):
//   eco_lista          -> JSON [{processo, regiao}]
//   eco_ok:<processo>  -> '1' quando indexado;   eco_dl:<processo> -> '1' quando a cópia (zip) foi baixada
// IndexedDB 'eco_seia': fichas por aba (chave própria, ex.: 'fichas_w2').
// Com {baixar:true}, baixa cada processo como SEIA_<processo>.zip (pasta interna com os PDFs + processo.json).
// Uso: eval(localStorage.getItem('eco_code')); SEIAW.iniciar({ chave:'fichas_w2', ordem:'desc', baixar:true })
// No Chrome (downloads automáticos liberados) cada processo vai direto para a pasta de downloads. Documentos: 2 em paralelo por aba
// (localStorage.eco_par), até 3 tentativas, cada uma cortada após 90 s sem receber dados.
window.SEIAW = (function () {
  // Temporizador num Web Worker: o Chrome freia setTimeout em abas de fundo, mas não os timers de workers.
  const sleep = (() => { try { const w = new Worker(URL.createObjectURL(new Blob(['onmessage=e=>setTimeout(()=>postMessage(e.data.id),e.data.ms)'], { type: 'text/javascript' }))); const p = {}; let n = 0; w.onmessage = e => { const f = p[e.data]; delete p[e.data]; if (f) f(); }; return ms => new Promise(r => { const id = ++n; p[id] = r; w.postMessage({ id, ms }); }); } catch (e) { return ms => new Promise(r => setTimeout(r, ms)); } })();
  const $ = id => document.getElementById(id);
  const tx = el => (el ? el.textContent : '').replace(/\s+/g, ' ').trim();
  const san = s => s.replace(/[\\/:*?"<>|]+/g, '_').replace(/\s+/g, ' ').trim().slice(0, 120);
  const livre = () => !(window.jQuery && jQuery.active > 0);
  const state = { rodando: false, feitos: 0, docs: 0, zips: 0, bytes: 0, naoEncontrados: 0, erros: [], atual: null };
  const fichas = new Map(); let chave = 'fichas_w', baixarZip = false;
  const tem = (pre, p) => { try { return localStorage.getItem(pre + p) === '1'; } catch (e) { return false; } };
  const marcar = (pre, p) => { try { localStorage.setItem(pre + p, '1'); } catch (e) { } };

  // ---- ZIP (método "store", nomes UTF-8) ----
  const CRC = (() => { const t = new Uint32Array(256); for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
  function crc32(u8) { let c = 0xFFFFFFFF; for (let i = 0; i < u8.length; i++) c = CRC[(c ^ u8[i]) & 0xFF] ^ (c >>> 8); return (c ^ 0xFFFFFFFF) >>> 0; }
  function zip(entradas) {
    const enc = new TextEncoder(); const partes = []; const central = []; let off = 0;
    const d = new Date(); const dt = ((d.getFullYear() - 1980) << 9) | ((d.getMonth() + 1) << 5) | d.getDate(); const tm = (d.getHours() << 11) | (d.getMinutes() << 5) | (d.getSeconds() >> 1);
    for (const e of entradas) {
      const nome = enc.encode(e.nome); const dados = e.dados; const crc = crc32(dados);
      const lh = new DataView(new ArrayBuffer(30));
      lh.setUint32(0, 0x04034b50, true); lh.setUint16(4, 20, true); lh.setUint16(6, 0x0800, true); lh.setUint16(8, 0, true);
      lh.setUint16(10, tm, true); lh.setUint16(12, dt, true); lh.setUint32(14, crc, true); lh.setUint32(18, dados.length, true); lh.setUint32(22, dados.length, true);
      lh.setUint16(26, nome.length, true); lh.setUint16(28, 0, true);
      partes.push(lh.buffer, nome, dados);
      const ch = new DataView(new ArrayBuffer(46));
      ch.setUint32(0, 0x02014b50, true); ch.setUint16(4, 20, true); ch.setUint16(6, 20, true); ch.setUint16(8, 0x0800, true); ch.setUint16(10, 0, true);
      ch.setUint16(12, tm, true); ch.setUint16(14, dt, true); ch.setUint32(16, crc, true); ch.setUint32(20, dados.length, true); ch.setUint32(24, dados.length, true);
      ch.setUint16(28, nome.length, true); ch.setUint32(42, off, true);
      central.push(ch.buffer, nome);
      off += 30 + nome.length + dados.length;
    }
    const tamCentral = central.reduce((s, b) => s + (b.byteLength || b.length), 0);
    const fim = new DataView(new ArrayBuffer(22));
    fim.setUint32(0, 0x06054b50, true); fim.setUint16(8, entradas.length, true); fim.setUint16(10, entradas.length, true);
    fim.setUint32(12, tamCentral, true); fim.setUint32(16, off, true);
    return new Blob([...partes, ...central, fim.buffer], { type: 'application/zip' });
  }
  function fila() { return new Promise((res, rej) => { const r = indexedDB.open('eco_fila', 1); r.onupgradeneeded = () => r.result.createObjectStore('q'); r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error); }); }
  // Chrome com downloads automáticos liberados: cada processo vai direto para a pasta de downloads (E:\\Downloads\\processos).
  async function salvarArquivo(blob, nome) {
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = nome; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 45000);
    try { localStorage.setItem('eco_arq:' + nome, blob.size + '|' + Date.now()); } catch (e) { }
    await sleep(1500);
  }
  // pausa enquanto houver muito arquivo esperando para ir do C: para o E: (padrão 8 GB na fila)
  async function aguardarEspaco() {
    for (;;) {
      const tot = Number(localStorage.getItem('eco_tot') || 0), dren = Number(localStorage.getItem('eco_drenado') || 0);
      const lim = Number(localStorage.getItem('eco_limite') || 8e9);
      if (tot - dren < lim || !state.rodando) return; state.pausado = true; await sleep(30000);
    }
  }

  async function esperar(cond, ms = 60000, passo = 200) { const t0 = Date.now(); while (Date.now() - t0 < ms) { try { const v = cond(); if (v) return v; } catch (e) { } await sleep(passo); } throw new Error('tempo esgotado'); }
  async function idb(op, k, v) {
    const db = await new Promise((res, rej) => { const r = indexedDB.open('eco_seia', 1); r.onupgradeneeded = () => r.result.createObjectStore('kv'); r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error); });
    return new Promise((res, rej) => { const t = db.transaction('kv', op === 'get' ? 'readonly' : 'readwrite'); const st = t.objectStore('kv'); const q = op === 'get' ? st.get(k) : st.put(v, k); q.onsuccess = () => res(q.result); q.onerror = () => rej(q.error); });
  }
  const salvar = () => idb('put', chave, JSON.stringify([...fichas.values()]));
  async function aguardarAjax(acao, alvoId) {
    const s = document.createElement('span'); const alvo = $(alvoId); if (alvo) alvo.appendChild(s);
    acao(); await sleep(150);
    await esperar(() => livre() && !(alvo && alvo.contains(s) && document.contains(s)), 90000).catch(() => null); await sleep(150);
  }
  async function abrir(proc) {
    try { dialogdetalharProcesso.hide(); } catch (e) { }
    const inp = $('conteudo:numeroProcesso'); if (!inp) throw new Error('SESSAO: deslogado?');
    for (const id of ['conteudo:numDocumento', 'conteudo:nome', 'conteudo:nomEmpreendimento']) if ($(id)) $(id).value = '';
    inp.value = proc;
    // limpa o resultado anterior e só decide quando a tabela mostrar o processo OU a mensagem de "nenhum registro"
    const tab = $('conteudo:dataTableProcesso'); if (tab) tab.setAttribute('data-eco', 'velho');
    const gr = $('growMsg'); if (gr) gr.innerHTML = '';
    await aguardarAjax(() => [...$('conteudo').querySelectorAll('button')].find(b => /Consultar/i.test(b.textContent)).click(), 'conteudo:dataTableProcesso');
    const achar = () => [...document.querySelectorAll('a[id*="dataTableProcesso"]')].find(a => a.textContent.trim() === proc);
    const vazio = () => /n[ãa]o foram encontrados registros/i.test(($('growMsg') || {}).textContent || '') && !(window.jQuery && jQuery.active > 0);
    const res = await esperar(() => achar() ? 'ok' : (vazio() ? 'vazio' : null), 45000, 300).catch(() => null);
    if (!res) throw new Error('busca sem resposta (tentar de novo depois)');
    const link = achar();
    if (!link) return false;
    await aguardarAjax(() => link.click(), 'formDetalharProcesso'); return true;
  }
  async function aba(rotulo) {
    const a = [...document.querySelectorAll('a[href*="tabviewprocesso:"]')].find(x => x.textContent.trim() === rotulo); if (!a) return null;
    const alvo = $(a.getAttribute('href').slice(1)); const s = document.createElement('span'); alvo.appendChild(s);
    a.click(); await sleep(150);
    await esperar(() => livre() && (!alvo.contains(s) || alvo.innerHTML.length > 200), 60000).catch(() => null);
    if (alvo.contains(s)) s.remove(); return alvo;
  }
  function dados(p) {
    const atos = []; if (p) for (const tb of p.querySelectorAll('table')) { const ths = [...tb.querySelectorAll('thead th')].map(tx); if (ths[0] === 'Nome do ato ambiental') for (const tr of tb.querySelectorAll('tbody tr')) { const td = [...tr.querySelectorAll('td')].map(tx); if (td[0]) atos.push({ ato: td[0], tipologia: td[1], status: td[2] }); } }
    return { atos, dados_texto: p ? p.innerText.replace(/[ \t]+/g, ' ').slice(0, 2500) : null };
  }
  function docs(painel, origem) { const out = []; if (!painel) return out; for (const inp of painel.querySelectorAll('input[type=image][title="Download"]')) { const td = [...inp.closest('tr').querySelectorAll('td')].map(tx); out.push({ origem, descricao: td[0] || '', arquivo: td[1] || '', tamanho: td[2] || '', gravado_em: td[3] || '', usuario: td[4] || '', campo: inp.name }); } return out; }
  async function baixarDoc(d) {
    const form = $('formDetalharProcesso'); const fd = new URLSearchParams(new FormData(form)); fd.set(d.campo + '.x', '5'); fd.set(d.campo + '.y', '5');
    // até 3 tentativas; cada uma é cortada se ficar 90 s sem receber dados ou se, depois de 5 min, a média ficar abaixo de 10 KB/s
    let ultErro = null;
    for (let k = 0; k < 3; k++) {
      const ac = new AbortController(); const t0 = Date.now(); let ult = Date.now(), fim = false, recebido = 0;
      (async () => { while (!fim) { await sleep(5000); if (fim) break; try { localStorage.setItem('eco_rs:' + state.atual, String(Date.now())); } catch (e) { } if (Date.now() - ult > 90000 || (Date.now() - t0 > 300000 && recebido / ((Date.now() - t0) / 1000) < 10000)) { ac.abort(); break; } } })();
      try {
        const r = await fetch(form.action, { method: 'POST', signal: ac.signal, body: fd, headers: { 'Content-Type': 'application/x-www-form-urlencoded' } });
        ult = Date.now();
        if (!r.ok) throw new Error('HTTP ' + r.status);
        if (/text\/html/i.test(r.headers.get('content-type') || '')) {
          state.htmlSeguidos = (state.htmlSeguidos || 0) + 1;
          if (state.htmlSeguidos >= 8) throw new Error('SESSAO? 8 respostas HTML seguidas');
          throw new Error('documento indisponível (HTML): ' + d.arquivo);
        }
        const rd = r.body.getReader(); const pedacos = []; let tot = 0;
        for (;;) { const { done, value } = await rd.read(); if (done) break; pedacos.push(value); tot += value.length; recebido = tot; ult = Date.now(); state.ultimoDado = ult; }
        fim = true; state.htmlSeguidos = 0;
        const u8 = new Uint8Array(tot); let o = 0; for (const p of pedacos) { u8.set(p, o); o += p.length; }
        return u8;
      } catch (e) {
        fim = true; ultErro = e;
        if (/SESSAO|HTML/.test((e && e.message) || '')) throw e;
        await sleep(3000 * (k + 1));
      }
    }
    throw new Error('download falhou (' + ((ultErro && (ultErro.message || ultErro.name)) || '?') + '): ' + d.arquivo);
  }
  async function processar(item) {
    const proc = item.processo; state.atual = proc;
    if (!(await abrir(proc))) { fichas.set(proc, { processo: proc, regiao: item.regiao, encontrado: false }); state.naoEncontrados++; marcar('eco_ok:', proc); marcar('eco_dl:', proc); return; }
    const dg = dados(await aba('Atos e Dados Gerais'));
    const ds = docs(await aba('Docs de Formação'), 'formacao').concat(docs(await aba('Docs Apensados'), 'apensado'));
    state.docs += ds.length;
    let baixado = false;
    if (baixarZip) {
      const pasta = san(proc.replace(/\//g, '_')); const entradas = []; let n = 1;
      // baixa os documentos em paralelo (padrão 2 por aba; ajustável em localStorage.eco_par)
      const PAR = Math.max(1, Number(localStorage.getItem('eco_par') || 2)); const res = new Array(ds.length); let prox = 0, sessao = null;
      await Promise.all(Array.from({ length: Math.min(PAR, ds.length) }, async () => {
        while (prox < ds.length && !sessao) {
          const i = prox++; const d = ds[i];
          try { const u8 = await baixarDoc(d); d.bytes = u8.length; d.nome_local = String(i + 1).padStart(2, '0') + ' - ' + san(d.arquivo || 'documento.pdf'); res[i] = { nome: pasta + '/' + d.nome_local, dados: u8 }; state.bytes += u8.length; }
          catch (e) { d.erro = e.message; state.erros.push(proc + ': ' + e.message); if (/SESSAO/.test(e.message)) sessao = e; }
        }
      }));
      if (sessao) throw sessao;
      for (const x of res) if (x) entradas.push(x);
      const ficha = { processo: proc, regiao: item.regiao, ...dg, documentos: ds.map(({ campo, ...x }) => x), baixado_em: new Date().toISOString() };
      const json = { nome: pasta + '/processo.json', dados: new TextEncoder().encode(JSON.stringify(ficha, null, 1)) };
      // processos grandes são divididos em partes de até ~300 MB (limite de cópia para o E:)
      const partes = []; let atual = [json], tam = 0;
      for (const e of entradas) { if (tam > 0 && tam + e.dados.length > 3e8) { partes.push(atual); atual = []; tam = 0; } atual.push(e); tam += e.dados.length; }
      partes.push(atual);
      for (let i = 0; i < partes.length; i++) await salvarArquivo(zip(partes[i]), 'SEIA_' + pasta + (partes.length > 1 ? '_parte' + (i + 1) : '') + '.zip');
      state.zips++; baixado = true; marcar('eco_dl:', proc);
      try { localStorage.setItem('eco_dlt:' + proc, String(Date.now()) + '|' + partes.length); } catch (e) { }
      await sleep(800);
    }
    fichas.set(proc, { processo: proc, regiao: item.regiao || 'OESTE', encontrado: true, ...dg, documentos: ds.map(({ campo, ...x }) => x), baixado, coletado_em: new Date().toISOString() });
    marcar('eco_ok:', proc);
  }
  async function iniciar(op = {}) {
    if (state.rodando) return 'já rodando';
    chave = op.chave || chave; baixarZip = !!op.baixar; const ordem = op.ordem || 'asc';
    const v = await idb('get', chave).catch(() => null); if (v) for (const f of JSON.parse(v)) if (!f.outraAba) fichas.set(f.processo, f);
    const lista = JSON.parse(localStorage.getItem('eco_lista') || '[]');
    let idx = op.inicio != null ? op.inicio : (ordem === 'desc' ? lista.length - 1 : 0);
    state.rodando = true; state.inicio = new Date().toISOString(); state.total = lista.length;
    // mantém a aba 'viva': segurar um Web Lock impede o Chrome de congelar a aba em segundo plano; __hbGaps registra pausas > 2 min
    if (!window.__vivo) { window.__vivo = true; try { navigator.locks.request('eco_vivo_' + chave, () => new Promise(() => { })); } catch (e) { } window.__hbGaps = []; let ultHb = Date.now(); setInterval(() => { const n = Date.now(); if (n - ultHb > 120000) { window.__hbGaps.push([new Date(ultHb).toLocaleTimeString('pt-BR'), Math.round((n - ultHb) / 1000)]); if (window.__hbGaps.length > 50) window.__hbGaps.shift(); } ultHb = n; }, 5000); }
    // trava de disco: para a aba quando a soma dos zips baixados (eco_arq) passa de localStorage.eco_limite_disco (bytes)
    (async () => { while (state.rodando) { const lim = Number(localStorage.getItem('eco_limite_disco') || 0); if (lim) { let t = 0; for (let i = 0; i < localStorage.length; i++) { const k = localStorage.key(i); if (k && k.startsWith('eco_arq:')) t += Number((localStorage.getItem(k) || '0').split('|')[0]) || 0; } state.totalBaixado = t; if (t > lim) { state.parouPor = 'limite de disco (' + Math.round(t / 1e9) + ' GB)'; state.rodando = false; break; } } await sleep(120000); } })();
    let volta = 1; const voltas = Math.max(1, op.voltas || 1); state.volta = 1; state.regiao = op.regiao || null;
    while (state.rodando) {
      if (idx < 0 || idx >= lista.length) { if (volta >= voltas) break; volta++; state.volta = volta; idx = ordem === 'desc' ? lista.length - 1 : 0; continue; }
      const item = lista[idx]; idx += ordem === 'desc' ? -1 : 1; state.idx = idx;
      if (op.regiao && item.regiao !== op.regiao) continue;
      if (baixarZip) await aguardarEspaco(); state.pausado = false;
      const feito = baixarZip ? tem('eco_dl:', item.processo) : (tem('eco_ok:', item.processo) || fichas.has(item.processo));
      if (feito) continue;
      // reserva o processo para esta aba (evita que duas abas baixem o mesmo); reservas com mais de 20 min expiram
      const rs = Number(localStorage.getItem('eco_rs:' + item.processo) || 0);
      if (rs && Date.now() - rs < 20 * 60000) continue;
      try { localStorage.setItem('eco_rs:' + item.processo, String(Date.now())); } catch (e) { }
      try { await processar(item); } catch (e) { state.erros.push(item.processo + ': ' + e.message); try { localStorage.removeItem('eco_rs:' + item.processo); } catch (_) { } if (/SESSAO/.test(e.message)) { state.parouPor = e.message; break; } await sleep(3000); }
      try { localStorage.removeItem('eco_rs:' + item.processo); } catch (_) { }
      state.feitos++; if (state.feitos % 5 === 0) await salvar().catch(() => { });
    }
    await salvar().catch(() => { }); state.rodando = false; state.fim = new Date().toISOString(); return state;
  }
  return { iniciar, parar: () => { state.rodando = false; }, state, fichas, salvar };
})();
