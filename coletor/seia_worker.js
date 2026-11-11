// Trabalhador paralelo do SEIA (várias abas da consulta pública ao mesmo tempo, sem repetir processos).
// Pré-requisitos no localStorage da origem sistema.seia.ba.gov.br:
//   eco_lista  -> JSON [{processo, regiao}] (lista completa)
//   eco_ok:<processo> -> '1' quando o processo já foi indexado por qualquer aba
// Cada aba grava suas fichas no IndexedDB 'eco_seia' com a chave própria (ex.: 'fichas_w2').
// Uso: SEIAW.iniciar({ chave: 'fichas_w2', ordem: 'desc' })   // ou { ordem: 'asc', inicio: 5000 }
window.SEIAW = (function () {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const $ = id => document.getElementById(id);
  const tx = el => (el ? el.textContent : '').replace(/\s+/g, ' ').trim();
  const livre = () => !(window.jQuery && jQuery.active > 0);
  const state = { rodando: false, feitos: 0, docs: 0, naoEncontrados: 0, erros: [], atual: null };
  const fichas = new Map(); let chave = 'fichas_w';
  const ok = p => { try { return localStorage.getItem('eco_ok:' + p) === '1'; } catch (e) { return false; } };
  const marcar = p => { try { localStorage.setItem('eco_ok:' + p, '1'); } catch (e) { } };
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
    await aguardarAjax(() => [...$('conteudo').querySelectorAll('button')].find(b => /Consultar/i.test(b.textContent)).click(), 'conteudo:dataTableProcesso');
    const link = [...document.querySelectorAll('a[id*="dataTableProcesso"]')].find(a => a.textContent.trim() === proc);
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
  function docs(painel, origem) { const out = []; if (!painel) return out; for (const inp of painel.querySelectorAll('input[type=image][title="Download"]')) { const td = [...inp.closest('tr').querySelectorAll('td')].map(tx); out.push({ origem, descricao: td[0] || '', arquivo: td[1] || '', tamanho: td[2] || '', gravado_em: td[3] || '', usuario: td[4] || '' }); } return out; }
  async function processar(item) {
    const proc = item.processo; state.atual = proc;
    if (!(await abrir(proc))) { fichas.set(proc, { processo: proc, regiao: item.regiao, encontrado: false }); state.naoEncontrados++; marcar(proc); return; }
    const dg = dados(await aba('Atos e Dados Gerais'));
    const ds = docs(await aba('Docs de Formação'), 'formacao').concat(docs(await aba('Docs Apensados'), 'apensado'));
    state.docs += ds.length;
    fichas.set(proc, { processo: proc, regiao: item.regiao || 'OESTE', encontrado: true, ...dg, documentos: ds, baixado: false, coletado_em: new Date().toISOString() });
    marcar(proc);
  }
  async function iniciar(op = {}) {
    if (state.rodando) return 'já rodando';
    chave = op.chave || chave; const ordem = op.ordem || 'asc';
    const v = await idb('get', chave).catch(() => null); if (v) for (const f of JSON.parse(v)) fichas.set(f.processo, f);
    const lista = JSON.parse(localStorage.getItem('eco_lista') || '[]');
    let idx = ordem === 'desc' ? lista.length - 1 : (op.inicio || 0);
    state.rodando = true; state.inicio = new Date().toISOString(); state.total = lista.length;
    while (state.rodando && idx >= 0 && idx < lista.length) {
      const item = lista[idx]; idx += ordem === 'desc' ? -1 : 1;
      if (ok(item.processo) || fichas.has(item.processo)) continue;
      try { await processar(item); } catch (e) { state.erros.push(item.processo + ': ' + e.message); if (/SESSAO/.test(e.message)) { state.parouPor = e.message; break; } await sleep(3000); }
      state.feitos++; if (state.feitos % 10 === 0) await salvar().catch(() => { });
    }
    await salvar().catch(() => { }); state.rodando = false; state.fim = new Date().toISOString(); return state;
  }
  return { iniciar, parar: () => { state.rodando = false; }, state, fichas, salvar };
})();
