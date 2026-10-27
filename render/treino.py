"""Gera a arte de treino (foto do Luan + números do report) na identidade LT.

Uso: python render/treino.py render/treinos/<data>.json [--subir]
O JSON é um objeto, ou uma lista deles:
{"arquivo": "midia/2026-10-27/treino-story.png", "formato": "story" | "feed",
 "foto": "treinos/fotos/2026-10-27.jpg", "foco": "50% 30%", "data": "27 out 2026",
 "rotulo": "Treino de hoje", "titulo": "Inferiores, **carga nova**",
 "metricas": [{"rotulo": "Duração", "valor": "62", "unidade": "min", "destaque": true}],
 "frase": "opcional, uma linha", "colunas": 3}
"foto" é relativo a render/ (ou URL). "foco" é o object-position da foto (onde fica o rosto).
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


def renderizar(artes, enviar=False):
    with sync_playwright() as p:
        nav = p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH"))
        for a in artes:
            altura = 1350 if a.get("formato") == "feed" else 1920
            pg = nav.new_page(viewport={"width": 1080, "height": altura})
            pg.goto("file://" + os.path.join(AQUI, "treino.html") + "#" + urllib.parse.quote(json.dumps(a)))
            pg.evaluate("document.fonts.ready.then(() => true)")
            pg.wait_for_function("[...document.images].every(i => i.complete)", timeout=20000)
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
