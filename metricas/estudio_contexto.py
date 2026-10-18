"""Contexto do Estúdio para avaliar headlines (banco do artifact, coleção "contexto").

Gera três arquivos, que a sessão do Claude envia com ArtifactData:
- metricas/estudio-contexto.json    -> doc "instagram": desempenho real dos posts (de metricas/painel.json)
- metricas/estudio-radar.json       -> doc "radar": assuntos em alta e melhores notícias (de radar/curadoria/)
- metricas/estudio-aprendizado.json -> doc "aprendizado": headline escolhida x resultado real (teste A/B),
                                       só com --criacoes <pasta> (export da coleção "criacoes" via ArtifactData list out_dir)

Rode: python3 metricas/estudio_contexto.py [--criacoes <pasta com os .json das criações>]
"""
import glob
import json
import os
import re
import statistics
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
PESOS = {"curiosidade": 20, "clareza": 15, "marca": 15, "publico": 15, "venda": 15, "historico": 10, "atualidade": 10}


def limpar_titulo(t):
    t = re.sub(r"\s+", " ", t or "").strip()
    return t[:140]


def gravar(nome, dados):
    destino = os.path.join(AQUI, nome)
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=1)
    return destino


def radar():
    arqs = sorted(glob.glob(os.path.join(RAIZ, "radar", "curadoria", "*.json")))
    if not arqs:
        return None
    d = json.load(open(arqs[-1], encoding="utf-8"))
    itens = d.get("itens", [])
    grupos = {}
    for i in itens:
        if i.get("em_alta") and i.get("cluster"):
            g = grupos.setdefault(i["cluster"], {"assunto": i["cluster"], "tema": i.get("tema"), "canais": set(), "nota_max": 0, "titulos": []})
            g["canais"].add(i["canal"])
            g["nota_max"] = max(g["nota_max"], i.get("nota") or 0)
            g["titulos"].append((i.get("nota") or 0, i["titulo"]))
    em_alta = []
    for g in sorted(grupos.values(), key=lambda g: (-len(g["canais"]), -g["nota_max"])):
        em_alta.append({"assunto": g["assunto"], "tema": g["tema"], "canais": len(g["canais"]), "nota_max": g["nota_max"],
                        "titulos": [t for _, t in sorted(g["titulos"], reverse=True)[:3]]})
    top = [{"titulo": i["titulo"], "canal": i["canal"], "assunto": i.get("cluster"), "nota": i.get("nota"),
            "gancho": (i.get("pitch") or {}).get("gancho")}
           for i in sorted(itens, key=lambda i: -(i.get("nota") or 0)) if (i.get("nota") or 0) >= 70][:10]
    return {"atualizado_em": d.get("gerado_em"), "em_alta": em_alta[:8], "top": top}


def spearman(xs, ys):
    def rank(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
                j += 1
            for k in range(i, j + 1):
                r[o[k]] = (i + j) / 2
            i = j + 1
        return r
    rx, ry = rank(xs), rank(ys)
    mx, my = statistics.mean(rx), statistics.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return round(num / den, 2) if den else None


def aprendizado(pasta, posts_por_id, mediana_taxa):
    fila = json.load(open(os.path.join(RAIZ, "fila.json"), encoding="utf-8"))
    media_de = {x["id"]: x.get("media_id") for x in fila if x.get("media_id")}
    pares = []
    for arq in sorted(glob.glob(os.path.join(pasta, "*.json"))):
        c = json.load(open(arq, encoding="utf-8"))
        c = c.get("data", c) if isinstance(c.get("data"), dict) else c
        h = c.get("headline") or {}
        if not h.get("titulo"):
            continue
        for formato, card in (c.get("resultado") or {}).items():
            post = posts_por_id.get(media_de.get(card))
            if not post:
                continue
            av = c.get("avaliacao_headlines") or {}
            esc = av.get("escolhida") or {}
            pares.append({
                "headline": h["titulo"], "formato": formato, "quando": post["quando"],
                "alcance": post["alcance"], "valor": post["valor"], "taxa": post["taxa"], "parcial": post["parcial"],
                "notas": esc.get("notas"), "total": esc.get("total"),
                "seguiu_recomendada": (esc.get("indice") == (av.get("recomendada") or {}).get("indice")) if av else None,
                "alternativas": [{"titulo": x.get("titulo"), "total": x.get("total")} for x in av.get("headlines", [])
                                 if x.get("titulo") != h["titulo"]][:3],
            })
    medidos = [p for p in pares if not p["parcial"] and p["taxa"] is not None]
    com_notas = [p for p in medidos if p["notas"]]
    correl = {}
    if len(com_notas) >= 6:
        for k in PESOS:
            xs = [p["notas"].get(k) for p in com_notas]
            if all(x is not None for x in xs) and len(set(xs)) > 1:
                correl[k] = spearman(xs, [p["taxa"] for p in com_notas])
    pesos = None
    if len(com_notas) >= 8 and correl:
        bruto = {k: PESOS[k] * (1 + max(-0.6, min(0.6, correl.get(k) or 0))) for k in PESOS}
        soma = sum(bruto.values())
        pesos = {k: round(v * 100 / soma) for k, v in bruto.items()}
    seguiu = [p for p in medidos if p["seguiu_recomendada"] is not None]
    def media(l):
        return round(statistics.mean(l), 1) if l else None
    return {
        "pares": pares[-30:], "medidos": len(medidos), "com_notas": len(com_notas), "mediana_taxa_perfil": mediana_taxa,
        "correlacao_taxa": correl, "pesos_sugeridos": pesos,
        "recomendada": {"seguiu": len([p for p in seguiu if p["seguiu_recomendada"]]), "nao_seguiu": len([p for p in seguiu if not p["seguiu_recomendada"]]),
                        "taxa_seguiu": media([p["taxa"] for p in seguiu if p["seguiu_recomendada"]]),
                        "taxa_nao_seguiu": media([p["taxa"] for p in seguiu if not p["seguiu_recomendada"]])},
    }


def main():
    d = json.load(open(os.path.join(AQUI, "painel.json"), encoding="utf-8"))
    posts = []
    for p in d.get("posts", []):
        if not p.get("titulo"):
            continue
        posts.append({
            "id": p.get("id"), "titulo": limpar_titulo(p["titulo"]), "tipo": p.get("tipo"), "quando": (p.get("quando") or "")[:10],
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
    print(f"{gravar('estudio-contexto.json', saida)}: {len(saida['posts'])} posts, medianas {medianas}")
    r = radar()
    if r:
        print(f"{gravar('estudio-radar.json', r)}: {len(r['em_alta'])} assuntos em alta, {len(r['top'])} notícias 70+")
    if "--criacoes" in sys.argv:
        pasta = sys.argv[sys.argv.index("--criacoes") + 1]
        a = aprendizado(pasta, {p["id"]: p for p in posts}, medianas.get("taxa"))
        print(f"{gravar('estudio-aprendizado.json', a)}: {len(a['pares'])} pares, {a['medidos']} medidos, pesos {a['pesos_sugeridos']}")


if __name__ == "__main__":
    main()
