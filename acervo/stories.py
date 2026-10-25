"""Stories automáticos de um dia do ciclo temático (diretrizes/ciclo.md, seções 3 e 4).

Uso: python acervo/stories.py AAAA-MM-DD [--ensaio] [--local DIR]

Gera, para o dia:
- 06:00 time-lapse de trabalho + frase de bom dia (vídeo);
- 08:00 ponte para o estático das 7h (imagem com a arte do post);
- 10:00 time-lapse de treino + CTA MÉTODO (vídeo);
- 12:30 ponte para o carrossel das 12h (imagem com a capa).
Ponte só sai se o post existir na fila; vídeo só sai se houver vídeo no acervo.

Cada story passa por render/revisar.py (revisar_story). Passou: card "agendado" no painel (o robô de publicação
importa e publica). Não passou: card "pronto" (Precisa de você) com o motivo.

--ensaio: não sobe nada, não grava card nem rotação; deixa prévias em render/previas/stories/<data>/.
--local DIR: lê os vídeos de DIR (nome do arquivo igual ao do Drive) em vez de baixar do Drive. Para testes.
Com "ativo": false em acervo/config.json, roda sempre em ensaio.
Precisa: GDRIVE_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY, MIDIA_BASE (fora do ensaio), ffmpeg, playwright.
"""
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(RAIZ, "render"))
from revisar import BRT, revisar_story  # noqa: E402

CONFIG = os.path.join(AQUI, "config.json")
INDICE = os.path.join(AQUI, "indice.json")
ROTACAO = os.path.join(RAIZ, "ciclos", "rotacao.json")
FILA = os.path.join(RAIZ, "fila.json")
DRIVE = "https://www.googleapis.com/drive/v3/files"
MIDIA_BASE = os.environ.get("MIDIA_BASE", "https://txiszakrpssubgvzpdcx.supabase.co/storage/v1/object/public/midia").rstrip("/")


def ler(caminho, padrao):
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return padrao


def gravar(caminho, dados):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=1)
        f.write("\n")


# ------------------------------------------------------------ rotação dos trechos
def duracao_s(arq):
    v = arq.get("videoMediaMetadata") or {}
    return int(v.get("durationMillis") or 0) / 1000


def trechos_do_video(arq, cfg):
    """Trechos possíveis: (k, início em s, janela em s, fator de aceleração)."""
    dur = duracao_s(arq)
    fator = cfg["acelerar"]["fator"] if dur >= cfg["acelerar"]["duracao_minima_s"] else 1
    janela = cfg["trecho_s"] * fator
    n = max(1, int(dur // janela)) if dur else 1
    return [(k, k * janela, min(janela, dur) if dur else janela, fator) for k in range(n)]


def escolher_trecho(slot, data, indice, rotacao, cfg):
    """Trecho usado há mais tempo. Nunca: mesmo vídeo no mesmo slot no dia anterior; mesmo trecho em 30 dias."""
    pasta = {"trabalho": "timelapse-trabalho", "treino": "timelapse-treino"}[slot]
    videos = [a for a in indice.get("pastas", {}).get(pasta, []) if a.get("mimeType", "").startswith("video/")]
    if not videos:
        return None
    hoje = dt.date.fromisoformat(data)
    usos = [u for u in rotacao.get("trechos", []) if u.get("slot") == slot]
    ontem = {u["video"] for u in usos if u["data"] == (hoje - dt.timedelta(days=1)).isoformat()}
    ultimo = {}
    for u in usos:
        ultimo[(u["video"], u["k"])] = max(ultimo.get((u["video"], u["k"]), ""), u["data"])
    limite = (hoje - dt.timedelta(days=cfg["repetir_trecho_apos_dias"])).isoformat()
    cand = []
    for v in videos:
        for k, inicio, janela, fator in trechos_do_video(v, cfg):
            usado = ultimo.get((v["id"], k), "")
            vezes_video = sum(1 for u in usos if u["video"] == v["id"])
            sorteio = hashlib.sha1(f"{data}{slot}{v['id']}{k}".encode()).hexdigest()
            cand.append({"video": v, "k": k, "inicio": inicio, "janela": janela, "fator": fator,
                         "usado": usado, "chave": (usado, vezes_video, sorteio),
                         "bloqueado": v["id"] in ontem and len(videos) > 1})
    livres = [c for c in cand if not c["bloqueado"] and c["usado"] < limite] or \
             [c for c in cand if not c["bloqueado"]] or cand
    return min(livres, key=lambda c: c["chave"])


# ------------------------------------------------------------ mídia
def baixar_video(arq, destino, local_dir=None):
    if local_dir:
        shutil.copy(os.path.join(local_dir, arq["name"]), destino)
        return
    url = f"{DRIVE}/{arq['id']}?alt=media&key={urllib.parse.quote(os.environ['GDRIVE_API_KEY'])}"
    with urllib.request.urlopen(url, timeout=600) as r, open(destino, "wb") as f:
        shutil.copyfileobj(r, f)


def montar_video(origem, camada_png, trecho, saida):
    """Corta o trecho, acelera, enquadra em 1080x1920, grava a camada de texto e comprime (sem áudio)."""
    filtro = (f"[0:v]setpts=PTS/{trecho['fator']},scale=1080:1920:force_original_aspect_ratio=increase,"
              f"crop=1080:1920,fps=30[v];[v][1:v]overlay=0:0[o]")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{trecho['inicio']:.2f}", "-t", f"{trecho['janela']:.2f}",
           "-i", origem, "-i", camada_png, "-filter_complex", filtro, "-map", "[o]", "-an",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-pix_fmt", "yuv420p",
           "-movflags", "+faststart", "-t", str(12 if trecho["fator"] > 1 else trecho["janela"]), saida]
    subprocess.run(cmd, check=True)
    if os.path.getsize(saida) > 45 * 1024 * 1024:
        raise RuntimeError(f"{saida} passou de 45 MB")


def quadro(video, saida_jpg):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "3", "-i", video, "-frames:v", "1",
                    "-q:v", "4", saida_jpg], check=True)


def subir(local, destino, tipo):
    url = os.environ["SUPABASE_URL"].rstrip("/")
    with open(local, "rb") as f:
        req = urllib.request.Request(f"{url}/storage/v1/object/midia/{urllib.parse.quote(destino)}", data=f.read(),
                                     method="POST", headers={"apikey": os.environ["SUPABASE_SERVICE_KEY"],
                                                             "Content-Type": tipo, "x-upsert": "true"})
    urllib.request.urlopen(req, timeout=300).read()


# ------------------------------------------------------------ posts do dia
def post_do_dia(fila, data, tipo, hora):
    for i in fila:
        if i.get("tipo") != tipo or i.get("status", "pendente") in ("cancelado",) or not i.get("arquivos"):
            continue
        try:
            q = dt.datetime.fromisoformat(i["quando"]).astimezone(BRT)
        except (KeyError, ValueError):
            continue
        if q.date().isoformat() == data and q.hour == hora:
            return i
    return None


# ------------------------------------------------------------ principal
def planejar(data, cfg, indice, rotacao, fila):
    h = cfg["horarios"]
    q = lambda hm: f"{data}T{hm}:00-03:00"  # noqa: E731
    dia = dt.date.fromisoformat(data).toordinal()
    plano = []

    t = escolher_trecho("trabalho", data, indice, rotacao, cfg)
    if t:
        frase = cfg["frases_bom_dia"][dia % len(cfg["frases_bom_dia"])]
        plano.append({"id": f"{data}-st-0600", "slot": "trabalho", "quando": q(h["trabalho"]), "aponta": "respostas",
                      "rotulo": "Bom dia", "titulo": frase, "trecho": t})

    est = post_do_dia(fila, data, "IMAGEM", 7)
    if est:
        p = cfg["pontes"]["ponte_estatico"]
        plano.append({"id": f"{data}-st-0800", "quando": q(h["ponte_estatico"]), "aponta": "post", "post_id": est["id"],
                      **p, "imagem": f"{MIDIA_BASE}/{est['arquivos'][0]}"})

    t = escolher_trecho("treino", data, indice, rotacao, cfg)
    if t:
        cta = cfg["ctas_treino"][dia % len(cfg["ctas_treino"])]
        plano.append({"id": f"{data}-st-1000", "slot": "treino", "quando": q(h["treino"]), "aponta": "direct",
                      **cta, "trecho": t})

    car = post_do_dia(fila, data, "CARROSSEL", 12)
    if car:
        p = cfg["pontes"]["ponte_carrossel"]
        plano.append({"id": f"{data}-st-1230", "quando": q(h["ponte_carrossel"]), "aponta": "post", "post_id": car["id"],
                      **p, "imagem": f"{MIDIA_BASE}/{car['arquivos'][0]}"})
    return plano


def main(argv):
    data = argv[0]
    cfg, indice = ler(CONFIG, {}), ler(INDICE, {})
    rotacao, fila = ler(ROTACAO, {"trechos": []}), ler(FILA, [])
    ensaio = "--ensaio" in argv or not cfg.get("ativo")
    local_dir = argv[argv.index("--local") + 1] if "--local" in argv else None
    from story import renderizar  # playwright só quando precisa

    ja = {i.get("id") for i in fila}
    plano = [s for s in planejar(data, cfg, indice, rotacao, fila) if s["id"] not in ja]
    if not plano:
        print("Nada a gerar (sem vídeo no acervo e sem post do dia, ou já gerado).")
        return 0

    previas = os.path.join(RAIZ, "render", "previas", "stories", data)
    os.makedirs(previas, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="stories-")
    resumo = []
    for s in plano:
        rev = revisar_story(s)
        video = "trecho" in s
        nome = f"{s['id'].split('-st-')[1]}"
        arq_bucket = f"{data}/story-{nome}.{'mp4' if video else 'png'}"
        tela = {k: s[k] for k in ("rotulo", "titulo", "texto", "imagem") if s.get(k)}
        if video:
            camada = os.path.join(tmp, f"camada-{nome}.png")
            renderizar([{**tela, "arquivo": os.path.relpath(camada, RAIZ), "transparente": True, "topo": 400}])
            origem = os.path.join(tmp, f"origem-{s['trecho']['video']['id']}")
            if not os.path.exists(origem):
                baixar_video(s["trecho"]["video"], origem, local_dir)
            local = os.path.join(tmp, f"story-{nome}.mp4")
            montar_video(origem, camada, s["trecho"], local)
            quadro(local, os.path.join(previas, f"story-{nome}.jpg"))
        else:
            local = os.path.join(tmp, f"story-{nome}.png")
            renderizar([{**tela, "arquivo": os.path.relpath(local, RAIZ), "topo": 1220, "imagem_topo": 360}])
            shutil.copy(local, os.path.join(previas, f"story-{nome}.png"))

        etapa = rev["decisao"] if rev["decisao"] == "agendado" else "pronto"
        resumo.append({"id": s["id"], "quando": s["quando"], "arquivo": arq_bucket, "decisao": rev["decisao"],
                       "problemas": rev["problemas"],
                       "trecho": {"video": s["trecho"]["video"]["name"], "k": s["trecho"]["k"]} if video else None})
        if ensaio:
            continue
        subir(local, arq_bucket, "video/mp4" if video else "image/png")
        import render as rnd  # noqa: E402  (grava card e revisão como os carrosséis)
        rnd.salvar_revisao(rev)
        rnd.gravar_card({"id": s["id"], "data": data, "quando": s["quando"], "pauta": _limpo(s["titulo"]),
                         "legenda": "", "tema": s.get("tema")}, [arq_bucket], tipo="STORY", etapa=etapa)
        if video:
            rotacao.setdefault("trechos", []).append({"data": data, "slot": s["slot"], "video": s["trecho"]["video"]["id"],
                                                      "nome": s["trecho"]["video"]["name"], "k": s["trecho"]["k"]})
    if not ensaio:
        import render as rnd  # noqa: E402
        rnd.publicar_revisoes()
        gravar(ROTACAO, rotacao)
    gravar(os.path.join(previas, "resumo.json"), {"data": data, "ensaio": ensaio, "stories": resumo})
    shutil.rmtree(tmp, ignore_errors=True)
    for r in resumo:
        print(f"{r['quando'][11:16]} {r['id']}: {r['decisao']} {'; '.join(r['problemas'])}")
    return 0


def _limpo(t):
    return (t or "").replace("**", "")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
