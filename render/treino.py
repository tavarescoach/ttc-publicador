"""Gera a arte de treino (foto do Luan + números do report) no estilo "pop-out" do story do Strava.

Uso: python render/treino.py render/treinos/<data>.json [--subir]
O JSON é um objeto, ou uma lista deles:
{"arquivo": "midia/2026-10-27/treino-story.png", "formato": "story" | "feed",
 "foto": "treinos/fotos/2026-10-27.jpg", "foco": "50% 30%", "data": "27 out 2026",
 "palavra": "PERNAS", "palavra_base": 0.85,
 "metricas": [{"rotulo": "Distância", "valor": "6,51", "unidade": "km", "destaque": false}],
 "rota": [[0.12, 0.55], [0.3, 0.48]], "dados_topo": 330, "fundo": "desfoque", "pessoa": {"base": 1.08},
 "musica": {"titulo": "Pump It", "artista": "Black Eyed Peas", "progresso": 0.7},
 "rota_img": "treinos/rotas/2026-10-27.png", "rota_caixa": [0.5, 0.6, 0.85]}
"foto" é relativo a render/. "foco" é o object-position da foto. "palavra" é o texto gigante atrás do Luan
("" para não ter). "rota" são pontos de 0 a 1 (x, y) da linha vermelha, desenhada atrás do Luan.
"rota_img" é a rota exportada do Strava (PNG transparente): cortada, pintada de vermelho e posta em
"rota_caixa" = [centro x, centro y, largura], frações da arte (padrão [0.5, 0.55, 0.95]).
"fundo": "desfoque" (padrão: a foto desfocada e escurecida no azul da marca, com o Luan nítido por cima,
posto conforme "pessoa": {"largura": 1, "x": 0.5, "base": 1.08}: largura em fração da arte, base é onde fica
borda de baixo da foto (1 = rente à base; acima de 1 desce e corta embaixo, sem mostrar as bordas da foto)) ou "foto" (a foto nítida
em tela cheia; só para fotos com fundo limpo, como céu). "contorno": false tira a palavra vazada por cima do Luan.
"musica": {"titulo", "artista", "capa" (opcional, relativo a render/), "tempo", "resta", "progresso" 0-1, "topo" px}
desenha o cartão de "tocando agora". "dados_coluna": true empilha os números em vez de pô-los em linha.
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
        remove(im, session=new_session("birefnet-portrait")).save(destino)
    return rel


def preparar_rota(imagem):
    """Rota exportada do app (PNG transparente): corta no traçado e pinta no vermelho da marca."""
    from PIL import Image, ImageChops
    base, _ = os.path.splitext(imagem)
    rel = base + "-vermelha.png"
    im = Image.open(os.path.join(AQUI, imagem)).convert("RGBA")
    # só o traçado laranja: o sticker do Strava traz também os números e a logo em branco
    r, g, b, a = im.split()
    mascara = ImageChops.subtract(r, b).point(lambda v: 255 if v > 90 else 0)
    alfa = ImageChops.multiply(a, mascara)
    alfa = alfa.crop(alfa.getbbox())
    vermelha = Image.new("RGBA", alfa.size, (229, 56, 59, 255))
    vermelha.putalpha(alfa)
    vermelha.save(os.path.join(AQUI, rel))
    return rel


def renderizar(artes, enviar=False):
    with sync_playwright() as p:
        nav = p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH"))
        for a in artes:
            if "recorte" not in a and not a["foto"].startswith("http"):
                a["recorte"] = recortar(a["foto"])
            if a.get("rota_img"):
                a["rota_img"] = preparar_rota(a["rota_img"])
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
