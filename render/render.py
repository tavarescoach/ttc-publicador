"""Renderiza um carrossel a partir de render/pedidos/<id>.json e entrega para o painel.

Uso: python render/render.py render/pedidos/<id>.json [--local]

Pedido (JSON):
{
  "id": "c-2610171339-y4f-carrossel",        # mesmo id da pauta no painel (a pauta vira "pronto")
  "data": "2026-10-20",                       # pasta da mídia e data sugerida
  "quando": "2026-10-20T12:00:00-03:00",      # horário sugerido (o Luan confirma ao aprovar)
  "pauta": "título curto para o card",
  "legenda": "legenda completa do post",
  "slides": [ {"tipo": "capa|texto_foto|numero|insight|licao|cta", "fundo": "marinho|preto|claro", ...} ]
}
Sem --local: baixa fotos, gera PNGs, sobe para o bucket "midia" do Supabase e grava o card
como "pronto" na tabela conteudos (precisa SUPABASE_URL e SUPABASE_SERVICE_KEY).
"""
import json
import os
import sys
import urllib.parse
import urllib.request

from playwright.sync_api import sync_playwright

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
UA = {"User-Agent": "Mozilla/5.0 (ttc-publicador render)"}


def baixar_foto(url, destino):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r, open(destino, "wb") as f:
        f.write(r.read())


def subir(caminho_local, caminho_bucket):
    with open(caminho_local, "rb") as f:
        req = urllib.request.Request(
            f"{URL}/storage/v1/object/midia/{urllib.parse.quote(caminho_bucket)}",
            data=f.read(), method="POST",
            headers={"apikey": KEY, "Content-Type": "image/png", "x-upsert": "true"})
    urllib.request.urlopen(req, timeout=60).read()


def gravar_card(p, arquivos, capa=None, tipo="CARROSSEL"):
    linha = {
        "id": p["id"], "data": p.get("data"), "tipo": tipo, "pauta": p.get("pauta"),
        "funil": p.get("funil"), "etapa": "pronto", "quando": p.get("quando"),
        "arquivos": arquivos, "legenda": p.get("legenda"), "capa": capa, "link": None, "media_id": None,
    }
    req = urllib.request.Request(
        f"{URL}/rest/v1/conteudos?on_conflict=id", data=json.dumps([linha], ensure_ascii=False).encode(),
        method="POST", headers={"apikey": KEY, "Content-Type": "application/json",
                                "Prefer": "resolution=merge-duplicates,return=minimal"})
    urllib.request.urlopen(req, timeout=60).read()


def main():
    caminho = sys.argv[1]
    local = "--local" in sys.argv
    p = json.load(open(caminho, encoding="utf-8"))
    slides = p["slides"]
    pasta_rel = f"{p['data']}/{p['id']}"
    saida = os.path.join(RAIZ, "render", "_saida", pasta_rel)
    fotos = os.path.join(RAIZ, "render", "_fotos")
    os.makedirs(saida, exist_ok=True)
    os.makedirs(fotos, exist_ok=True)

    reels = p.get("formato") == "reels"
    W, H = (1080, 1920) if reels else (1080, 1350)
    for i, s in enumerate(slides, 1):  # foto do repositório (quadro do vídeo) -> caminho absoluto
        if (s.get("foto") or "").startswith("render/"):
            s["foto"] = "file://" + os.path.join(RAIZ, s["foto"])
    for i, s in enumerate(slides, 1):  # foto remota -> arquivo local; se falhar, slide sem foto
        if (s.get("foto") or "").startswith("http"):
            destino = os.path.join(fotos, f"{p['id']}-{i}.jpg")
            try:
                baixar_foto(s["foto"], destino)
                s["foto"] = "file://" + destino
            except Exception as e:
                print(f"::warning::foto do slide {i} não baixou ({e}); segue sem foto")
                s["foto"] = None

    arquivos = []
    modelo = "file://" + os.path.join(AQUI, "capa-reels.html" if reels else "carrossel.html")
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        pg = nav.new_page(viewport={"width": W, "height": H})
        for i, s in enumerate(slides, 1):
            pg.add_init_script(f"window.SLIDE={json.dumps(s, ensure_ascii=False)};window.TOTAL={len(slides)};window.INDICE={i};")
            pg.goto(modelo)
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(300)
            nome = "reels-capa.png" if reels else f"carrossel-{i}.png"
            pg.screenshot(path=os.path.join(saida, nome))
            arquivos.append(f"{pasta_rel}/{nome}")
            pg.close()
            pg = nav.new_page(viewport={"width": W, "height": H})
            if reels:
                break
        nav.close()
    print(f"{len(arquivos)} slides gerados em {saida}")
    try:  # folha de prévia (para conferência do Claude): render/previas/<id>.jpg
        from PIL import Image
        W, H, n = (300, 533, 1) if reels else (270, 338, len(arquivos))
        cols = 5
        folha = Image.new("RGB", (cols * (W + 6) + 6, ((n + cols - 1) // cols) * (H + 6) + 6), (40, 40, 40))
        for k, a in enumerate(arquivos):
            im = Image.open(os.path.join(RAIZ, "render", "_saida", a)).convert("RGB").resize((W, H))
            folha.paste(im, (6 + (k % cols) * (W + 6), 6 + (k // cols) * (H + 6)))
        os.makedirs(os.path.join(AQUI, "previas"), exist_ok=True)
        folha.save(os.path.join(AQUI, "previas", f"{p['id']}.jpg"), quality=82)
    except Exception as e:
        print(f"[aviso] sem prévia: {e}")

    if local:
        return 0
    for a in arquivos:
        subir(os.path.join(RAIZ, "render", "_saida", a), a)
    if reels:
        gravar_card(p, [p["video"]], capa=arquivos[0], tipo="REELS")
    else:
        gravar_card(p, arquivos)
    print(f"card '{p['id']}' gravado como pronto no painel")
    return 0


if __name__ == "__main__":
    sys.exit(main())
