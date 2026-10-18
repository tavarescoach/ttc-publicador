"""Gera telas de story 1080x1920 (identidade LT) a partir de um JSON.

Uso: python render/story.py render/stories/<data>.json
O JSON é uma lista: [{"arquivo": "midia/2026-10-19/story-1.png", "rotulo": "...", "titulo": "...",
  "texto": "...", "topo": 660, "vaga": {"y": 1150, "h": 300, "txt": "..."}}]
"vaga" marca a área onde o Luan põe o sticker no app (só em telas de fundo para story manual).
"""
import json
import os
import sys
import urllib.parse

from playwright.sync_api import sync_playwright

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)


def main(caminho):
    telas = json.load(open(caminho, encoding="utf-8"))
    with sync_playwright() as p:
        nav = p.chromium.launch()
        pg = nav.new_page(viewport={"width": 1080, "height": 1920})
        for t in telas:
            pg.goto("file://" + os.path.join(AQUI, "story.html") + "#" + urllib.parse.quote(json.dumps(t)))
            pg.reload()
            pg.wait_for_timeout(400)
            destino = os.path.join(RAIZ, t["arquivo"])
            os.makedirs(os.path.dirname(destino), exist_ok=True)
            pg.screenshot(path=destino)
            print("ok", t["arquivo"])
        nav.close()


if __name__ == "__main__":
    main(sys.argv[1])
