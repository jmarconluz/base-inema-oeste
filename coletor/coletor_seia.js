// Coletor de processos do SEIA (consulta pública) – Ecoplan
// Página: https://sistema.seia.ba.gov.br/paginas/manter-consultapublica/consultaPublica.xhtml  (HTTPS, logado)
//
// 1) Índice: para cada processo da lista, lê atos, dados gerais e a lista de documentos
//    (Docs de Formação + Docs Apensados). Progresso salvo no IndexedDB 'eco_seia' (chave 'fichas').
// 2) Cópia integral: depois de SEIA.definirPasta() (escolher E:\Downloads\processos), baixa cada
//    documento para <pasta>/<processo>/NN - arquivo.pdf e grava <pasta>/<processo>/processo.json.
//
// Uso (console da página):
//   SEIA.definirListaB36('<lista compacta>')   // ou SEIA.definirLista([...números de processo])
//   SEIA.rodar()                                 // retoma de onde parou (pula processos já feitos)
//   SEIA.state                                   // progresso
//   SEIA.exportar()                              // baixa seia_indice.json (fichas coletadas)
window.SEIA = (function () {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const $ = id => document.getElementById(id);
  const tx = el => (el ? el.textContent : '').replace(/\s+/g, ' ').trim();
  const san = s => s.replace(/[\\/:*?"<>|]+/g, '_').replace(/\s+/g, ' ').trim().slice(0, 150);
  const livre = () => !(window.jQuery && jQuery.active > 0);
  const state = { rodando: false, feitos: 0, total: 0, docs: 0, baixados: 0, bytes: 0, pulados: 0, naoEncontrados: 0, erros: [], atual: null };
  let lista = [], dir = null; const fichas = new Map();

  function definirLista(nums) { lista = nums.map(p => ({ processo: p })); return lista.length; }
  function definirListaB36(s) {
    lista = [];
    for (const parte of s.split(';')) {
      const [ano, ds] = parte.split('|'); let prev = null;
      for (const d of ds.split('.')) { const v = parseInt(d, 36); const n = prev === null ? v : prev - v; prev = n; const nn = String(n).padStart(6, '0'); lista.push({ processo: ano + '.001.' + nn + '/INEMA/LIC-' + nn.slice(1) }); }
    }
    return lista.length;
  }
  async function idb(op, k, v) {
    const db = await new Promise((res, rej) => { const r = indexedDB.open('eco_seia', 1); r.onupgradeneeded = () => r.result.createObjectStore('kv'); r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error); });
    return new Promise((res, rej) => { const t = db.transaction('kv', op === 'get' ? 'readonly' : 'readwrite'); const st = t.objectStore('kv'); const q = op === 'get' ? st.get(k) : st.put(v, k); q.onsuccess = () => res(q.result); q.onerror = () => rej(q.error); });
  }
  async function carregar() { const v = await idb('get', 'fichas'); if (v) for (const f of JSON.parse(v)) fichas.set(f.processo, f); return fichas.size; }
  const salvar = () => idb('put', 'fichas', JSON.stringify([...fichas.values()]));
  async function esperar(cond, ms = 60000, passo = 300) { const t0 = Date.now(); while (Date.now() - t0 < ms) { try { const v = cond(); if (v) return v; } catch (e) { } await sleep(passo); } throw new Error('tempo esgotado'); }

  async function aguardarUpdate(acao) {
    const f = $('formDetalharProcesso'); const s = document.createElement('span'); s.id = 'eco-sent'; f.appendChild(s);
    acao(); await esperar(() => !document.getElementById('eco-sent') && livre(), 90000); await sleep(300);
  }
  async function abrir(proc) {
    try { dialogdetalharProcesso.hide(); } catch (e) { }
    const inp = $('conteudo:numeroProcesso'); if (!inp) throw new Error('SESSAO: deslogado?');
    for (const id of ['conteudo:numDocumento', 'conteudo:nome', 'conteudo:nomEmpreendimento']) if ($(id)) $(id).value = '';
    inp.value = proc;
    const tab = $('conteudo:dataTableProcesso'); if (tab) tab.setAttribute('data-eco', 'velho');
    [...$('conteudo').querySelectorAll('button')].find(b => /Consultar/i.test(b.textContent)).click();
    await esperar(() => { const t = $('conteudo:dataTableProcesso'); return t && t.getAttribute('data-eco') !== 'velho' && livre(); }, 90000);
    const link = [...document.querySelectorAll('a[id*="dataTableProcesso"]')].find(a => a.textContent.trim() === proc);
    if (!link) return false;
    await aguardarUpdate(() => link.click());
    return true;
  }
  async function aba(rotulo) {
    const a = [...document.querySelectorAll('a[href*="tabviewprocesso:"]')].find(x => x.textContent.trim() === rotulo); if (!a) return null;
    const alvo = $(a.getAttribute('href').slice(1)); a.click();
    await sleep(500); await esperar(livre, 120000).catch(() => null);
    await esperar(() => alvo && alvo.innerHTML.length > 50, 30000).catch(() => null); return alvo;
  }
  function dados(p) {
    const atos = [];
    if (p) for (const tb of p.querySelectorAll('table')) {
      const ths = [...tb.querySelectorAll('thead th')].map(tx);
      if (ths[0] === 'Nome do ato ambiental') for (const tr of tb.querySelectorAll('tbody tr')) { const td = [...tr.querySelectorAll('td')].map(tx); if (td[0]) atos.push({ ato: td[0], tipologia: td[1], status: td[2] }); }
    }
    return { atos, dados_texto: p ? p.innerText.replace(/[ \t]+/g, ' ').slice(0, 2500) : null };
  }
  function docs(painel, origem) {
    const out = []; if (!painel) return out;
    for (const inp of painel.querySelectorAll('input[type=image][title="Download"]')) {
      const td = [...inp.closest('tr').querySelectorAll('td')].map(tx);
      out.push({ origem, descricao: td[0] || '', arquivo: td[1] || '', tamanho: td[2] || '', gravado_em: td[3] || '', usuario: td[4] || '', campo: inp.name });
    }
    return out;
  }
  async function baixar(d, pasta, n) {
    const form = $('formDetalharProcesso'); const fd = new URLSearchParams(new FormData(form)); fd.set(d.campo + '.x', '5'); fd.set(d.campo + '.y', '5');
    let r;
    for (let k = 0; k < 3; k++) { try { r = await fetch(form.action, { method: 'POST', body: fd, headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }); if (r.ok) break; } catch (e) { } await sleep(3000 * (k + 1)); }
    if (!r || !r.ok || /text\/html/i.test(r.headers.get('content-type') || '')) throw new Error('download falhou: ' + d.arquivo);
    const nome = String(n).padStart(2, '0') + ' - ' + san(d.arquivo || 'documento.pdf');
    const fh = await pasta.getFileHandle(nome, { create: true }); const w = await fh.createWritable(); await r.body.pipeTo(w);
    const sz = (await fh.getFile()).size; state.bytes += sz; state.baixados++; return { nome_local: nome, bytes: sz };
  }
  async function processar(item) {
    const proc = item.processo; const f0 = fichas.get(proc);
    if (f0 && (f0.encontrado === false || !dir || f0.baixado)) { state.pulados++; return; }
    state.atual = proc;
    if (!(await abrir(proc))) { fichas.set(proc, { processo: proc, encontrado: false }); state.naoEncontrados++; return; }
    const dg = dados(await aba('Atos e Dados Gerais'));
    const ds = docs(await aba('Docs de Formação'), 'formacao').concat(docs(await aba('Docs Apensados'), 'apensado'));
    state.docs += ds.length;
    let baixado = false;
    if (dir) {
      const pasta = await dir.getDirectoryHandle(san(proc.replace(/\//g, '_')), { create: true }); let n = 1;
      for (const d of ds) { try { Object.assign(d, await baixar(d, pasta, n++)); } catch (e) { d.erro = e.message; state.erros.push(proc + ': ' + e.message); } }
      const fh = await pasta.getFileHandle('processo.json', { create: true }); const w = await fh.createWritable();
      await w.write(JSON.stringify({ processo: proc, ...dg, documentos: ds.map(({ campo, ...x }) => x) }, null, 1)); await w.close(); baixado = true;
    }
    fichas.set(proc, { processo: proc, encontrado: true, ...dg, documentos: ds.map(({ campo, ...x }) => x), baixado, coletado_em: new Date().toISOString() });
  }
  async function rodar() {
    if (state.rodando) return 'já rodando';
    state.rodando = true; state.inicio = new Date().toISOString(); await carregar().catch(() => 0); state.total = lista.length;
    for (const item of lista) {
      if (!state.rodando) break;
      try { await processar(item); }
      catch (e) { state.erros.push(item.processo + ': ' + e.message); if (/SESSAO/.test(e.message)) { state.parouPor = e.message; break; } await sleep(4000); }
      state.feitos++; if (state.feitos % 5 === 0) await salvar().catch(() => { });
    }
    await salvar().catch(() => { }); state.rodando = false; state.atual = null; state.fim = new Date().toISOString(); return state;
  }
  async function definirPasta() { dir = await window.showDirectoryPicker({ id: 'seia-processos', mode: 'readwrite' }); return dir.name; }
  function exportar() {
    const b = new Blob([JSON.stringify([...fichas.values()])], { type: 'application/json' });
    const el = document.createElement('a'); el.href = URL.createObjectURL(b); el.download = 'seia_indice.json'; document.body.appendChild(el); el.click(); el.remove();
    return fichas.size;
  }
  return { definirLista, definirListaB36, rodar, parar: () => { state.rodando = false; }, state, fichas, definirPasta, exportar, salvar, carregar, get lista() { return lista; } };
})();
