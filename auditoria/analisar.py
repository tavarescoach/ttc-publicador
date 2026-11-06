"""Análise da auditoria do Instagram (@tavarescoach).

Lê auditoria/dados/ultimo.json (coletado por auditoria/coletar.py) e fila.json, e grava
auditoria/relatorios/AAAA-MM-DD.json com os números que a skill auditoria-instagram-ttc usa:
- conta: alcance diário (mediana por semana), saldo de seguidores, visitas ao perfil
- por formato x origem (AUTO = publicado pelo robô, MAN = postado pelo Luan no app)
- por hora, por tema, por padrão de abertura da legenda
- concentração: quanto dos seguidores ganhos veio dos 3 melhores posts
- público: % do Rio entre seguidores e entre o público engajado, % homens, faixa 25-44
- os 5 melhores e os 5 piores posts do período

Uso: python auditoria/analisar.py [AAAA-MM-DD início] [AAAA-MM-DD fim]
(padrão: últimos 21 dias; posts com menos de 24 h ficam de fora)
"""
import collections
import datetime as dt
import json
import os
import statistics as st
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRT = dt.timezone(dt.timedelta(hours=-3))
RIO = "Rio de Janeiro, Rio de Janeiro (state)"


def carregar():
    d = json.load(open(os.path.join(RAIZ, "auditoria/dados/ultimo.json"), encoding="utf-8"))
    fila = json.load(open(os.path.join(RAIZ, "fila.json"), encoding="utf-8"))
    return d, {x.get("media_id"): x for x in fila if x.get("media_id")}


def resumo(g):
    if not g:
        return None
    alc = [x["alcance"] or 0 for x in g]
    return {
        "n": len(g), "alcance_mediana": round(st.median(alc)), "alcance_media": round(st.mean(alc)),
        "alcance_max": max(alc),
        "salvos_compart_por_post": round(st.mean([(x["salvos"] or 0) + (x["compart"] or 0) for x in g]), 1),
        "seguidores_ganhos": sum(x["seguiu"] or 0 for x in g),
        "visitas_perfil": sum(x["visitas_perfil"] or 0 for x in g),
    }


def abertura(leg):
    l = (leg.strip().splitlines() or [""])[0]
    if l.startswith("Decodificando"):
        return "Decodificando"
    if l.startswith("Eu "):
        return "Opinião em 1ª pessoa"
    if any(c.isdigit() for c in l[:40]):
        return "Número na 1ª linha"
    return "Outra"


def main():
    d, fila = carregar()
    agora = dt.datetime.fromisoformat(d["gerado_em"])
    fim = sys.argv[2] if len(sys.argv) > 2 else (agora - dt.timedelta(hours=24)).isoformat(timespec="minutes")
    ini = sys.argv[1] if len(sys.argv) > 1 else (agora - dt.timedelta(days=21)).date().isoformat()
    P = [x for x in d["posts"] if ini <= x["quando"] <= fim]
    for x in P:
        q = fila.get(x["id"])
        x["origem"] = "AUTO" if q else "MAN"
        x["tema"] = (q or {}).get("tema") or "sem tema"
    out = {"gerado_em": d["gerado_em"], "periodo": [ini, fim[:10]], "conta": d["conta"]}

    # conta: semanas
    sem = collections.defaultdict(list)
    for dia in d["diario"]:
        s = dt.date.fromisoformat(dia["dia"])
        sem[(s - dt.timedelta(days=s.weekday())).isoformat()].append(dia)
    out["semanas"] = [{
        "semana": k, "alcance_dia_mediana": round(st.median([x["reach"] or 0 for x in v])),
        "visitas_perfil": sum(x["profile_views"] or 0 for x in v),
        "saldo_seguidores": sum((x["ganhos"] or 0) - (x["perdidos"] or 0) for x in v),
        "posts_feed": sum(1 for p in d["posts"] if p["quando"][:10] in {x["dia"] for x in v}),
    } for k, v in sorted(sem.items())]

    out["todos"] = resumo(P)
    out["formato_origem"] = {f"{t} {o}": resumo([x for x in P if x["tipo"] == t and x["origem"] == o])
                             for t in ("CARROSSEL", "IMAGEM", "REELS") for o in ("AUTO", "MAN")}
    out["hora_auto_feed"] = {h: resumo([x for x in P if x["origem"] == "AUTO" and x["tipo"] != "REELS" and x["quando"][11:13] == h])
                             for h in sorted({x["quando"][11:13] for x in P})}
    out["tema_auto"] = {t: resumo([x for x in P if x["origem"] == "AUTO" and x["tema"] == t]) for t in sorted({x["tema"] for x in P})}
    out["abertura_auto"] = {a: resumo([x for x in P if x["origem"] == "AUTO" and abertura(x["legenda"]) == a])
                            for a in ("Decodificando", "Opinião em 1ª pessoa", "Número na 1ª linha", "Outra")}
    por_dia = collections.Counter(x["quando"][:10] for x in P if x["tipo"] != "REELS" or x["origem"] == "AUTO")
    out["feed_por_dia_media"] = round(st.mean(por_dia.values()), 1) if por_dia else None
    ganhos = sorted([x["seguiu"] or 0 for x in P], reverse=True)
    out["seguidores_top3_pct"] = round(100 * sum(ganhos[:3]) / sum(ganhos)) if sum(ganhos) else None
    reels = [x["tempo_medio_s"] for x in P if x["tempo_medio_s"]]
    out["reels_tempo_medio_mediana_s"] = round(st.median(reels), 1) if reels else None

    pub = d.get("publico") or {}
    def pct(m, chave, val):
        b = (pub.get(m) or {}).get(chave) or {}
        tot = sum(((pub.get(m) or {}).get("gender") or {}).values())
        return round(100 * sum(b.get(v, 0) for v in val) / tot) if tot else None
    out["publico"] = {
        "seguidores_rio_pct": pct("follower_demographics", "city", [RIO]),
        "engajados_rio_pct": pct("engaged_audience_demographics", "city", [RIO]),
        "seguidores_homens_pct": pct("follower_demographics", "gender", ["M"]),
        "engajados_homens_pct": pct("engaged_audience_demographics", "gender", ["M"]),
        "seguidores_25_44_pct": pct("follower_demographics", "age", ["25-34", "35-44"]),
    }
    chave = lambda x: (x["seguiu"] or 0) * 10 + (x["salvos"] or 0) * 3 + (x["compart"] or 0) * 3 + (x["alcance"] or 0) / 100
    lin = lambda x: {"quando": x["quando"], "tipo": x["tipo"], "origem": x["origem"], "alcance": x["alcance"],
                     "salvos": x["salvos"], "compart": x["compart"], "seguiu": x["seguiu"],
                     "abertura": (x["legenda"].strip().splitlines() or [""])[0][:90], "link": x["link"]}
    ordem = sorted(P, key=chave, reverse=True)
    out["melhores"] = [lin(x) for x in ordem[:5]]
    out["piores"] = [lin(x) for x in ordem[-5:]]

    pasta = os.path.join(RAIZ, "auditoria/relatorios")
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, agora.date().isoformat() + ".json")
    json.dump(out, open(caminho, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
