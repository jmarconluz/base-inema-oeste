"""Gera as tabelas da base a partir dos arquivos brutos do coletor.

Entrada : dados/brutos/doe_inema_AAAA.json  (um por ano, saída do coletor/coletor_doe.js)
Saídas  : dados/bahia/portarias_bahia.csv        – todos os atos de ASV e outorga da Bahia (sem texto integral)
          dados/oeste/portarias_oeste.csv        – só o Oeste Baiano (com texto integral)
          dados/oeste/portarias_oeste.json       – idem, em JSON
          dados/oeste/pontos_outorga_asv_oeste.geojson – coordenadas (poços, captações, áreas) para abrir no QGIS
          dados/resumo.md                         – números gerais da base

Uso: python scripts/processar.py
"""
import csv
import glob
import json
import os
import re
from collections import Counter, defaultdict

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRUTOS = os.path.join(RAIZ, "dados", "brutos")

CAMPOS = ["chave", "tipo", "categoria", "acao", "tipo_outorga", "portaria_num", "data_portaria", "data_publicacao", "ano", "processo",
          "requerente", "tipo_pessoa", "municipio", "municipios_citados", "oeste", "finalidade", "area_ha",
          "volume_lenhoso_m3", "validade", "modalidade", "bacia", "vazao_m3_dia", "horas_dia", "fazenda",
          "coordenadas", "n_pontos", "link_doe", "edicao_id", "materia_id"]

DMS = re.compile(
    r"Lat\.?\s*(-?\d{1,2})\s*[°º]\s*(\d{1,2})\s*['’′]\s*([\d.,]+)?\s*[\"”″]?\s*([SN])?"
    r".{0,15}?Long\.?\s*(-?\d{1,3})\s*[°º]\s*(\d{1,2})\s*['’′]\s*([\d.,]+)?\s*[\"”″]?\s*([WO])?",
    re.I,
)


def dms_para_graus(g, m, s, hemi, negativo_padrao=True):
    v = abs(float(g)) + float(m) / 60 + (float(s.replace(",", ".")) if s else 0) / 3600
    if hemi:
        return -v if hemi.upper() in ("S", "W", "O") else v
    return -v if negativo_padrao else v  # Bahia: latitude Sul e longitude Oeste


def pontos(coord_txt):
    out = []
    for m in DMS.finditer(coord_txt or ""):
        try:
            lat = dms_para_graus(m.group(1), m.group(2), m.group(3), m.group(4))
            lon = dms_para_graus(m.group(5), m.group(6), m.group(7), m.group(8))
        except (ValueError, TypeError):
            continue
        if -19 < lat < -8 and -47 < lon < -37:  # dentro da Bahia
            out.append((round(lon, 6), round(lat, 6)))
    return out


def carregar():
    regs = {}
    for f in sorted(glob.glob(os.path.join(BRUTOS, "doe_inema_*.json"))):
        with open(f, encoding="utf-8") as fh:
            for r in json.load(fh):
                regs[r["chave"]] = r
    return list(regs.values())


MUN_CANON = {"Luis Eduardo Magalhães": "Luís Eduardo Magalhães", "Muquém de São Francisco": "Muquém do São Francisco"}


SUBTERRANEA = re.compile(r"capta[çc][ãa]o\s+subterr|po[çc]os?\b|aqu[íi]fero|tubular", re.I)
SUPERFICIAL = re.compile(r"capta[çc][ãa]o\s+superficial|\b(rio|riacho|c[óo]rrego|ribeir[ãa]o|vereda|lagoa|represa|reservat[óo]rio|a[çc]ude)\b", re.I)


def tipo_outorga(r):
    """Classifica a outorga: poço (subterrânea), captação superficial, barramento, lançamento ou outros."""
    if "OUTORGA" not in (r.get("tipo") or ""):
        return ""
    mod = (r.get("modalidade") or "").lower()
    t = r.get("texto") or ""
    art = t[t.upper().find("RESOLVE"):][:3000] if "RESOLVE" in t.upper() else t[:3000]
    if mod.startswith("subterr"):
        base = "Poço (captação subterrânea)"
    elif mod.startswith("superficial"):
        base = "Captação superficial"
    elif "lan" in mod and "efluente" in mod:
        return "Lançamento de efluentes"
    elif mod in ("barragem", "barramento"):
        return "Barramento"
    elif SUBTERRANEA.search(art) and not re.search(r"capta[çc][ãa]o\s+superficial", art, re.I):
        base = "Poço (captação subterrânea)"
    elif SUPERFICIAL.search(art):
        base = "Captação superficial"
    elif r.get("acao") == "Transferir":
        return "Transferência de titularidade (sem dado técnico)"
    elif re.search(r"altera[çc][ãa]o do direito", art, re.I):
        return "Alteração de outorga (sem dado técnico)"
    else:
        return "Não identificado"
    if re.search(r"capta[çc][ãa]o\s+subterr", art, re.I) and re.search(r"capta[çc][ãa]o\s+superficial", art, re.I):
        return "Poço + captação superficial"
    return base


def preparar(r):
    r = dict(r)
    if r.get("municipio") in MUN_CANON:
        r["municipio"] = MUN_CANON[r["municipio"]]
    cat, _, acao = (r.get("tipo") or "").partition(" - ")
    r["categoria"], r["acao"] = cat, acao
    r["ano"] = (r.get("data_publicacao") or "")[:4]
    r["n_pontos"] = len(pontos(r.get("coordenadas")))
    r["tipo_outorga"] = tipo_outorga(r)
    return r


def salvar_csv(caminho, regs, campos):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos, extrasaction="ignore", delimiter=";")
        w.writeheader()
        for r in regs:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in campos})


def main():
    regs = sorted((preparar(r) for r in carregar()), key=lambda r: (r["data_publicacao"] or "", r["portaria_num"] or ""))
    oeste = [r for r in regs if r.get("oeste")]

    salvar_csv(os.path.join(RAIZ, "dados", "bahia", "portarias_bahia.csv"), regs, CAMPOS + ["texto"])
    with open(os.path.join(RAIZ, "dados", "bahia", "portarias_bahia.json"), "w", encoding="utf-8") as fh:
        json.dump(regs, fh, ensure_ascii=False)
    salvar_csv(os.path.join(RAIZ, "dados", "oeste", "portarias_oeste.csv"), oeste, CAMPOS + ["texto"])
    with open(os.path.join(RAIZ, "dados", "oeste", "portarias_oeste.json"), "w", encoding="utf-8") as fh:
        json.dump(oeste, fh, ensure_ascii=False, indent=1)

    def geo(lista, nome):
        fs = []
        for r in lista:
            for i, (lon, lat) in enumerate(pontos(r.get("coordenadas"))):
                props = {k: r.get(k) for k in CAMPOS if k not in ("coordenadas",)}
                props["ponto"] = i + 1
                fs.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [lon, lat]}, "properties": props})
        with open(nome, "w", encoding="utf-8") as fh:
            json.dump({"type": "FeatureCollection", "name": os.path.basename(nome)[:-8],
                       "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::4674"}}, "features": fs}, fh, ensure_ascii=False)
        return fs
    eh_asv = lambda r: "ASV" in (r.get("categoria") or "")
    eh_out = lambda r: "OUTORGA" in (r.get("categoria") or "")
    feats_ba = geo([r for r in regs if eh_out(r)], os.path.join(RAIZ, "dados", "bahia", "pontos_outorga_bahia.geojson"))
    feats_ba += geo([r for r in regs if eh_asv(r)], os.path.join(RAIZ, "dados", "bahia", "pontos_asv_bahia.geojson"))
    feats_oe_out = geo([r for r in oeste if eh_out(r)], os.path.join(RAIZ, "dados", "oeste", "pontos_outorga_oeste.geojson"))
    feats_oe_asv = geo([r for r in oeste if eh_asv(r)], os.path.join(RAIZ, "dados", "oeste", "pontos_asv_oeste.geojson"))
    feats = feats_oe_out + feats_oe_asv

    # resumo
    tipos_out = Counter(r["tipo_outorga"] for r in regs if r["tipo_outorga"])
    por_ano = defaultdict(Counter)
    for r in regs:
        por_ano[r["ano"]][("Oeste " if r.get("oeste") else "Demais ") + r["categoria"]] += 1
    mun = Counter(r["municipio"] for r in oeste if r.get("municipio"))
    cats = ["Oeste ASV", "Oeste OUTORGA", "Demais ASV", "Demais OUTORGA"]
    linhas = ["# Resumo da base", "", f"Total de atos (Bahia): **{len(regs)}** · Oeste Baiano: **{len(oeste)}** · "
              f"pontos georreferenciados no Oeste: **{len(feats)}**", "",
              "| Ano | " + " | ".join(cats) + " |", "|---|" + "---|" * len(cats)]
    for a in sorted(por_ano):
        linhas.append(f"| {a} | " + " | ".join(str(por_ano[a][c]) for c in cats) + " |")
    linhas += ["", "## Outorgas por tipo (Bahia)", "", "| Tipo | Atos |", "|---|---|"]
    linhas += [f"| {k} | {v} |" for k, v in tipos_out.most_common()]
    linhas += ["", f"Pontos georreferenciados na Bahia: **{len(feats_ba)}** · Oeste: outorga **{len(feats_oe_out)}**, ASV **{len(feats_oe_asv)}**"]
    linhas += ["", "## Municípios do Oeste com mais atos", "", "| Município | Atos |", "|---|---|"]
    linhas += [f"| {m} | {n} |" for m, n in mun.most_common(20)]
    with open(os.path.join(RAIZ, "dados", "resumo.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(linhas) + "\n")
    print(f"Bahia: {len(regs)} | Oeste: {len(oeste)} | pontos: {len(feats)}")


if __name__ == "__main__":
    main()
