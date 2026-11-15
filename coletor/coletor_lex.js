// Coletor de legislação (Planalto e LegislaBahia): texto vigente, sem os trechos tachados/revogados.
// Rodar numa aba aberta na MESMA origem das URLs: https://www.planalto.gov.br/ ou https://www.legislabahia.ba.gov.br/
// (os sites não liberam CORS; por isso a aba precisa estar no próprio site).
// Uso:
//   await LEX.verificarRepo('<sha do commit>');  // compara com juridico/legislacao/hashes.json do repositório
//                                               // e devolve só as normas desta origem cujo texto mudou
//   await LEX.preparar([urls que mudaram]); LEX.parte(0) ...  // envelopes {chave:'lex_<site>', parte, partes, n, dados, pad}
//   (depois: python scripts/decodificar_partes.py /tmp/pacotes && python scripts/verificar_legislacao.py atualizar /tmp/pacotes/lex_*.json)
window.LEX = {
  REPO: 'https://raw.githubusercontent.com/jmarconluz/base-inema-oeste/',
  async texto(url) {
    const r = await fetch(url); if (!r.ok) throw new Error('HTTP ' + r.status + ' ' + url);
    const buf = await r.arrayBuffer();
    let html = new TextDecoder('utf-8').decode(buf);
    if (html.includes('�')) html = new TextDecoder('windows-1252').decode(buf);
    const doc = new DOMParser().parseFromString(html, 'text/html');
    doc.querySelectorAll('script,style,strike,s,del,[style*="line-through"],header,footer,nav').forEach(e => e.remove());
    const main = doc.querySelector('.field--name-body, .node__content, article, main, #content') || doc.body;
    main.querySelectorAll('p,br,div,tr,h1,h2,h3,h4,li,table').forEach(e => e.append('\n'));
    const t = (main.textContent || '').replace(/ /g, ' ').replace(/[ \t]+/g, ' ').replace(/ *\n[ \n]*/g, '\n').trim();
    return { url, titulo: (doc.title || '').trim(), chars: t.length, texto: t };
  },
  // Cabeçalho institucional do Planalto (muda de formato sem mudar a norma): fica fora do hash (igual ao Python).
  canon(t) { return t.replace(/^Presid[êe]ncia da Rep[úu]blica\n(?:Casa Civil\n)?(?:Subchefia|Secretaria Especial) para Assuntos Jur[íi]dicos\n/, ''); },
  async hash(t) {
    const b = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(this.canon(t)));
    return [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, '0')).join('');
  },
  async verificar(urls) {
    const out = [];
    for (const u of urls) {
      try { const r = await this.texto(u); out.push({ url: u, chars: r.chars, sha256: await this.hash(r.texto), titulo: r.titulo }); }
      catch (e) { out.push({ url: u, erro: e.message }); }
    }
    return out;
  },
  // Lê juridico/legislacao/hashes.json do repositório (no commit indicado) e confere as normas desta origem.
  async verificarRepo(sha = 'main') {
    const ref = await (await fetch(this.REPO + sha + '/juridico/legislacao/hashes.json', { cache: 'no-store' })).json();
    const daqui = ref.filter(x => new URL(x.url).host === location.host);
    const atual = await this.verificar(daqui.map(x => x.url));
    const mudou = [], erros = [];
    for (const a of atual) {
      const r = daqui.find(x => x.url === a.url);
      if (a.erro) erros.push(a);
      else if (a.sha256 !== r.sha256) mudou.push({ url: a.url, arquivo: r.arquivo, chars_antes: r.chars, chars_agora: a.chars });
    }
    return { origem: location.host, conferidas: daqui.length, mudou, erros };
  },
  async preparar(urls, chave = 'lex_' + location.host.replace(/\W+/g, '_')) {
    const out = [];
    for (const u of urls) { try { out.push(await this.texto(u)); } catch (e) { out.push({ url: u, erro: e.message }); } }
    const gz = await new Response(new Blob([JSON.stringify(out)]).stream().pipeThrough(new CompressionStream('gzip'))).arrayBuffer();
    const u8 = new Uint8Array(gz); let bin = '';
    for (let i = 0; i < u8.length; i += 0x8000) bin += String.fromCharCode.apply(null, u8.subarray(i, i + 0x8000));
    this.b64 = btoa(bin); this.chave = chave; this.n = out.length;
    return { chave, n: out.length, partes: Math.ceil(this.b64.length / 180000) || 1, resumo: out.map(o => ({ url: o.url, chars: o.chars, erro: o.erro })) };
  },
  parte(i) {
    const d = this.b64.slice(i * 180000, (i + 1) * 180000);
    return { chave: this.chave, parte: i, partes: Math.ceil(this.b64.length / 180000) || 1, n: this.n, dados: d, pad: '#'.repeat(Math.max(0, 120000 - d.length)) };
  }
};
