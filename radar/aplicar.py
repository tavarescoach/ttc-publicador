"""Radar — aplica a curadoria do Claude (radar/curadoria/*.json) na tabela radar.
Atualiza só os campos da curadoria; o status que o Luan deu (salvo/descartado) nunca é tocado."""
import glob
import json
import os
import sys
import urllib.request

URL = os.environ["SUPABASE_URL"].rstrip("/")
KEY = os.environ["SUPABASE_SERVICE_KEY"]
CAMPOS = ["id", "canal", "titulo", "link", "imagem", "publicado_em", "tema", "nota", "motivo", "publico", "pitch", "cluster", "em_alta"]


def main():
    arqs = sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "curadoria", "*.json")))
    if not arqs:
        print("Sem curadoria.")
        return 0
    itens = json.load(open(arqs[-1], encoding="utf-8")).get("itens", [])
    linhas = []
    for i in itens:
        l = {c: i.get(c) for c in CAMPOS}
        l["curado"] = True
        linhas.append(l)
    req = urllib.request.Request(f"{URL}/rest/v1/radar?on_conflict=id", method="POST",
        data=json.dumps(linhas, ensure_ascii=False).encode(),
        headers={"apikey": KEY, "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates,return=minimal"})
    urllib.request.urlopen(req, timeout=60).read()
    print(f"Curadoria aplicada: {len(linhas)} notícias ({os.path.basename(arqs[-1])}).")
    # o que o radar aprendeu com as referências do Luan aparece no painel logo depois da curadoria
    perfil = os.path.join(os.path.dirname(os.path.abspath(__file__)), "perfil-interesse.json")
    if os.path.exists(perfil):
        try:
            up = urllib.request.Request(f"{URL}/storage/v1/object/materiais/radar/perfil.json", method="POST",
                data=open(perfil, "rb").read(),
                headers={"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json",
                         "x-upsert": "true", "cache-control": "no-cache"})
            urllib.request.urlopen(up, timeout=30).read()
            print("Perfil de interesse publicado no painel.")
        except Exception as e:
            print(f"::warning::Não publiquei o perfil: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
