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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from revisar import revisar  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
UA = {"User-Agent": "Mozilla/5.0 (ttc-publicador render)"}


def dhash(caminho):
    """Impressão da imagem (64 bits, hex) para achar a mesma foto vinda de outro link."""
    from PIL import Image
    im = Image.open(caminho).convert("L").resize((9, 8))
    px = list(im.getdata())
    bits = "".join("1" if px[r * 9 + c] > px[r * 9 + c + 1] else "0" for r in range(8) for c in range(8))
    return f"{int(bits, 2):016x}"


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


def etapa_atual(cid):
    """Etapa que o card já tem no painel (None se ainda não existe)."""
    req = urllib.request.Request(f"{URL}/rest/v1/conteudos?id=eq.{urllib.parse.quote(cid)}&select=*",
                                 headers={"apikey": KEY})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            linhas = json.loads(r.read())
        return linhas[0] if linhas else None
    except Exception as e:
        print(f"::warning::não li a etapa atual de {cid}: {e}")
        return None


def aprovado_na_fila(cid):
    """Item do fila.json ainda por publicar (o Luan já aprovou): devolve o item, senão None."""
    try:
        for i in json.load(open(os.path.join(RAIZ, "fila.json"), encoding="utf-8")):
            if i.get("id") == cid and i.get("status", "pendente") in ("pendente", "erro", "atrasado"):
                return i
    except Exception as e:
        print(f"::warning::não li o fila.json: {e}")
    return None


def gravar_card(p, arquivos, capa=None, tipo="CARROSSEL", etapa="pronto"):
    atual = etapa_atual(p["id"]) or {}
    quando = p.get("quando")
    na_fila = aprovado_na_fila(p["id"])
    if atual.get("etapa") not in ("cancelado", "publicado", "agendado") and na_fila and etapa == "agendado":
        quando = na_fila.get("quando") or quando  # já aprovado: volta ao horário da fila
    if atual.get("etapa") in ("cancelado", "publicado"):
        etapa = atual["etapa"]  # nunca ressuscita o que foi cancelado nem mexe no que já saiu
        quando = atual.get("quando") or quando
    elif atual.get("etapa") == "agendado":
        quando = atual.get("quando") or quando  # o horário que já estava valendo (pode ter sido ajustado no painel)
        if etapa == "pronto":
            print(f"::warning::{p['id']} estava agendado e a nova versão não passou na revisão: volta para Precisa de você")
    linha = {
        "id": p["id"], "data": p.get("data"), "tipo": tipo, "pauta": p.get("pauta"),
        "funil": p.get("funil"), "etapa": etapa, "quando": quando,
        "arquivos": arquivos, "legenda": p.get("legenda"), "capa": capa, "link": None, "media_id": None,
    }
    if p.get("tema") and not atual.get("tema"):
        linha["tema"] = p["tema"]  # só preenche: o tema corrigido no painel vale mais
    req = urllib.request.Request(
        f"{URL}/rest/v1/conteudos?on_conflict=id", data=json.dumps([linha], ensure_ascii=False).encode(),
        method="POST", headers={"apikey": KEY, "Content-Type": "application/json",
                                "Prefer": "resolution=merge-duplicates,return=minimal"})
    urllib.request.urlopen(req, timeout=60).read()


def main():
    caminho = sys.argv[1]
    local = "--local" in sys.argv
    p = json.load(open(caminho, encoding="utf-8"))
    if p.get("formato") == "foto":
        return entregar_foto(p, local)
    slides = p.get("slides") or []
    pasta_rel = f"{p['data']}/{p['id']}"
    saida = os.path.join(RAIZ, "render", "_saida", pasta_rel)
    fotos = os.path.join(RAIZ, "render", "_fotos")
    os.makedirs(saida, exist_ok=True)
    os.makedirs(fotos, exist_ok=True)

    fotos_falharam, cortes = [], []
    reels = p.get("formato") == "reels"
    estatico = p.get("formato") == "estatico"
    meme = p.get("formato") == "meme"  # diretrizes/conteudo.md, seção 5
    if meme:
        slides = p["slides"] = [{"tipo": "meme", "frase": p.get("frase"), "foto": p.get("foto"), "foco": p.get("foco")}]
    if estatico:
        slides = p["slides"] = slides[:1]
    W, H = (1080, 1920) if reels else (1080, 1350)
    for s in slides:  # capa com pessoa conhecida e sem foto: o robô busca no Commons, com licença conferida
        if s.get("tipo") == "capa" and s.get("pessoa") and not s.get("foto"):
            try:
                from foto_commons import buscar
                achada = buscar(s["pessoa"])
            except Exception as e:
                achada = None
                print(f"::warning::busca no Commons falhou ({e}); capa sem foto")
            if achada:
                s.update(achada)
                print(f"Foto do Commons: {achada['pagina_origem']} ({achada['licenca']})")
            elif s.get("foto_reproducao"):  # reserva aceita pelo Luan em 02/11/2026: foto da notícia, com crédito
                s.update({"foto": s["foto_reproducao"], "licenca": "reproducao",
                          "credito": s.get("credito_reproducao") or "Foto: Reprodução",
                          "pagina_origem": s.get("origem_reproducao") or s.get("link_noticia")})
                print(f"Sem foto no Commons; usando reprodução de {s['pagina_origem']}")
            else:
                s["foto_nao_achada"] = True  # a revisão manda para "Precisa de você" (capa sem rosto)
                print(f"Sem foto liberada de {s['pessoa']} no Commons; capa só com texto")
    for i, s in enumerate(slides, 1):  # foto do repositório (quadro do vídeo) -> caminho absoluto
        if (s.get("foto") or "").startswith("render/"):
            s["foto"] = "file://" + os.path.join(RAIZ, s["foto"])
    for i, s in enumerate(slides, 1):  # foto remota -> arquivo local; se falhar, slide sem foto
        if (s.get("foto") or "").startswith("http"):
            s.setdefault("foto_url", s["foto"])
            destino = os.path.join(fotos, f"{p['id']}-{i}.jpg")
            try:
                baixar_foto(s["foto"], destino)
                s["foto"] = "file://" + destino
            except Exception as e:
                print(f"::warning::foto do slide {i} não baixou ({e}); segue sem foto")
                s["foto"] = None
                fotos_falharam.append(i)

    hashes = {}
    for i, s in enumerate(slides, 1):  # impressão de cada foto (revisão de foto repetida)
        f = s.get("foto") or ""
        if f.startswith("file://"):
            try:
                hashes[i] = dhash(f[7:])
            except Exception as e:
                print(f"[aviso] sem impressão da foto do slide {i}: {e}")

    arquivos = []
    modelo = "file://" + os.path.join(AQUI, "capa-reels.html" if reels else "meme.html" if meme else "carrossel.html")
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        pg = nav.new_page(viewport={"width": W, "height": H})
        for i, s in enumerate(slides, 1):
            pg.add_init_script(f"window.SLIDE={json.dumps(s, ensure_ascii=False)};window.TOTAL={len(slides)};window.INDICE={i};")
            pg.goto(modelo)
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(300)
            cortado = pg.evaluate("""() => {
              const c = document.querySelector('.corpo'), sec = document.querySelector('.s'), rod = document.querySelector('.rod');
              if (!c || !sec) return false;
              if (c.scrollHeight > c.clientHeight + 4 || sec.scrollHeight > sec.clientHeight + 4) return true;
              if (rod && rod.getBoundingClientRect().bottom > sec.getBoundingClientRect().bottom - 20) return true;
              return [...c.querySelectorAll('h1,p,.nota,.cta-box,.num')].some(e => e.scrollWidth > e.clientWidth + 4);
            }""")
            if cortado:
                cortes.append(i)
            nome = "reels-capa.png" if reels else "estatico.png" if estatico else "meme.png" if meme else f"carrossel-{i}.png"
            pg.screenshot(path=os.path.join(saida, nome))
            arquivos.append(f"{pasta_rel}/{nome}")
            pg.close()
            pg = nav.new_page(viewport={"width": W, "height": H})
            if reels or estatico or meme:
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

    # Card que já existe no painel: a revisão usa o horário que vale lá (pode ter sido ajustado com o lápis),
    # e um card que o Luan já aprovou (agendado) continua agendado se a nova versão não tiver problema técnico.
    atual = {} if local else (etapa_atual(p["id"]) or {})
    na_fila = aprovado_na_fila(p["id"])
    aprovado = atual.get("etapa") == "agendado" or na_fila is not None
    quando_valido = atual.get("quando") if atual.get("etapa") == "agendado" else (na_fila or {}).get("quando")
    p_rev = dict(p, quando=quando_valido or p.get("quando")) if aprovado else p
    rev = revisar(p_rev, cortes=cortes, fotos_falharam=fotos_falharam, hashes=hashes)
    if aprovado and not rev["problemas"] and rev["decisao"] != "agendado":
        rev["decisao"] = "agendado"
        rev["avisos"].append("Já aprovado no painel; a nova versão manteve a aprovação.")
    if str(p["id"]).startswith(("teste", "e-teste")):
        rev["decisao"] = "precisa"
        rev["avisos"].append("Pedido de teste: nunca agenda sozinho.")
    salvar_revisao(rev)
    print(f"Revisão: {rev['decisao']} · problemas={rev['problemas']} atenção={rev['atencao']} avisos={rev['avisos']}")
    if local:
        return 0
    for a in arquivos:
        subir(os.path.join(RAIZ, "render", "_saida", a), a)
    etapa = "agendado" if rev["decisao"] == "agendado" else "pronto"
    if reels:
        gravar_card(p, [p["video"]], capa=arquivos[0], tipo="REELS", etapa=etapa)
    elif estatico or meme:
        gravar_card(p, arquivos, tipo="IMAGEM", etapa=etapa)
    else:
        gravar_card(p, arquivos, etapa=etapa)
    publicar_revisoes()
    print(f"card '{p['id']}' gravado no painel como {etapa}")
    return 0


def entregar_foto(p, local):
    """Foto pessoal (ciclo temático): a imagem já está no bucket (robô Escolher tema do ciclo); só revisa a legenda."""
    rev = revisar(p)
    salvar_revisao(rev)
    print(f"Revisão: {rev['decisao']} · problemas={rev['problemas']} avisos={rev['avisos']}")
    if local:
        return 0
    gravar_card(p, [p["arquivo"]], tipo="IMAGEM", etapa="agendado" if rev["decisao"] == "agendado" else "pronto")
    publicar_revisoes()
    print(f"card '{p['id']}' gravado no painel")
    return 0


def salvar_revisao(rev):
    pasta = os.path.join(AQUI, "revisoes")
    os.makedirs(pasta, exist_ok=True)
    with open(os.path.join(pasta, f"{rev['id']}.json"), "w", encoding="utf-8") as f:
        json.dump(rev, f, ensure_ascii=False, indent=1)
        f.write("\n")


def publicar_revisoes():
    """Junta render/revisoes/*.json num índice e grava em materiais/revisao/indice.json (o painel lê)."""
    pasta = os.path.join(AQUI, "revisoes")
    indice = {}
    for nome in sorted(os.listdir(pasta)):
        if nome.endswith(".json"):
            with open(os.path.join(pasta, nome), encoding="utf-8") as f:
                r = json.load(f)
            indice[r["id"]] = r
    req = urllib.request.Request(
        f"{URL}/storage/v1/object/materiais/revisao/indice.json",
        data=json.dumps(indice, ensure_ascii=False).encode(), method="POST",
        headers={"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json",
                 "x-upsert": "true", "cache-control": "no-cache"})
    try:
        urllib.request.urlopen(req, timeout=60).read()
    except Exception as e:
        print(f"::warning::não publiquei o índice de revisões: {e}")


if __name__ == "__main__":
    sys.exit(main())
