"""Teste de ponta a ponta de um dia do ciclo: publica AGORA, em ordem, com 40 s entre as publicações.

Uso (robô "Teste do ciclo"): python ciclo/teste.py AAAA-MM-DD
Pré-requisito: render/render.py já subiu as artes de ciclos/teste/teste-ciclo-estatico.json e -carrossel.json.
Não mexe no fila.json, na rotação nem no painel. Resultado em ciclos/teste/resultado.json.
"""
import datetime as dt
import json
import os
import sys
import tempfile
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [RAIZ, os.path.join(RAIZ, "acervo"), os.path.join(RAIZ, "ciclo"), os.path.join(RAIZ, "render")]
import escolher  # noqa: E402
import publicar  # noqa: E402
import stories  # noqa: E402
from story import renderizar  # noqa: E402

PAUSA = 40


def main(data):
    T = os.path.join(RAIZ, "ciclos", "teste")
    est = json.load(open(os.path.join(T, "teste-ciclo-estatico.json"), encoding="utf-8"))
    car = json.load(open(os.path.join(T, "teste-ciclo-carrossel.json"), encoding="utf-8"))
    foto = json.load(open(os.path.join(T, "teste-ciclo-foto.json"), encoding="utf-8"))
    n_slides = len(car["slides"])
    est_arq = [f"{est['data']}/{est['id']}/estatico.png"]
    car_arq = [f"{car['data']}/{car['id']}/carrossel-{i}.png" for i in range(1, n_slides + 1)]

    # foto pessoal: a primeira do índice que não é HEIF, enquadrada e enviada ao bucket
    indice = json.load(open(os.path.join(RAIZ, "acervo", "indice.json"), encoding="utf-8"))
    arq_foto = next(f for f in indice["pastas"]["fotos"] if f.get("id") == foto.get("drive_id")) if foto.get("drive_id") \
        else escolher.escolher_fotos(1, data, {"fotos": []})[0]
    escolher.preparar_foto(arq_foto, os.path.join(tempfile.gettempdir(), "foto.jpg"), foto["arquivo"], False)

    # stories do dia, com os posts do teste como destino das pontes
    cfg = json.load(open(os.path.join(RAIZ, "acervo", "config.json"), encoding="utf-8"))
    fila_fake = [{"id": est["id"], "tipo": "IMAGEM", "quando": f"{data}T07:00:00-03:00", "arquivos": est_arq},
                 {"id": car["id"], "tipo": "CARROSSEL", "quando": f"{data}T12:00:00-03:00", "arquivos": car_arq}]
    plano = stories.planejar(data, cfg, indice, {"trechos": []}, fila_fake)
    tmp = tempfile.mkdtemp()
    arquivos_story = {}
    for s in plano:
        nome = s["id"].split("-st-")[1]
        tela = {k: s[k] for k in ("rotulo", "titulo", "texto", "imagem") if s.get(k)}
        if "trecho" in s:
            local, _ = stories.story_em_video(s, tela, tmp, nome)
            tipo, ext = "video/mp4", "mp4"
        else:
            local, tipo, ext = os.path.join(tmp, f"story-{nome}.png"), "image/png", "png"
            renderizar([{**tela, "arquivo": os.path.relpath(local, RAIZ), "topo": 1220, "imagem_topo": 360}])
        bucket = f"{data}/teste-ciclo/story-{nome}.{ext}"
        stories.subir(local, bucket, tipo)
        arquivos_story[nome] = bucket

    # ordem do dia
    seq = []
    if "0600" in arquivos_story:
        seq.append({"id": "teste-story-0600", "tipo": "STORY", "arquivos": [arquivos_story["0600"]]})
    seq.append({"id": est["id"], "tipo": "IMAGEM", "arquivos": est_arq, "legenda": est["legenda"]})
    if "0800" in arquivos_story:
        seq.append({"id": "teste-story-0800", "tipo": "STORY", "arquivos": [arquivos_story["0800"]]})
    if "1000" in arquivos_story:
        seq.append({"id": "teste-story-1000", "tipo": "STORY", "arquivos": [arquivos_story["1000"]]})
    seq.append({"id": car["id"], "tipo": "CARROSSEL", "arquivos": car_arq, "legenda": car["legenda"]})
    if "1230" in arquivos_story:
        seq.append({"id": "teste-story-1230", "tipo": "STORY", "arquivos": [arquivos_story["1230"]]})
    seq.append({"id": foto["id"], "tipo": "IMAGEM", "arquivos": [foto["arquivo"]], "legenda": foto["legenda"]})

    resultado = []
    for n, item in enumerate(seq):
        if n:
            time.sleep(PAUSA)
        r = {"id": item["id"], "tipo": item["tipo"], "arquivos": item["arquivos"]}
        try:
            mid = publicar.publicar(item)
            r.update(status="publicado", media_id=mid, link=publicar.buscar_link(mid) if mid else None)
        except Exception as e:  # segue para o próximo, registra o erro
            r.update(status="erro", erro=str(e)[:400])
        r["em"] = dt.datetime.now(publicar.BRT).isoformat(timespec="seconds")
        print(json.dumps(r, ensure_ascii=False))
        resultado.append(r)
    json.dump(resultado, open(os.path.join(T, "resultado.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 0 if all(r["status"] == "publicado" for r in resultado) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
