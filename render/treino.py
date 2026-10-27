"""Gera a arte de treino (foto do Luan + números do report) no estilo "pop-out" do story do Strava.

Uso: python render/treino.py render/treinos/<data>.json [--subir]
O JSON é um objeto, ou uma lista deles:
{"arquivo": "midia/2026-10-27/treino-story.png", "formato": "story" | "feed",
 "foto": "treinos/fotos/2026-10-27.jpg", "foco": "50% 30%", "data": "27 out 2026",
 "palavra": "PERNAS", "palavra_base": 0.85,
 "metricas": [{"rotulo": "Distância", "valor": "6,51", "unidade": "km", "destaque": false}],
 "rota": [[0.12, 0.55], [0.3, 0.48]], "dados_topo": 340, "lado_a_lado": false}
"foto" é relativo a render/. "foco" é o object-position da foto. "palavra" é o texto gigante atrás do Luan
("" para não ter). "rota" são pontos de 0 a 1 (x, y) da linha vermelha, desenhada atrás do Luan.
O recorte do Luan é gerado com rembg na primeira vez e guardado ao lado da foto (<nome>-recorte.png).
Com --subir, cada PNG vai para o bucket "midia" do Supabase (mesmo esquema de render/story.py).
"""
import json
import os
import sys
import urllib.parse

from playwright.sync_api import sync_playwright

from story import subir

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)


def recortar(foto):
    """Recorte do Luan (fundo transparente), feito uma vez por foto."""
    base, _ = os.path.splitext(foto)
    rel = base + "-recorte.png"
    destino = os.path.join(AQUI, rel)
    if not os.path.exists(destino):
        from PIL import Image, ImageOps
        from rembg import new_session, remove
        im = ImageOps.exif_transpose(Image.open(os.path.join(AQUI, foto)))
        remove(im, session=new_session("u2net_human_seg")).save(destino)
    return rel


def renderizar(artes, enviar=False):
    with sync_playwright() as p:
        nav = p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH"))
        for a in artes:
            if "recorte" not in a and not a["foto"].startswith("http"):
                a["recorte"] = recortar(a["foto"])
            altura = 1350 if a.get("formato") == "feed" else 1920
            pg = nav.new_page(viewport={"width": 1080, "height": altura})
            pg.goto("file://" + os.path.join(AQUI, "treino.html") + "#" + urllib.parse.quote(json.dumps(a)))
            pg.wait_for_function("document.body.dataset.pronto && [...document.images].every(i => i.complete)", timeout=20000)
            pg.wait_for_timeout(300)
            destino = os.path.join(RAIZ, a["arquivo"])
            os.makedirs(os.path.dirname(destino), exist_ok=True)
            pg.screenshot(path=destino)
            if enviar:
                subir(destino, a["arquivo"].removeprefix("midia/"))
            print("ok", a["arquivo"])
            pg.close()
        nav.close()


if __name__ == "__main__":
    dados = json.load(open(sys.argv[1], encoding="utf-8"))
    renderizar(dados if isinstance(dados, list) else [dados], "--subir" in sys.argv)
