"""Render da linha Dor → Movimento (diretrizes/dor-movimento.md, v1.1, 26/11/2026).

Chamado por render/render.py quando o pedido tem "formato": "dor_movimento". Também roda sozinho:
    python render/dor_movimento.py render/pedidos/<id>.json --local

Pedido (JSON):
{
  "id": "d-2026-12-01-abd", "data": "2026-12-01", "quando": "2026-12-01T09:00:00-03:00",
  "formato": "dor_movimento", "persona": "rafael", "tema": "ABD", "pauta": "Barriga: 7 dores e 7 movimentos",
  "pares": [
    {"dor": "Encolhe a barriga na foto da praia?", "movimento": "Treine força 3x por semana",
     "foto_dor": "drive:<id>", "foto_movimento": "drive:<id>",
     "foco_dor": "center 30%",        # opcional: sem foco, o robô põe o rosto a 32% da metade
     "ia": false, "rotulo_ia": false}
  ],
  "guia": {"titulo": "Barriga não sai", "titulo_vermelho": "no improviso.", "texto": "No TTC, …", "foto": "drive:<id>"},
  "cta": {"etiqueta": "Salva pra usar essa semana", "titulo": "Quer isso com", "titulo_vermelho": "plano e direção?",
          "texto": "…", "palavra": "MÉTODO", "foto": "drive:<id>"},
  "legenda": "…"
}

Fotos: "drive:<id>" (original do TTC Acervo, nunca a cópia de 1080×1350 do bucket), link https ou caminho do
repositório ("render/…"). Toda foto passa por render/foto_qualidade.py: rosto visível e enquadrado, sem ampliação
e com nitidez mínima. O que falhar vai para "Precisa de você" com o motivo.
"""
import json
import os
import sys
import urllib.parse

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)

MAX_PARES = 8  # 8 pares + guia + CTA = 10, o limite de carrossel da API do Instagram
ALTO_CHEIO = 1440


def _baixar(fonte, destino):
    """Resolve uma foto do pedido para um arquivo local. Devolve o caminho ou levanta erro."""
    import render as R
    if fonte.startswith("drive:"):
        chave = os.environ.get("GDRIVE_API_KEY")
        if not chave:
            raise RuntimeError("falta GDRIVE_API_KEY para baixar o original do Drive")
        fid = fonte.split(":", 1)[1]
        R.baixar_foto(f"https://www.googleapis.com/drive/v3/files/{urllib.parse.quote(fid)}?alt=media&key={urllib.parse.quote(chave)}", destino)
        return destino
    if fonte.startswith("http"):
        R.baixar_foto(fonte, destino)
        return destino
    caminho = fonte[7:] if fonte.startswith("file://") else os.path.join(RAIZ, fonte)
    if not os.path.exists(caminho):
        raise FileNotFoundError(caminho)
    return caminho


def montar_slides(p):
    """Pedido -> lista de slides para o modelo dor-movimento.html (fotos ainda como vieram no pedido)."""
    slides = []
    for par in p.get("pares") or []:
        slides.append({"tipo": "dm_par", "dor": par.get("dor"), "movimento": par.get("movimento"),
                       "foto_dor": par.get("foto_dor"), "foco_dor": par.get("foco_dor"),
                       "foto_mov": par.get("foto_movimento"), "foco_mov": par.get("foco_movimento"),
                       "ia": par.get("ia", False), "rotulo_ia": par.get("rotulo_ia", False)})
    g = p.get("guia") or {}
    slides.append({"tipo": "dm_guia", "etiqueta": g.get("etiqueta") or "O que eu faço com meus alunos",
                   "titulo": g.get("titulo"), "titulo_vermelho": g.get("titulo_vermelho"), "texto": g.get("texto"),
                   "foto": g.get("foto"), "foco": g.get("foco")})
    c = p.get("cta") or {}
    palavra = c.get("palavra") or "MÉTODO"
    slides.append({"tipo": "cta", "etiqueta": c.get("etiqueta") or "Salva pra usar essa semana",
                   "titulo": c.get("titulo"), "titulo_vermelho": c.get("titulo_vermelho"), "texto": c.get("texto"),
                   "cta": f"Me manda {palavra} no direct", "palavra": palavra, "foto": c.get("foto"), "foco": c.get("foco")})
    return slides


def preparar_fotos(p, slides, pasta_fotos):
    """Baixa as fotos, escolhe o foco pelo rosto e confere a qualidade. Devolve (problemas, avisos, hashes)."""
    import render as R
    from foto_qualidade import avaliar, melhor_foco
    from revisar import HASH_PARECIDA, _dist
    problemas, avisos, hashes, vistos = [], [], {}, {}
    campos = (("foto_dor", "foco_dor", "em cima", 720, 0.70), ("foto_mov", "foco_mov", "embaixo", 720, 0.70),
              ("foto", "foco", "", ALTO_CHEIO, 0.58))
    for i, s in enumerate(slides, 1):
        for cf, cfoco, onde, altura, lim in campos:
            if cf not in s:
                continue
            nome = f"Slide {i}" + (f" ({onde})" if onde else "")
            fonte = s.get(cf) or ""
            if not fonte:
                problemas.append(f"{nome}: sem foto.")
                continue
            s[cf + "_origem"] = fonte
            try:
                local = _baixar(fonte, os.path.join(pasta_fotos, f"{p['id']}-{i}-{cf}.jpg"))
            except Exception as e:
                problemas.append(f"{nome}: a foto não baixou ({e}).")
                s[cf] = None
                continue
            s[cf] = "file://" + local
            if not s.get(cfoco):
                alvo = 0.32 if altura == 720 else 0.24
                s[cfoco] = melhor_foco(local, altura, alvo) or "center 30%"
            r = avaliar(local, s[cfoco], altura, lim)
            problemas += [f"{nome}: {x}." for x in r["problemas"]]
            avisos += [f"{nome}: {x}." for x in r["avisos"]]
            try:
                h = R.dhash(local)
                hashes[f"{i} ({onde})" if onde else str(i)] = h
                for outro, h2 in vistos.items():
                    if _dist(h, h2) <= HASH_PARECIDA:
                        problemas.append(f"{nome}: a mesma foto já está em {outro} deste carrossel.")
                        break
                vistos[nome] = h
            except Exception as e:
                print(f"[aviso] sem impressão da foto de {nome}: {e}")
    return problemas, avisos, hashes


def renderizar(p, local=False):
    import render as R
    from playwright.sync_api import sync_playwright
    from revisar import revisar

    slides = p["slides"] = montar_slides(p)
    pasta_rel = f"{p['data']}/{p['id']}"
    saida = os.path.join(RAIZ, "render", "_saida", pasta_rel)
    fotos = os.path.join(RAIZ, "render", "_fotos")
    os.makedirs(saida, exist_ok=True)
    os.makedirs(fotos, exist_ok=True)

    prob_fotos, av_fotos, hashes = preparar_fotos(p, slides, fotos)
    cortes, arquivos = [], []
    modelo = "file://" + os.path.join(AQUI, "dor-movimento.html")
    with sync_playwright() as pw:
        nav = pw.chromium.launch(args=["--allow-file-access-from-files"])
        for i, s in enumerate(slides, 1):
            pg = nav.new_page(viewport={"width": 1080, "height": 1440})
            pg.add_init_script(f"window.SLIDE={json.dumps(s, ensure_ascii=False)};")
            pg.goto(modelo)
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(400)
            if pg.evaluate("""() => [...document.querySelectorAll('.txt')].some(t => t.dataset.cortado)
                || (() => { const c = document.querySelector('.corpo'); return c && c.scrollHeight > c.clientHeight + 4; })()"""):
                cortes.append(i)
            nome = f"carrossel-{i}.png"
            pg.screenshot(path=os.path.join(saida, nome))
            arquivos.append(f"{pasta_rel}/{nome}")
            pg.close()
        nav.close()
    print(f"{len(arquivos)} slides gerados em {saida}")
    try:  # folha de prévia: render/previas/<id>.jpg
        from PIL import Image
        W, H, cols = 270, 360, 5
        folha = Image.new("RGB", (cols * (W + 6) + 6, ((len(arquivos) + cols - 1) // cols) * (H + 6) + 6), (40, 40, 40))
        for k, a in enumerate(arquivos):
            im = Image.open(os.path.join(RAIZ, "render", "_saida", a)).convert("RGB").resize((W, H))
            folha.paste(im, (6 + (k % cols) * (W + 6), 6 + (k // cols) * (H + 6)))
        os.makedirs(os.path.join(AQUI, "previas"), exist_ok=True)
        folha.save(os.path.join(AQUI, "previas", f"{p['id']}.jpg"), quality=82)
    except Exception as e:
        print(f"[aviso] sem prévia: {e}")

    rev = revisar(p, cortes=cortes, hashes=hashes, checagem_fotos=(prob_fotos, av_fotos))
    if str(p["id"]).startswith(("teste", "e-teste")):
        rev["decisao"] = "precisa"
        rev["avisos"].append("Pedido de teste: nunca agenda sozinho.")
    R.salvar_revisao(rev)
    print(f"Revisão: {rev['decisao']} · problemas={rev['problemas']} avisos={rev['avisos']}")
    if local:
        return 0
    for a in arquivos:
        R.subir(os.path.join(RAIZ, "render", "_saida", a), a)
    R.gravar_card(p, arquivos, etapa="agendado" if rev["decisao"] == "agendado" else "pronto")
    R.publicar_revisoes()
    print(f"card '{p['id']}' gravado no painel")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(renderizar(json.load(open(sys.argv[1], encoding="utf-8")), "--local" in sys.argv))
