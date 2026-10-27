"""Gera a arte de treino (foto do Luan + report) no estilo "pop-out" do story do Strava.

Uso: python render/treino.py render/treinos/<data>.json [--subir]
O JSON é um objeto, ou uma lista deles. Campos principais:
  arquivo, formato ("story" | "feed"), foto (relativo a render/), foco (object-position da foto)
  sticker: o PNG que o Strava exporta para o story. É separado em números, rota (laranja) e logo,
    usados como no story feito à mão: números pequenos no alto, rota gigante atrás do Luan,
    logo gigante na base. "dados_sticker": false / "logo_sticker": false descartam números / logo.
  dados_caixa [centro x, topo, largura], rota_caixa [centro x, centro y, largura],
    palavra_caixa [centro x, base, largura]: frações da arte (largura pode passar de 1 e sangrar).
  musica: {"titulo", "subtitulo", "tempo", "resta", "x", "y", "largura"}: widget "tocando agora" do iPhone.
  Sem sticker: "metricas" [{"rotulo", "valor", "unidade"}] e "palavra" (texto) fazem o mesmo papel;
    "rota" (pontos 0-1, cor em "cor_rota", padrão o laranja do Strava) ou "rota_img" (PNG já pronto) desenham a rota.
  fundo: "foto" (padrão, a foto nítida) ou "desfoque" (foto desfocada, com o Luan reduzido conforme
    "pessoa": {"largura", "x", "base"}). marca: true põe a logo LT e o @ no alto.
O recorte do Luan é gerado com rembg (birefnet-portrait) e guardado ao lado da foto (<nome>-recorte.png).
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


def separar_sticker(sticker):
    """Sticker do Strava (PNG transparente 1080x1920) em três peças: números, rota (laranja) e logo.
    Os números e a logo são o branco acima e abaixo do traçado laranja."""
    import numpy as np
    from PIL import Image
    base, _ = os.path.splitext(sticker)
    im = Image.open(os.path.join(AQUI, sticker)).convert("RGBA")
    px = np.array(im).astype(int)
    r, b, a = px[..., 0], px[..., 2], px[..., 3]
    laranja = (a > 20) & (r - b > 90)
    branco = (a > 20) & ~laranja
    linhas = np.where(laranja.any(1))[0]
    if len(linhas):
        topo, fundo = linhas.min(), linhas.max()
    else:
        # atividade sem mapa (esteira, bike indoor): números e logo separados pelo maior vão entre eles
        brancas = np.where(branco.any(1))[0]
        vao = np.argmax(np.diff(brancas))
        topo, fundo = brancas[vao] + 1, brancas[vao + 1] - 1
    pecas = {}
    for nome, mascara in (("rota", laranja), ("dados", branco & (np.arange(im.height)[:, None] < topo)),
                          ("logo", branco & (np.arange(im.height)[:, None] > fundo))):
        if not mascara.any():
            continue
        p = px.copy()
        p[..., 3] = np.where(mascara, p[..., 3], 0)
        peca = Image.fromarray(p.astype("uint8"), "RGBA")
        peca = peca.crop(peca.getbbox())
        if nome != "dados":
            # rota e logo vão ampliadas 3-4x na arte: amplia aqui e endurece a borda para não borrar
            peca = peca.resize((peca.width * 4, peca.height * 4), Image.LANCZOS)
            r_, g_, b_, a_ = peca.split()
            peca = Image.merge("RGBA", (r_, g_, b_, a_.point(lambda v: max(0, min(255, (v - 128) * 3 + 128)))))
        rel = f"{base}-{nome}.png"
        peca.save(os.path.join(AQUI, rel))
        pecas[nome] = rel
    return pecas


def renderizar(artes, enviar=False):
    with sync_playwright() as p:
        nav = p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH"))
        for a in artes:
            if "recorte" not in a and not a["foto"].startswith("http"):
                a["recorte"] = recortar(a["foto"])
            if a.get("sticker"):
                pecas = separar_sticker(a["sticker"])
                a.setdefault("rota_img", pecas.get("rota"))
                if a.get("dados_sticker", True) and "dados" in pecas:
                    a.setdefault("dados_img", pecas["dados"])
                if a.get("logo_sticker", True) and "logo" in pecas:
                    a.setdefault("palavra_img", pecas["logo"])
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
