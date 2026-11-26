"""Stories automáticos de um dia (diretrizes/stories.md, bloco v3).

Uso: python acervo/stories.py AAAA-MM-DD [--ensaio] [--local DIR]

Modelo v3 ("modelo": "v3" em acervo/config.json), Linha Editorial v3 de 26/11/2026. Texto do dia em
ciclos/stories/<data>.json, escrito pelo pacote do ciclo (PIPELINE.md). Gera:
- 07:30 Abertura: só o título com a ideia central (time-lapse de trabalho, ou foto);
- 10:00 Virada: a decisão + fonte do artigo (foto);
- 12:05 Post novo: capa do carrossel das 12h como cartão (foto de fundo), só se o carrossel estiver na fila;
- 13:00 Resultado e critério (time-lapse de treino, ou foto);
- 21:00 Convite: "Responde este story com <palavra do tema>..." (foto).
Foto = pasta "banco" (fotos de banco de imagem) ou "fotos" do acervo, sem repetir em 14 dias.
Sem o plano do dia, sai só o Post novo e o resumo avisa "sem plano".

Modelo v2 (arco antigo, só para voltar atrás): 06:00 bom dia, 08:00 ponte do estático, 10:00 CTA MÉTODO,
12:30 ponte do carrossel. Ponte só sai se o post existir na fila; vídeo só sai se houver vídeo no acervo.

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
import re
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
PLANOS = os.path.join(RAIZ, "ciclos", "stories")
TAGS = os.path.join(AQUI, "tags.json")
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
    """Partes do story, em ordem: trechos usados há mais tempo.

    Nunca: mesmo vídeo no mesmo slot no dia anterior; mesmo trecho em 30 dias (se faltar, relaxa).
    Clipe curto (o acervo de treino tem muitos de 1 a 4 s): junta clipes de vídeos diferentes até ~12 s,
    cada um com no máximo `parte_max_s`.
    """
    pasta = {"trabalho": "timelapse-trabalho", "treino": "timelapse-treino"}[slot]
    videos, vistos_chave = [], set()
    for a in indice.get("pastas", {}).get(pasta, []):
        if not a.get("mimeType", "").startswith("video/") or duracao_s(a) < cfg.get("clipe_min_s", 1):
            continue
        # cópias do mesmo arquivo ("nome (1).mp4", mesmo tamanho) contam uma vez só
        chave = (re.sub(r" \(\d+\)(?=\.\w+$)", "", a.get("name", "")).lower(), a.get("size"))
        if chave in vistos_chave:
            continue
        vistos_chave.add(chave)
        videos.append(a)
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
    livres.sort(key=lambda c: c["chave"])
    alvo, parte_max = cfg["trecho_s"], cfg.get("parte_max_s", 4)
    partes, total, vistos = [], 0.0, set()
    for c in livres:
        saida = c["janela"] / c["fator"]
        if not partes and saida >= alvo - 2:  # trecho longo: sozinho
            return [dict(c, saida=min(saida, alvo))]
        if c["video"]["id"] in vistos:
            continue
        c = dict(c, saida=min(saida, parte_max))
        c["janela"] = c["saida"] * c["fator"]
        partes.append(c)
        vistos.add(c["video"]["id"])
        total += c["saida"]
        if total >= alvo - 1 or len(partes) >= cfg.get("partes_max", 6):
            break
    return partes


# ------------------------------------------------------------ fotos (v3)
FOTO_OK = ("image/jpeg", "image/png")


def candidatas_foto(indice, tags, cfg3):
    """Fotos que podem ir ao fundo de um story: banco + acervo, sem `evitar`, sem camisa nem aluno sem autorização."""
    fotos = []
    for pasta in cfg3["pastas_foto"]:
        for a in indice.get("pastas", {}).get(pasta, []):
            if a.get("mimeType") not in FOTO_OK:
                continue
            t = tags.get(a["id"], {}) if isinstance(tags.get(a["id"]), dict) else {}
            if t.get("evitar") or t.get("sem_camisa") or (t.get("aluno") and not t.get("autorizado")):
                continue
            fotos.append(dict(a, pasta=pasta))
    return fotos


def escolher_foto(tela, data, fotos, rotacao, usadas_hoje, cfg3):
    """A foto usada há mais tempo (nunca antes = primeiro), sem repetir no dia nem em `repetir_foto_apos_dias`."""
    if not fotos:
        return None
    ultimo = {}
    for u in rotacao.get("fotos", []):  # mesma lista do feed (ciclo/escolher.py): story e post não repetem foto
        fid = u.get("id") or u.get("foto")
        ultimo[fid] = max(ultimo.get(fid, ""), u.get("data", ""))
    limite = (dt.date.fromisoformat(data) - dt.timedelta(days=cfg3["repetir_foto_apos_dias"])).isoformat()
    livres = [f for f in fotos if f["id"] not in usadas_hoje]
    boas = [f for f in livres if ultimo.get(f["id"], "") < limite] or livres or fotos
    chave = lambda f: (ultimo.get(f["id"], ""), hashlib.sha1(f"{data}{tela}{f['id']}".encode()).hexdigest())  # noqa: E731
    return sorted(boas, key=chave)[0]


def baixar_foto(arq, destino, local_dir=None):
    if local_dir:
        shutil.copy(os.path.join(local_dir, arq["name"]), destino)
        return
    url = f"{DRIVE}/{arq['id']}?alt=media&key={urllib.parse.quote(os.environ['GDRIVE_API_KEY'])}"
    with urllib.request.urlopen(url, timeout=300) as r, open(destino, "wb") as f:
        shutil.copyfileobj(r, f)


# ------------------------------------------------------------ mídia
def baixar_video(arq, destino, local_dir=None):
    if local_dir:
        shutil.copy(os.path.join(local_dir, arq["name"]), destino)
        return
    url = f"{DRIVE}/{arq['id']}?alt=media&key={urllib.parse.quote(os.environ['GDRIVE_API_KEY'])}"
    with urllib.request.urlopen(url, timeout=600) as r, open(destino, "wb") as f:
        shutil.copyfileobj(r, f)


def montar_video(origens, camada_png, partes, saida):
    """Corta cada parte, acelera, enquadra em 1080x1920, emenda, grava a camada de texto e comprime (sem áudio).
    camada_png None: só a base (para achar o rosto antes de posicionar o texto)."""
    cmd, filtros = ["ffmpeg", "-y", "-loglevel", "error"], []
    for i, (o, t) in enumerate(zip(origens, partes)):
        cmd += ["-ss", f"{t['inicio']:.2f}", "-t", f"{t['janela']:.2f}", "-i", o]
        filtros.append(f"[{i}:v]setpts=(PTS-STARTPTS)/{t['fator']},scale=1080:1920:force_original_aspect_ratio=increase,"
                       f"crop=1080:1920,fps=30,setsar=1,format=yuv420p[p{i}]")
    n = len(partes)
    filtro = ";".join(filtros) + ";" + "".join(f"[p{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[v]"
    if camada_png:
        cmd += ["-i", camada_png]
        filtro += f";[v][{n}:v]overlay=0:0[o]"
    else:
        filtro += ";[v]null[o]"
    total = sum(t["saida"] for t in partes)
    cmd += ["-filter_complex", filtro, "-map", "[o]", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-t", f"{total:.2f}", saida]
    subprocess.run(cmd, check=True)
    if os.path.getsize(saida) > 45 * 1024 * 1024:
        raise RuntimeError(f"{saida} passou de 45 MB")


# Caixa de texto nos vídeos: embaixo por padrão; sobe quando há rosto na faixa de baixo e não na de cima.
CAIXA = {"baixo": (1070, 1560), "cima": (400, 920)}


def onde_tem_rosto(video, amostras=8):
    """Quanto de rosto (área somada nos quadros) cai em cada faixa de CAIXA. Detectores de rosto do OpenCV 4."""
    import cv2
    det = [cv2.CascadeClassifier(cv2.data.haarcascades + n)
           for n in ("haarcascade_frontalface_default.xml", "haarcascade_profileface.xml")]
    cap = cv2.VideoCapture(video)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    achou = {k: 0 for k in CAIXA}
    for i in range(amostras):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(total * (i + 0.5) / amostras))
        ok, img = cap.read()
        if not ok:
            continue
        cinza = cv2.equalizeHist(cv2.cvtColor(cv2.resize(img, (540, 960)), cv2.COLOR_BGR2GRAY))
        for d in det:
            for (x, y, w, h) in d.detectMultiScale(cinza, scaleFactor=1.1, minNeighbors=6, minSize=(50, 50)):
                topo, base = y * 2, (y + h) * 2
                for k, (a, b) in CAIXA.items():
                    achou[k] += max(0, min(base, b) - max(topo, a)) * w * 2  # área do rosto dentro da faixa
    cap.release()
    return achou


def posicao_texto(video):
    try:
        r = onde_tem_rosto(video)
    except Exception as e:  # sem OpenCV ou vídeo ilegível: posição padrão
        print(f"[aviso] detecção de rosto falhou ({e}); texto embaixo")
        return "baixo", {}
    return ("cima" if r["baixo"] > r["cima"] * 1.2 else "baixo"), r


def gravar_camada(base, camada_png, saida):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", base, "-i", camada_png, "-filter_complex",
                    "[0:v][1:v]overlay=0:0[o]", "-map", "[o]", "-an", "-c:v", "libx264", "-preset", "veryfast",
                    "-crf", "24", "-pix_fmt", "yuv420p", "-movflags", "+faststart", saida], check=True)
    if os.path.getsize(saida) > 45 * 1024 * 1024:
        raise RuntimeError(f"{saida} passou de 45 MB")


def story_em_video(s, tela, tmp, nome, local_dir=None):
    """Monta o vídeo do story: base, rosto, camada de texto na faixa livre. Devolve (arquivo, posição)."""
    from story import renderizar
    origens = []
    for t in s["trecho"]:
        origem = os.path.join(tmp, f"origem-{t['video']['id']}")
        if not os.path.exists(origem):
            baixar_video(t["video"], origem, local_dir)
        origens.append(origem)
    base = os.path.join(tmp, f"base-{nome}.mp4")
    montar_video(origens, None, s["trecho"], base)
    pos, rostos = posicao_texto(base)
    camada = os.path.join(tmp, f"camada-{nome}.png")
    lugar = ({"ancora": pos, "topo": CAIXA["cima"][0]} if tela.get("modelo") == "v3" else {"topo": CAIXA[pos][0]})
    renderizar([{**tela, "arquivo": os.path.relpath(camada, RAIZ), "transparente": True, **lugar}])
    local = os.path.join(tmp, f"story-{nome}.mp4")
    gravar_camada(base, camada, local)
    print(f"story {nome}: texto {pos} (rostos {rostos})")
    return local, pos


def quadro(video, saida_jpg):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "1.5", "-i", video, "-frames:v", "1",
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
def ler_plano(data):
    """Texto do dia (ciclos/stories/<data>.json), escrito pelo pacote do ciclo. None se não existir."""
    return ler(os.path.join(PLANOS, f"{data}.json"), None)


def planejar_v3(data, cfg, indice, rotacao, fila, tags):
    """Arco v3: abertura, virada, post novo, resultado, convite. Devolve (plano, avisos)."""
    c3 = cfg["v3"]
    h, rot, midia = c3["horarios"], c3["rotulos"], c3["midia"]
    q = lambda hm: f"{data}T{hm}:00-03:00"  # noqa: E731
    texto = ler_plano(data)
    avisos = [] if texto else [f"Sem plano de stories (ciclos/stories/{data}.json): só sai o Post novo."]
    texto = texto or {}
    serie, palavra, tema = texto.get("serie", ""), (texto.get("palavra") or "").strip().upper(), texto.get("tema")
    fotos = candidatas_foto(indice, tags, c3)
    por_id = {f["id"]: f for f in fotos}
    usadas = set()
    plano = []

    def fundo(tela):
        """Mídia da tela: vídeo do slot (se houver) ou foto. Foto pedida no plano (URL ou drive_id) tem prioridade."""
        pedida = (texto.get("fotos") or {}).get(tela)
        if pedida:
            if str(pedida).startswith("http"):
                return {"fundo_url": pedida}
            if pedida in por_id:
                usadas.add(pedida)
                return {"foto": por_id[pedida]}
            avisos.append(f"{tela}: foto pedida no plano não está no acervo ({pedida}); escolhi outra.")
        tipo = midia.get(tela, "foto")
        if tipo.startswith("video:"):
            t = escolher_trecho(tipo.split(":", 1)[1], data, indice, rotacao, cfg)
            if t:
                return {"slot": tipo.split(":", 1)[1], "trecho": t}
        f = escolher_foto(tela, data, fotos, rotacao, usadas, c3)
        if f:
            usadas.add(f["id"])
            return {"foto": f}
        avisos.append(f"{tela}: sem foto nem vídeo no acervo; fundo liso.")
        return {}

    base = {"modelo": "v3", "tema": tema, "serie": serie, "palavra": palavra}
    if texto.get("abertura"):
        a = texto["abertura"]
        plano.append({**base, "id": f"{data}-st-0730", "tela": "abertura", "quando": q(h["abertura"]),
                      "aponta": "respostas", "rotulo": serie, "titulo": a["titulo"], **fundo("abertura")})
    if texto.get("virada"):
        v = texto["virada"]
        plano.append({**base, "id": f"{data}-st-1000", "tela": "virada", "quando": q(h["virada"]), "aponta": "respostas",
                      "rotulo": rot["virada"], "titulo": v["titulo"], "fonte": v.get("fonte"), "link": v.get("link"),
                      **fundo("virada")})
    car = post_do_dia(fila, data, "CARROSSEL", 12)
    if car:
        plano.append({**base, "id": f"{data}-st-1205", "tela": "post_novo", "quando": q(h["post_novo"]), "aponta": "post",
                      "post_id": car["id"], "rotulo": rot["post_novo"], "titulo": c3["post_novo"]["titulo"],
                      "imagem": f"{MIDIA_BASE}/{car['arquivos'][0]}", "tema": tema or car.get("tema"),
                      **fundo("post_novo")})
    if texto.get("resultado"):
        r = texto["resultado"]
        plano.append({**base, "id": f"{data}-st-1300", "tela": "resultado", "quando": q(h["resultado"]),
                      "aponta": "respostas", "rotulo": rot["resultado"], "titulo": r["titulo"],
                      "texto": r.get("criterio"), "fonte": r.get("fonte"), "link": r.get("link"),
                      **fundo("resultado")})
    if palavra or texto.get("convite"):
        cv = texto.get("convite") or {}
        titulo = cv.get("titulo") or c3["convite_padrao"].format(palavra=palavra)
        plano.append({**base, "id": f"{data}-st-2100", "tela": "convite", "quando": q(h["convite"]), "aponta": "direct",
                      "rotulo": rot["convite"], "titulo": titulo, **fundo("convite")})
    return plano, avisos


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

    est = post_do_dia(fila, data, "IMAGEM", 7) or post_do_dia(fila, data, "CARROSSEL", 7)
    if est:  # estático do ciclo chama o carrossel do meio-dia; carrossel das 7h (Estúdio) usa a ponte de carrossel
        p = cfg["pontes"]["ponte_estatico" if est["tipo"] == "IMAGEM" else "ponte_carrossel"]
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
    inicio = cfg.get("inicio_stories") or (ler(os.path.join(RAIZ, "ciclo", "config.json"), {}) or {}).get("inicio")
    if inicio and data < inicio:
        ensaio = True  # antes do primeiro ciclo: só prévia
    local_dir = argv[argv.index("--local") + 1] if "--local" in argv else None
    from story import renderizar  # playwright só quando precisa

    ja = {i.get("id") for i in fila}
    v3 = cfg.get("modelo") == "v3"
    if v3:
        plano, avisos = planejar_v3(data, cfg, indice, rotacao, fila, ler(TAGS, {}))
    else:
        plano, avisos = planejar(data, cfg, indice, rotacao, fila), []
    plano = [s for s in plano if s["id"] not in ja]
    for a in avisos:
        print(f"[aviso] {a}")
    previas = os.path.join(RAIZ, "render", "previas", "stories", data)
    if not plano:
        print("Nada a gerar (sem plano, sem vídeo no acervo e sem post do dia, ou já gerado).")
        if avisos:
            gravar(os.path.join(previas, "resumo.json"), {"data": data, "ensaio": ensaio, "avisos": avisos, "stories": []})
        return 0

    os.makedirs(previas, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="stories-")
    resumo = []
    for s in plano:
        rev = revisar_story(s)
        video = "trecho" in s
        nome = f"{s['id'].split('-st-')[1]}"
        arq_bucket = f"{data}/story-{nome}.{'mp4' if video else 'png'}"
        tela = {k: s[k] for k in ("rotulo", "titulo", "texto", "imagem", "fonte", "modelo") if s.get(k)}
        pos = None
        if video:
            local, pos = story_em_video(s, tela, tmp, nome, local_dir)
            quadro(local, os.path.join(previas, f"story-{nome}.jpg"))
        else:
            local = os.path.join(tmp, f"story-{nome}.png")
            if v3:
                extra = {"ancora": "baixo"}
                if s.get("foto"):
                    origem = os.path.join(tmp, f"foto-{s['foto']['id']}")
                    if not os.path.exists(origem):
                        baixar_foto(s["foto"], origem, local_dir)
                    extra["fundo"] = "file://" + origem
                elif s.get("fundo_url"):
                    extra["fundo"] = s["fundo_url"]
                if s.get("imagem"):  # post novo: texto em cima, cartão embaixo
                    extra = {**extra, "ancora": None, "topo": 500, "imagem_topo": 950}
            else:
                extra = {"topo": 1220, "imagem_topo": 360}
            renderizar([{**tela, **extra, "arquivo": os.path.relpath(local, RAIZ)}])
            shutil.copy(local, os.path.join(previas, f"story-{nome}.png"))

        etapa = rev["decisao"] if rev["decisao"] == "agendado" else "pronto"
        resumo.append({"id": s["id"], "tela": s.get("tela"), "quando": s["quando"], "arquivo": arq_bucket,
                       "decisao": rev["decisao"], "texto": pos, "problemas": rev["problemas"],
                       "foto": (s.get("foto") or {}).get("name") or s.get("fundo_url"),
                       "partes": [{"video": t["video"]["name"], "k": t["k"], "s": round(t["saida"], 1)}
                                  for t in s["trecho"]] if video else None})
        if ensaio:
            continue
        subir(local, arq_bucket, "video/mp4" if video else "image/png")
        import render as rnd  # noqa: E402  (grava card e revisão como os carrosséis)
        rnd.salvar_revisao(rev)
        legenda = f"Palavra do dia: {s['palavra']}" if s.get("tela") == "convite" and s.get("palavra") else ""
        rnd.gravar_card({"id": s["id"], "data": data, "quando": s["quando"], "pauta": _limpo(s["titulo"]),
                         "legenda": legenda, "tema": s.get("tema")}, [arq_bucket], tipo="STORY", etapa=etapa)
        if video:
            for t in s["trecho"]:
                rotacao.setdefault("trechos", []).append({"data": data, "slot": s["slot"], "video": t["video"]["id"],
                                                          "nome": t["video"]["name"], "k": t["k"]})
        if s.get("foto"):
            rotacao.setdefault("fotos", []).append({"id": s["foto"]["id"], "nome": s["foto"]["name"], "data": data,
                                                    "uso": f"story-{s['tela']}"})
        if s.get("tela") == "convite" and s.get("palavra"):
            registrar_palavra(data, s["palavra"], s.get("serie"))
    if not ensaio:
        import render as rnd  # noqa: E402
        rnd.publicar_revisoes()
        gravar(ROTACAO, rotacao)
    gravar(os.path.join(previas, "resumo.json"), {"data": data, "ensaio": ensaio, "modelo": "v3" if v3 else "v2",
                                                  "avisos": avisos, "stories": resumo})
    shutil.rmtree(tmp, ignore_errors=True)
    for r in resumo:
        print(f"{r['quando'][11:16]} {r['id']}: {r['decisao']} {'; '.join(r['problemas'])}")
    return 0


PALAVRAS = os.path.join(RAIZ, "metricas", "palavras.json")


def registrar_palavra(data, palavra, serie):
    """Palavra-chave do convite por dia e origem: o painel conta as conversas por palavra (Linha Editorial v3)."""
    reg = ler(PALAVRAS, {"_doc": "Palavra-chave de CTA por dia e origem. Stories: palavra do tema do dia.", "itens": []})
    reg["itens"] = [i for i in reg.get("itens", []) if not (i.get("data") == data and i.get("origem") == "stories")]
    reg["itens"].append({"data": data, "origem": "stories", "palavra": palavra, "serie": serie})
    gravar(PALAVRAS, reg)


def _limpo(t):
    return (t or "").replace("**", "")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
