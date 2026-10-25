"""Escolhe o tema do próximo ciclo de 3 dias (diretrizes/ciclo.md, seção 1). Conta fixa, sem IA.

Uso: python ciclo/escolher.py [--hoje AAAA-MM-DD] [--simular]

Roda todo dia às 14h50 (robô "Ciclo temático"). Só cria ciclo na véspera do próximo; nos outros dias, sai.
Na véspera:
1. pontua os 8 temas com as notícias do Radar das últimas 72 h (radar/curadoria/*.json);
2. aplica as regras (2 ciclos anteriores fora; depois de 2 cruzados, só centrais; empate = usado há mais tempo);
3. lista as notícias com pessoa conhecida do tema (para o estático das 7h);
4. escolhe as fotos pessoais dos dias 1 e 3 (20h), sem repetir até usar todas, e sobe para o bucket;
5. grava o ciclo em ciclos/ciclos.json (status "escolhido"). A tarefa "Pacote do ciclo" (15h07) escreve o conteúdo.
Com "ativo": false em ciclo/config.json (ou --simular), só grava ciclos/simulacao.json.
"""
import datetime as dt
import glob
import hashlib
import io
import json
import os
import re
import sys
import urllib.parse
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
BRT = dt.timezone(dt.timedelta(hours=-3))
CFG = os.path.join(AQUI, "config.json")
CICLOS = os.path.join(RAIZ, "ciclos", "ciclos.json")
ROTACAO = os.path.join(RAIZ, "ciclos", "rotacao.json")
SIMULACAO = os.path.join(RAIZ, "ciclos", "simulacao.json")


def ler(c, padrao):
    try:
        with open(c, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return padrao


def gravar(c, d):
    os.makedirs(os.path.dirname(c), exist_ok=True)
    with open(c, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
        f.write("\n")


# ------------------------------------------------------------ dados do Radar
def pesos_fontes():
    pesos = {}
    for arq in ("fontes.json", "fontes-extras.json"):
        for f in ler(os.path.join(RAIZ, "radar", arq), []):
            if isinstance(f, dict) and f.get("canal"):
                pesos[f["canal"]] = float(f.get("peso", 1.0))
    return pesos


def noticias(agora, horas=72):
    """Itens das curadorias das últimas `horas`, sem repetir id (vale a avaliação mais nova)."""
    por_id = {}
    for arq in sorted(glob.glob(os.path.join(RAIZ, "radar", "curadoria", "*.json"))):
        for it in ler(arq, {}).get("itens", []):
            por_id[it.get("id")] = it
    out = []
    for it in por_id.values():
        try:
            pub = dt.datetime.fromisoformat(str(it.get("publicado_em")).replace("Z", "+00:00"))
        except ValueError:
            continue
        idade = (agora - pub).total_seconds() / 3600
        if 0 <= idade <= horas:
            out.append(dict(it, _idade_h=idade))
    return out


def tema_do_item(it, cfg):
    """tema_editorial da curadoria; sem ele, palavras-chave no título, motivo e cluster."""
    t = it.get("tema_editorial")
    if t in cfg["temas"]:
        return t
    texto = " ".join(str(it.get(c) or "") for c in ("titulo", "motivo", "cluster")).lower()
    achados = [s for s, rx in cfg["palavras"].items() if re.search(rx, texto)]
    return achados[0] if len(achados) == 1 else (achados[0] if achados else None)


def recencia(h):
    return 1.0 if h <= 24 else 0.6 if h <= 48 else 0.3


def pontuar(itens, cfg, pesos, inicio, fim):
    assuntos = {}
    for it in itens:
        if (it.get("nota") or 0) < 50:
            continue
        t = tema_do_item(it, cfg)
        if not t:
            continue
        valor = (it["nota"] / 100) * pesos.get(it.get("canal"), 1.0) * recencia(it["_idade_h"])
        chave = (t, it.get("cluster") or it["id"])
        a = assuntos.setdefault(chave, {"valor": 0, "canais": set(), "em_alta": False, "ids": []})
        a["valor"] = max(a["valor"], valor)
        a["canais"].add(it.get("canal"))
        a["em_alta"] |= bool(it.get("em_alta"))
        a["ids"].append(it["id"])
    pts = {s: 0.0 for s in cfg["temas"]}
    base = {s: [] for s in cfg["temas"]}
    for (t, _), a in assuntos.items():
        v = a["valor"] * min(2.0, 1 + 0.25 * (len(a["canais"]) - 1)) * (1.5 if a["em_alta"] or len(a["canais"]) >= 3 else 1)
        pts[t] += v
        base[t] += a["ids"]
    bonus = {}
    for d in ler(os.path.join(RAIZ, "radar", "calendario.json"), []):
        s = cfg["calendario"].get(d.get("slug"))
        if s and data_no_periodo(d, inicio, fim):
            pts[s] *= 1.3
            bonus[s] = d.get("titulo")
    return {s: round(v, 3) for s, v in pts.items()}, base, bonus


def data_no_periodo(d, inicio, fim):
    """Datas do calendário vêm como MM-DD (podem virar o ano)."""
    dia = inicio
    while dia <= fim:
        md = dia.strftime("%m-%d")
        if (d["inicio"] <= d["fim"] and d["inicio"] <= md <= d["fim"]) or \
                (d["inicio"] > d["fim"] and (md >= d["inicio"] or md <= d["fim"])):
            return True
        dia += dt.timedelta(days=1)
    return False


def escolher(pts, ciclos, cfg):
    anteriores = [c["sigla"] for c in ciclos[-2:]]
    cand = [s for s in cfg["temas"] if s not in anteriores]
    regra = "2 ciclos anteriores fora"
    if len(ciclos) >= 2 and all(c["sigla"] not in cfg["centrais"] for c in ciclos[-2:]):
        cand = [s for s in cand if s in cfg["centrais"]]
        regra += "; só centrais (2 cruzados seguidos)"
    ultimo_uso = {s: "" for s in cfg["temas"]}
    for c in ciclos:
        ultimo_uso[c["sigla"]] = c["inicio"]
    if max(pts[s] for s in cand) <= 0:
        cand = [s for s in cand if s in cfg["centrais"]] or cand
        return min(cand, key=lambda s: ultimo_uso[s]), regra + "; sem notícia pontuada: central usado há mais tempo"
    return max(cand, key=lambda s: (pts[s], -_ord(ultimo_uso[s]))), regra


def _ord(d):
    return dt.date.fromisoformat(d).toordinal() if d else 0


# ------------------------------------------------------------ fotos pessoais
def escolher_fotos(n, data_ref, rotacao):
    fotos = [f for f in ler(os.path.join(RAIZ, "acervo", "indice.json"), {}).get("pastas", {}).get("fotos", [])
             if f.get("mimeType", "").startswith("image/")]
    usadas = {u["id"]: u["data"] for u in rotacao.get("fotos", [])}
    if not fotos:
        return []
    ordem = sorted(fotos, key=lambda f: (usadas.get(f["id"], ""),
                                         hashlib.sha1(f"{data_ref}{f['id']}".encode()).hexdigest()))
    return ordem[:n]


def preparar_foto(arq, destino_local, destino_bucket, simular):
    """Baixa do Drive, corrige a rotação do celular, enquadra no limite do feed (4:5 a 1,91:1) e sobe."""
    from PIL import Image, ImageOps
    url = f"https://www.googleapis.com/drive/v3/files/{arq['id']}?alt=media&key={urllib.parse.quote(os.environ['GDRIVE_API_KEY'])}"
    with urllib.request.urlopen(url, timeout=300) as r:
        im = ImageOps.exif_transpose(Image.open(io.BytesIO(r.read()))).convert("RGB")
    w, h = im.size
    if w / h < 0.8:  # mais alta que 4:5: corta em cima e embaixo (sem filtro, sem edição)
        nh = int(w / 0.8)
        topo = (h - nh) // 2
        im = im.crop((0, topo, w, topo + nh))
    elif w / h > 1.91:
        nw = int(h * 1.91)
        esq = (w - nw) // 2
        im = im.crop((esq, 0, esq + nw, h))
    im.thumbnail((1080, 1350) if im.width <= im.height else (1440, 1080))
    os.makedirs(os.path.dirname(destino_local), exist_ok=True)
    im.save(destino_local, "JPEG", quality=90)
    if simular:
        return
    base = os.environ["SUPABASE_URL"].rstrip("/")
    with open(destino_local, "rb") as f:
        req = urllib.request.Request(f"{base}/storage/v1/object/midia/{urllib.parse.quote(destino_bucket)}",
                                     data=f.read(), method="POST",
                                     headers={"apikey": os.environ["SUPABASE_SERVICE_KEY"],
                                              "Content-Type": "image/jpeg", "x-upsert": "true"})
    urllib.request.urlopen(req, timeout=120).read()


# ------------------------------------------------------------ principal
def main(argv):
    cfg = ler(CFG, {})
    hoje = dt.date.fromisoformat(argv[argv.index("--hoje") + 1]) if "--hoje" in argv else dt.datetime.now(BRT).date()
    simular = "--simular" in argv or not cfg.get("ativo")
    ciclos = ler(CICLOS, [])
    if ciclos:
        inicio = dt.date.fromisoformat(ciclos[-1]["fim"]) + dt.timedelta(days=1)
    elif cfg.get("inicio"):
        inicio = dt.date.fromisoformat(cfg["inicio"])
    else:
        inicio = hoje + dt.timedelta(days=1)  # só na simulação
    if inicio <= hoje:  # ciclo perdido: começa amanhã
        inicio = hoje + dt.timedelta(days=1)
    vespera = inicio - dt.timedelta(days=1)
    if not simular and hoje != vespera:
        print(f"Hoje não é véspera de ciclo (próximo começa em {inicio}).")
        return 0
    fim = inicio + dt.timedelta(days=cfg["dias"] - 1)

    agora = dt.datetime.combine(hoje, dt.time(14, 50), BRT) if "--hoje" in argv else dt.datetime.now(BRT)
    itens = noticias(agora, 72)
    pts, base, bonus = pontuar(itens, cfg, pesos_fontes(), inicio, fim)
    sigla, regra = escolher(pts, ciclos, cfg)

    famosos = []
    for h in (24, 72, 168):
        famosos = [{"nome": it["pessoa"], "noticia_id": it["id"], "titulo": it.get("titulo"), "link": it.get("link"),
                    "canal": it.get("canal"), "data": it.get("publicado_em"), "nota": it.get("nota")}
                   for it in noticias(agora, h) if it.get("pessoa") and tema_do_item(it, cfg) == sigla]
        if famosos:
            break
    famosos.sort(key=lambda f: -(f.get("nota") or 0))

    rotacao = ler(ROTACAO, {"trechos": [], "fotos": []})
    fotos = []
    for n, arq in zip(cfg["foto_dias"], escolher_fotos(len(cfg["foto_dias"]), inicio.isoformat(), rotacao)):
        dia = (inicio + dt.timedelta(days=n - 1)).isoformat()
        bucket = f"{dia}/foto-pessoal.jpg"
        preparar_foto(arq, os.path.join(RAIZ, "ciclos", "fotos", f"{dia}.jpg"), bucket, simular)
        fotos.append({"dia": dia, "quando": f"{dia}T{cfg['foto_hora']}:00-03:00", "arquivo": bucket,
                      "previa": f"ciclos/fotos/{dia}.jpg", "drive_id": arq["id"], "nome": arq["name"]})
        if not simular:
            rotacao.setdefault("fotos", []).append({"id": arq["id"], "nome": arq["name"], "data": dia})

    ciclo = {"id": f"c-{inicio}", "inicio": inicio.isoformat(), "fim": fim.isoformat(),
             "tema": cfg["temas"][sigla], "sigla": sigla,
             "pontuacao": dict(sorted(pts.items(), key=lambda x: -x[1])),
             "excluidos": [c["sigla"] for c in ciclos[-2:]], "regra": regra, "bonus_calendario": bonus,
             "noticias_base": base[sigla][:15], "famosos": famosos[:8], "fotos": fotos,
             "escolhido_em": agora.isoformat(timespec="minutes"), "status": "escolhido"}
    if simular:
        gravar(SIMULACAO, ciclo)
        print(f"[simulação] {inicio}–{fim}: {sigla} · {ciclo['pontuacao']}")
        return 0
    ciclos.append(ciclo)
    gravar(CICLOS, ciclos)
    gravar(ROTACAO, rotacao)
    print(f"Ciclo {ciclo['id']} ({inicio}–{fim}): {ciclo['tema']} · {len(famosos)} notícia(s) com pessoa · {len(fotos)} foto(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
