"""Exporta do painel (Supabase) as criações que estão esperando o Claude.

Gera criacoes/pendentes.json e baixa os materiais enviados (PDF, imagens etc.)
para criacoes/materiais/, para o Claude ler na sessão.

Variáveis: SUPABASE_URL, SUPABASE_SERVICE_KEY
"""
import json
import os
import sys
import urllib.parse
import urllib.request

PASTA = os.path.dirname(os.path.abspath(__file__))
URL = os.environ["SUPABASE_URL"].rstrip("/")
KEY = os.environ["SUPABASE_SERVICE_KEY"]


def get(caminho):
    req = urllib.request.Request(f"{URL}{caminho}", headers={"apikey": KEY})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def main():
    pend = json.loads(get("/rest/v1/criacoes?vez=eq.claude&etapa=neq.cancelada&select=*&order=criado_em"))
    os.makedirs(os.path.join(PASTA, "criacoes"), exist_ok=True)
    for c in pend:
        arq = (c.get("entrada") or {}).get("arquivo")
        if not arq:
            continue
        destino = os.path.join(PASTA, "criacoes", "materiais", arq)
        if os.path.exists(destino):
            continue
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        try:
            dados = get("/storage/v1/object/materiais/" + urllib.parse.quote(arq))
            with open(destino, "wb") as f:
                f.write(dados)
            print(f"material baixado: {arq}")
        except Exception as e:  # material ausente não impede a exportação
            print(f"::warning::não baixou {arq}: {e}")
    with open(os.path.join(PASTA, "criacoes", "pendentes.json"), "w", encoding="utf-8") as f:
        json.dump(pend, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"{len(pend)} criação(ões) esperando o Claude.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
