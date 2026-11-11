// Coletor de portarias do INEMA (ASV e outorga) no Diário Oficial do Estado da Bahia (DOOL/EGBA).
// Roda no contexto da página https://dool.egba.ba.gov.br (navegador com conexão do Brasil).
// Guarda os registros na memória da página (window.__store) e baixa um JSON por ano ao final.
// Uso (no console da página do DOOL):
//   await ECO.rodar('2016-11-11', '2026-11-11');   // coleta
//   ECO.baixar();                                  // baixa doe_inema_AAAA.json para a pasta Downloads
window.ECO = (function () {
  const OESTE = ['Barreiras', 'Luís Eduardo Magalhães', 'Luis Eduardo Magalhães', 'São Desidério', 'Formosa do Rio Preto',
    'Riachão das Neves', 'Correntina', 'Jaborandi', 'Cocos', 'Santa Maria da Vitória', 'Baianópolis', 'Angical', 'Cotegipe',
    'Wanderley', 'Cristópolis', 'Catolândia', 'Tabocas do Brejo Velho', 'Santana', 'Canápolis', 'Serra Dourada', 'Coribe',
    'São Félix do Coribe', 'Mansidão', 'Santa Rita de Cássia', 'Brejolândia', 'Buritirama', 'Sítio do Mato', 'Serra do Ramalho',
    'Muquém do São Francisco', 'Muquém de São Francisco', 'Barra', 'Ibotirama'];
  const norm = s => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();
  const OESTE_N = new Set(OESTE.map(norm));
  const MESES = { janeiro: 1, fevereiro: 2, 'março': 3, marco: 3, abril: 4, maio: 5, junho: 6, julho: 7, agosto: 8, setembro: 9, outubro: 10, novembro: 11, dezembro: 12 };
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const strip = h => h.replace(/<style[\s\S]*?<\/style>/gi, '').replace(/<br\s*\/?>/gi, ' ').replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ').replace(/&quot;/g, '"').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&#(\d+);/g, (m, c) => String.fromCharCode(c)).replace(/\s+/g, ' ').trim();
  const num = s => {
    if (!s) return null; s = s.trim();
    if (/,\d{1,4}$/.test(s)) s = s.replace(/\./g, '').replace(',', '.');
    else if (/^\d{1,3}(\.\d{3})+$/.test(s)) s = s.replace(/\./g, '');
    const v = parseFloat(s); return isNaN(v) ? null : v;
  };
  const MUN_RE = /munic[ií]pios?\s+de\s+([A-ZÀ-Ú][A-Za-zÀ-ú'\-]+(?:\s+(?:d[aeo]s?|[A-ZÀ-Ú][A-Za-zÀ-ú'\-]+))*)/g;
  const muns = t => [...t.matchAll(MUN_RE)].map(m => m[1].replace(/\s+(d[aeo]s?)$/, '').trim());
  const mask = t => t.replace(/\d{3}\.?\d{3}\.?\d{3}\s*-\s*\d{2}/g, '***.***.***-**');

  function parse(p, ed, materia) {
    if (!/RESOLVE/i.test(p)) return null;
    const isASV = /SUPRESS[ÃA]O D[AE] VEGETA[ÇC][ÃA]O/i.test(p);
    const isOUT = /direito de uso d[oe]s? recursos? h[ií]dricos|OUTORGA D[EO] DIREITO|outorga de uso/i.test(p);
    if (!isASV && !isOUT) return null;
    const pos = p.search(/RESOLVE/i);
    const rest = p.slice(pos); const a2 = rest.search(/Art\.?\s*2/i);
    const art = a2 > 0 ? rest.slice(0, a2) : rest.slice(0, 3000);
    const acaoM = art.match(/RESOLVE\s*:?\s*(?:Art\.?\s*1\.?\s*[º°o]?\.?\s*[-–:]?\s*)?([A-Za-zÀ-ú]+)/i);
    const acao = acaoM ? acaoM[1] : '';
    if (/^(Revogar|Cancelar|Suspender|Arquivar|Indeferir|Tornar|Declarar)/i.test(acao)) return null;
    const nM = p.match(/PORTARIA\s*N[º°o]\.?\s*([\d\.]+)/i);
    const dM = p.match(/DE\s+(\d{1,2})\s+DE\s+([A-Za-zçÇ]+)\s+DE\s+(\d{4})/i);
    const procM = p.match(/Processo\s*n[º°o]?\.?\s*([0-9][0-9\.\s\/\-A-Za-z]{6,60}?)(?=\s*[,;]|\s+RESOLVE|\s+requerid)/i);
    let reqM = art.match(/(?:requerid[oa]\s+por|\s(?:à|ao)\s)\s*([^,]{3,140}?)\s*,\s*(?:inscrit|CPF|CNPJ|pessoa)/i)
      || p.match(/requerid[oa]\s+por\s+([^,]{3,140}?)\s*,/i)
      || p.match(/(?:\s(?:à|ao|a|para)\s+(?:empresa\s+)?)([A-ZÀ-Ú][A-ZÀ-Ú0-9 &\.\-\/'ºª]{3,140}?)\s*,\s*(?:inscrit|CPF|CNPJ|portador)/);
    let mA = muns(art); if (!mA.length) mA = muns(p);
    const munU = [...new Set(mA)];
    const mun = mA.length ? mA[mA.length - 1] : null;
    const oeste = (mun && OESTE_N.has(norm(mun))) || munU.some(m => OESTE_N.has(norm(m)));
    let fin = null;
    if (isOUT && !isASV) { const f = art.match(/para\s+fins?\s+de\s+([^,;]+)/i) || art.match(/finalidade\s+(?:de\s+)?([^,;]+)/i); fin = f ? f[1] : null; }
    else { const i = art.search(/VEGETA[ÇC][ÃA]O NATIVA/i); const f = art.slice(Math.max(0, i)).match(/\spara\s+(?!o\s+prazo)((?:[^,;]|,(?=\d)){4,200})/i); fin = f ? f[1] : null; }
    if (fin) fin = fin.replace(/\s+em uma área de.*$/i, '').trim();
    const areaM = isASV
      ? art.slice(Math.max(0, art.search(/VEGETA[ÇC][ÃA]O NATIVA/i))).match(/[áa]rea\s+(?:total\s+)?(?:de\s+supress[ãa]o\s+)?(?:de\s+)?([\d\.,]+)\s*(?:ha|hectares)/i)
      : art.match(/[áa]rea\s+(?:irrigada\s+)?(?:de\s+)?([\d\.,]+)\s*(?:ha|hectares)/i);
    const volM = p.match(/lenhoso[^0-9]{0,80}([\d\.,]+)\s*m[³3]/i);
    const valM = art.match(/v[áa]lid[ao]\s+(?:pelo\s+prazo\s+de\s+|at[ée]\s+)([^,;]{2,40})/i);
    const modM = art.match(/capta[çc][ãa]o\s+(subterr[âa]nea|superficial)/i) || art.match(/(lan[çc]amento de efluentes|barramento|barragem|perfura[çc][ãa]o)/i);
    const bacM = art.match(/Bacia\s+Hidrogr[áa]fica\s+(?:do\s+|da\s+|de\s+)?([^,;]{2,60})/i);
    const hM = art.match(/durante\s+([\d,]+)\s*h/i); const horas = hM ? num(hM[1]) : null;
    let vaz = 0, nv = 0;
    for (const m of art.matchAll(/vaz[ãa]o\s+(?:m[áa]xima\s+)?(?:de\s+|instant[âa]nea\s+de\s+)?([\d\.,]+)\s*m[³3]\s*\/\s*(dia|d|h|hora|s)/gi)) {
      let v = num(m[1]); if (v == null) continue; const u = m[2].toLowerCase();
      if (u.startsWith('h')) v = v * (horas || 24); else if (u === 's') v = v * 86400; vaz += v; nv++;
    }
    const fazM = art.match(/(Fazendas?\s+[^,;]{2,80})/i);
    const coords = [...art.matchAll(/(Lat\.?\s*[-\d°º'’"″,\.\sSN]+?\s*e\s*Long\.?\s*[-\d°º'’"″,\.\sWO]+)/gi)].map(m => m[1].trim().replace(/,$/, '')).slice(0, 20).join('; ');
    const dataPub = ed.data.split('/').reverse().join('-');
    const pn = nM ? nM[1].replace(/\./g, '') : null;
    const cat = (isASV && isOUT) ? 'ASV+OUTORGA' : (isASV ? 'ASV' : 'OUTORGA');
    return {
      chave: (pn || ('m' + materia + '-' + p.length)) + '|' + dataPub, tipo: cat + ' - ' + acao, portaria_num: pn,
      data_portaria: dM ? `${dM[3]}-${String(MESES[dM[2].toLowerCase()] || 0).padStart(2, '0')}-${dM[1].padStart(2, '0')}` : null,
      data_publicacao: dataPub, edicao_id: String(ed.id), materia_id: String(materia),
      processo: procM ? procM[1].replace(/\s+/g, '') : null, requerente: reqM ? reqM[1].trim() : null,
      tipo_pessoa: /CNPJ/i.test(p) ? 'PJ' : (/CPF/i.test(p) ? 'PF' : null),
      municipio: mun, municipios_citados: munU.join('; '), oeste: !!oeste,
      finalidade: fin ? fin.slice(0, 200) : null, area_ha: areaM ? num(areaM[1]) : null, volume_lenhoso_m3: volM ? num(volM[1]) : null,
      validade: valM ? valM[1].trim() : null, modalidade: modM ? modM[1].toLowerCase() : null, bacia: bacM ? bacM[1].trim() : null,
      vazao_m3_dia: nv ? Math.round(vaz * 100) / 100 : null, horas_dia: horas, fazenda: fazM ? fazM[1].trim() : null,
      coordenadas: coords || null, texto: oeste ? mask(p).slice(0, 20000) : null,
      link_doe: `https://dool.egba.ba.gov.br/ver-html/${ed.id}/#e:${ed.id}`
    };
  }

  const SKIP_SUB = /Resumo|Aditivo|Licita|Apostila|Contrato|Conv[êe]nio|Dispensa|Inexigib|Homolog|Adjudica|Preg[ãa]o|Extrato|Ratifica|Aviso/i;
  async function getText(url) {
    for (let k = 0; k < 4; k++) {
      try { const r = await fetch(url); if (!r.ok) throw new Error(r.status); return await r.text(); }
      catch (e) { await sleep(1500 * (k + 1)); }
    }
    throw new Error('falha ' + url);
  }
  async function edicao(ed) {
    const h = await getText('/html/' + ed.id + '.html');
    const doc = new DOMParser().parseFromString(h, 'text/html');
    const folds = [...doc.querySelectorAll('span.folder')].filter(s => /INEMA|Instituto do Meio Ambiente e Recursos H/i.test(s.textContent));
    const recs = []; const seen = new Set();
    for (const f of folds) {
      for (const a of f.parentElement.querySelectorAll('a.linkMateria')) {
        const mid = a.getAttribute('data-materia-id'); if (seen.has(mid)) continue; seen.add(mid);
        const ul = a.closest('ul'); const sub = (ul && ul.parentElement.querySelector('span.folder') || {}).textContent || '';
        if (/RHBAHIA/i.test(a.textContent) || SKIP_SUB.test(sub)) continue;
        let t; try { t = strip(await getText('/apifront/portal/edicoes/publicacoes_ver_conteudo/' + mid)); } catch (e) { state.erros.push('materia ' + mid); continue; }
        for (const p of t.split(/(?=PORTARIA\s*N[º°o]\.?\s*[\d\.]+)/i)) { const r = parse(p, ed, mid); if (r) recs.push(r); }
      }
    }
    return recs;
  }
  async function edicoesDaData(d) {
    const j = JSON.parse(await getText('/apifront/portal/edicoes/edicoes_from_data/' + d));
    return (j.itens || []).filter(i => /Estado da Bahia/i.test(i.tipo_edicao_nome));
  }
  window.__store = window.__store || new Map();
  async function enviar(recs) { for (const r of recs) window.__store.set(r.chave, r); }

  // Baixa um arquivo JSON por ano de publicação (doe_inema_AAAA.json).
  function baixar(prefixo = 'doe_inema_') {
    const porAno = {};
    for (const r of window.__store.values()) { const a = (r.data_publicacao || '0000').slice(0, 4); (porAno[a] = porAno[a] || []).push(r); }
    const anos = Object.keys(porAno).sort();
    anos.forEach((a, i) => setTimeout(() => {
      const regs = porAno[a].sort((x, y) => (x.data_publicacao + x.portaria_num).localeCompare(y.data_publicacao + y.portaria_num));
      const blob = new Blob([JSON.stringify(regs)], { type: 'application/json' });
      const el = document.createElement('a'); el.href = URL.createObjectURL(blob); el.download = prefixo + a + '.json';
      document.body.appendChild(el); el.click(); el.remove();
    }, i * 1500));
    return anos.map(a => a + ': ' + porAno[a].length);
  }

  const state = { rodando: false, datasTotal: 0, datasFeitas: 0, edicoes: 0, registros: 0, oeste: 0, erros: [], ultima: null, inicio: null };
  function loadDone() { try { return new Set(JSON.parse(localStorage.getItem('eco_datas_ok') || '[]')); } catch (e) { return new Set(); } }
  function saveDone(s) { try { localStorage.setItem('eco_datas_ok', JSON.stringify([...s])); } catch (e) { } }

  async function processarData(d, done) {
    const eds = await edicoesDaData(d);
    for (const ed of eds) {
      const recs = await edicao(ed);
      if (recs.length) await enviar(recs);
      state.edicoes++; state.registros += recs.length; state.oeste += recs.filter(r => r.oeste).length;
    }
    done.add(d); state.datasFeitas++; state.ultima = d;
  }

  // Coleta de um intervalo de datas (YYYY-MM-DD), da mais recente para a mais antiga.
  async function rodar(inicio, fim, workers = 3) {
    if (state.rodando) return 'já está rodando';
    state.rodando = true; state.inicio = new Date().toISOString(); state.erros = [];
    const done = loadDone(); const datas = [];
    for (let d = new Date(fim + 'T12:00:00'); d >= new Date(inicio + 'T12:00:00'); d.setDate(d.getDate() - 1)) {
      const s = d.toISOString().slice(0, 10); if (d.getDay() !== 0 && !done.has(s)) datas.push(s);
    }
    state.datasTotal = datas.length; state.datasFeitas = 0;
    let idx = 0; let salvos = 0;
    async function worker() {
      while (state.rodando && idx < datas.length) {
        const d = datas[idx++];
        try { await processarData(d, done); } catch (e) { state.erros.push(d + ': ' + e.message); }
        if (++salvos % 10 === 0) saveDone(done);
      }
    }
    await Promise.all(Array.from({ length: workers }, worker));
    saveDone(done); state.rodando = false; state.fim = new Date().toISOString();
    return state;
  }
  function parar() { state.rodando = false; }
  return { parse, edicao, edicoesDaData, enviar, rodar, parar, baixar, state, OESTE };
})();
