"""Gera telas de story 1080x1920 (identidade LT) a partir de um JSON.

Uso: python render/story.py render/stories/<data>.json [--subir]
Com --subir (robô "Renderizar stories"), cada PNG vai para o bucket "midia" do Supabase
no mesmo caminho sem o prefixo midia/ (precisa SUPABASE_URL e SUPABASE_SERVICE_KEY).
O JSON é uma lista: [{"arquivo": "midia/2026-10-19/story-1.png", "rotulo": "...", "titulo": "...",
  "texto": "...", "topo": 660, "vaga": {"y": 1150, "h": 300, "txt": "..."}}]
"vaga" marca a área onde o Luan põe o sticker no app (só em telas de fundo para story manual).
"transparente": true gera PNG sem fundo, para gravar por cima de vídeo (acervo/stories.py).
"imagem": URL ou caminho da arte do post, mostrada como cartão (story-ponte); "imagem_topo" em px.
"""
import json
import os
import sys
import urllib.parse
import urllib.request

from playwright.sync_api import sync_playwright

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)


def subir(local, destino):
    url = os.environ["SUPABASE_URL"].rstrip("/")
    with open(local, "rb") as f:
        req = urllib.request.Request(f"{url}/storage/v1/object/midia/{urllib.parse.quote(destino)}", data=f.read(),
                                     method="POST", headers={"apikey": os.environ["SUPABASE_SERVICE_KEY"],
                                                             "Content-Type": "image/png", "x-upsert": "true"})
    urllib.request.urlopen(req, timeout=60).read()


def main(caminho, enviar=False):
    renderizar(json.load(open(caminho, encoding="utf-8")), enviar)


def renderizar(telas, enviar=False):
    with sync_playwright() as p:
        nav = p.chromium.launch(executable_path=os.environ.get("CHROME_PATH") or None)  # CHROME_PATH: testes locais
        pg = nav.new_page(viewport={"width": 1080, "height": 1920})
        for t in telas:
            pg.goto("file://" + os.path.join(AQUI, "story.html") + "#" + urllib.parse.quote(json.dumps(t)))
            pg.reload()
            pg.evaluate("document.fonts.ready.then(() => true)")
            pg.wait_for_timeout(400)
            if t.get("imagem") or t.get("fundo"):
                pg.wait_for_function("[...document.images].every(i => i.complete)", timeout=20000)
            destino = os.path.join(RAIZ, t["arquivo"])
            os.makedirs(os.path.dirname(destino), exist_ok=True)
            pg.screenshot(path=destino, omit_background=bool(t.get("transparente")))
            if enviar:
                subir(destino, t["arquivo"].removeprefix("midia/"))
            print("ok", t["arquivo"])
        nav.close()


if __name__ == "__main__":
    main(sys.argv[1], "--subir" in sys.argv)
