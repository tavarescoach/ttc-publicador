"""Grava no painel (coluna conteudos.fontes) as referências de cada conteúdo: render/fontes/<id>.json.

Formato: [{"tipo": "estudo|noticia|artigo", "titulo": "...", "url": "https://..."}]
Só atualiza a coluna fontes (não mexe em etapa, data ou legenda). Uso: python render/fontes.py [arquivos...]
"""
import glob
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
AQUI = os.path.dirname(os.path.abspath(__file__))


def main():
    arqs = [a for a in sys.argv[1:] if a.endswith(".json")] or sorted(glob.glob(os.path.join(AQUI, "fontes", "*.json")))
    if not (URL and KEY):
        print("Sem SUPABASE_URL/KEY: nada enviado.")
        return 0
    falhas = 0
    for a in arqs:
        if not os.path.exists(a):
            continue
        cid = os.path.splitext(os.path.basename(a))[0]
        fontes = [f for f in json.load(open(a, encoding="utf-8")) if str(f.get("url", "")).startswith("http")]
        req = urllib.request.Request(
            f"{URL}/rest/v1/conteudos?id=eq.{urllib.parse.quote(cid)}", method="PATCH",
            data=json.dumps({"fontes": fontes}, ensure_ascii=False).encode(),
            headers={"apikey": KEY, "Content-Type": "application/json", "Prefer": "return=representation"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                n = len(json.loads(r.read() or b"[]"))
            print(f"::notice::fontes {cid}: {len(fontes)} link(s), {n} card(s) atualizado(s)")
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:300]
            if "fontes" in msg:
                print("::warning::A tabela conteudos ainda não tem a coluna fontes. Rode no Supabase: "
                      "alter table public.conteudos add column if not exists fontes jsonb;")
                return 0
            print(f"::error::{cid}: HTTP {e.code} {msg}")
            falhas += 1
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
