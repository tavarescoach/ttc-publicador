"""Acha uma foto de pessoa conhecida no Wikimedia Commons com licença de uso comercial.

Usado por render/render.py quando a capa traz "pessoa" e não traz "foto". A licença vem dos metadados
oficiais do arquivo (extmetadata), não de leitura de página. Só aceita CC BY, CC BY-SA, CC0 e domínio público.
Uso direto (teste): python render/foto_commons.py "Leslie Jones"
"""
import html
import json
import re
import sys
import urllib.parse
import urllib.request

API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "ttc-publicador/1.0 (https://github.com/tavarescoach/ttc-publicador; Instagram @tavarescoach)"}


def _licenca(curta):
    c = (curta or "").lower().replace("-", " ").strip()
    if c.startswith("cc by sa"):
        return "cc-by-sa"
    if c.startswith("cc by") and "nc" not in c and "nd" not in c:
        return "cc-by"
    if c.startswith("cc0") or c.startswith("cc zero"):
        return "cc0"
    if "public domain" in c or c in ("pd", "domínio público"):
        return "dominio-publico"
    return None


def _texto(h):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", h or ""))).strip()


def buscar(pessoa, largura=1600):
    q = {"action": "query", "format": "json", "generator": "search", "gsrnamespace": 6, "gsrlimit": 30,
         "gsrsearch": f'"{pessoa}" filetype:bitmap', "prop": "imageinfo",
         "iiprop": "url|size|extmetadata", "iiurlwidth": largura}
    req = urllib.request.Request(f"{API}?{urllib.parse.urlencode(q)}", headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        paginas = (json.loads(r.read()).get("query") or {}).get("pages", {}).values()
    partes = [p.lower() for p in pessoa.split() if len(p) > 2]
    cand = []
    for p in paginas:
        titulo = p.get("title", "")
        if not all(x in titulo.lower() for x in partes):
            continue  # o nome precisa estar no nome do arquivo
        ii = (p.get("imageinfo") or [{}])[0]
        meta = ii.get("extmetadata") or {}
        lic = _licenca((meta.get("LicenseShortName") or {}).get("value"))
        if not lic or ii.get("width", 0) < 600:
            continue
        autor = _texto((meta.get("Artist") or {}).get("value")) or "autor no Commons"
        cand.append({
            "foto": ii.get("thumburl") or ii.get("url"),
            "credito": f"Foto: {autor[:60]} / Wikimedia Commons ({_texto(meta['LicenseShortName']['value'])})",
            "licenca": lic,
            "pagina_origem": ii.get("descriptionurl"),
            "_ordem": (ii.get("height", 0) >= ii.get("width", 0), ii.get("width", 0) * ii.get("height", 0)),
        })
    if not cand:
        return None
    melhor = max(cand, key=lambda c: c["_ordem"])
    melhor.pop("_ordem")
    return melhor


if __name__ == "__main__":
    print(json.dumps(buscar(" ".join(sys.argv[1:])), ensure_ascii=False, indent=1))
