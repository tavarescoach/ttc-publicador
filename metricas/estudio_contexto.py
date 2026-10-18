"""Resumo do desempenho real do Instagram para o Estúdio avaliar headlines.

Lê metricas/painel.json e grava metricas/estudio-contexto.json, que a sessão do Claude envia ao banco do Estúdio
(ArtifactData update, collection "contexto", doc "instagram"). Rode: python3 metricas/estudio_contexto.py
"""
import json
import os
import re
import statistics

AQUI = os.path.dirname(os.path.abspath(__file__))


def limpar_titulo(t):
    t = re.sub(r"\s+", " ", t or "").strip()
    return t[:140]


def main():
    d = json.load(open(os.path.join(AQUI, "painel.json"), encoding="utf-8"))
    posts = []
    for p in d.get("posts", []):
        if not p.get("titulo"):
            continue
        posts.append({
            "titulo": limpar_titulo(p["titulo"]), "tipo": p.get("tipo"), "quando": (p.get("quando") or "")[:10],
            "alcance": p.get("alcance") or 0, "views": p.get("views") or 0, "salvos": p.get("salvos") or 0,
            "compart": p.get("compart") or 0, "comentarios": p.get("comentarios") or 0,
            "valor": p.get("valor") or 0, "taxa": p.get("taxa"), "parcial": bool(p.get("parcial")),
        })
    # "valor" = salvos*3 + compartilhamentos*3 + comentários*2 + curtidas; "taxa" = valor por 100 contas alcançadas
    posts.sort(key=lambda p: (p["valor"], p["alcance"]), reverse=True)
    maduros = [p for p in posts if not p["parcial"]] or posts
    medianas = {}
    for k in ("alcance", "valor", "taxa"):
        vals = [p[k] for p in maduros if p[k] is not None]
        medianas[k] = round(statistics.median(vals), 1) if vals else None
    por_tipo = {}
    for p in posts:
        t = por_tipo.setdefault(p["tipo"], {"posts": 0, "alcance": 0, "valor": 0})
        t["posts"] += 1
        t["alcance"] += p["alcance"]
        t["valor"] += p["valor"]
    for t in por_tipo.values():
        t["alcance_medio"] = round(t.pop("alcance") / t["posts"])
        t["valor_medio"] = round(t.pop("valor") / t["posts"], 1)
    saida = {
        "atualizado_em": d.get("gerado_em"),
        "seguidores": (d.get("conta") or {}).get("seguidores"),
        "explica": "valor = salvos x3 + compartilhamentos x3 + comentários x2 + curtidas; taxa = valor por 100 contas alcançadas; "
                   "parcial = post com menos de 48 h, números ainda subindo",
        "medianas": medianas,
        "por_tipo": por_tipo,
        "posts": posts[:20],
    }
    destino = os.path.join(AQUI, "estudio-contexto.json")
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=1)
    print(f"{destino}: {len(saida['posts'])} posts, medianas {medianas}")


if __name__ == "__main__":
    main()
