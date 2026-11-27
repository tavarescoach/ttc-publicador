"""Etiqueta a qualidade das fotos do acervo para a linha Dor → Movimento (diretrizes/dor-movimento.md, seção 6.1).

Para cada foto de acervo/indice.json (pasta "fotos") que ainda não tem `nitidez` em acervo/tags.json, baixa o ORIGINAL
do Google Drive e grava em tags.json:
  rosto         "frente" (o detector achou rosto) ou "sem_rosto"
  largura_px    largura do original
  nitidez       variância do Laplaciano no maior rosto (render/foto_qualidade.py)
  dor_movimento "ok" ou "bloqueada" (sem rosto, menos de 1080 px de largura ou rosto sem nitidez)

O perfil ("perfil") e o de costas ("costas") podem ser corrigidos à mão; o robô não reescreve uma foto já etiquetada.
Uso: python acervo/qualidade.py [--max N] [--pasta-local DIR]   (precisa GDRIVE_API_KEY sem --pasta-local)
"""
import argparse
import json
import os
import sys
import tempfile
import urllib.parse
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(RAIZ, "render"))
from foto_qualidade import NITIDEZ_MIN, nitidez, rostos  # noqa: E402

INDICE = os.path.join(AQUI, "indice.json")
TAGS = os.path.join(AQUI, "tags.json")
LARGURA_MIN = 1080
LEGIVEIS = (".jpg", ".jpeg", ".png", ".webp")  # HEIC fica de fora até ser convertido


def avaliar_original(caminho):
    import cv2
    img = cv2.imread(caminho)
    if img is None:
        return None
    h, w = img.shape[:2]
    achados = rostos(img)
    n = round(nitidez(img, achados[0]), 1) if achados else 0.0
    ok = bool(achados) and w >= LARGURA_MIN and n >= NITIDEZ_MIN
    return {"rosto": "frente" if achados else "sem_rosto", "largura_px": w, "nitidez": n,
            "dor_movimento": "ok" if ok else "bloqueada"}


def baixar(fid, destino, chave):
    url = f"https://www.googleapis.com/drive/v3/files/{urllib.parse.quote(fid)}?alt=media&key={urllib.parse.quote(chave)}"
    with urllib.request.urlopen(url, timeout=120) as r, open(destino, "wb") as f:
        f.write(r.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=60, help="fotos por execução (o resto fica para a próxima)")
    ap.add_argument("--pasta-local", help="pasta com os arquivos já baixados, com o nome igual ao do Drive")
    a = ap.parse_args()
    chave = os.environ.get("GDRIVE_API_KEY")
    if not a.pasta_local and not chave:
        sys.exit("Falta o segredo GDRIVE_API_KEY.")
    indice = json.load(open(INDICE, encoding="utf-8"))
    tags = json.load(open(TAGS, encoding="utf-8"))
    pendentes = [f for f in indice["pastas"].get("fotos", [])
                 if f["name"].lower().endswith(LEGIVEIS)
                 and not (isinstance(tags.get(f["id"]), dict) and "nitidez" in tags[f["id"]])]
    print(f"{len(pendentes)} fotos sem etiqueta de qualidade; esta execução avalia até {a.max}.")
    feitas = 0
    with tempfile.TemporaryDirectory() as tmp:
        for f in pendentes[:a.max]:
            if a.pasta_local:
                caminho = os.path.join(a.pasta_local, f["name"])
                if not os.path.exists(caminho):
                    continue
            else:
                caminho = os.path.join(tmp, f["id"] + os.path.splitext(f["name"])[1])
                try:
                    baixar(f["id"], caminho, chave)
                except Exception as e:
                    print(f"::warning::{f['name']} não baixou: {e}")
                    continue
            r = avaliar_original(caminho)
            if not r:
                print(f"::warning::{f['name']} não abriu")
                continue
            atual = tags.get(f["id"]) if isinstance(tags.get(f["id"]), dict) else {}
            if atual.get("rosto") in ("perfil", "costas"):  # correção manual vale mais que o detector
                r["rosto"] = atual["rosto"]
                if r["rosto"] == "costas":
                    r["dor_movimento"] = "bloqueada"
            tags[f["id"]] = {**atual, **r}
            feitas += 1
            print(f"{f['name']}: {r}")
            if not a.pasta_local:
                os.remove(caminho)
    with open(TAGS, "w", encoding="utf-8") as fh:
        json.dump(tags, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print(f"{feitas} fotos etiquetadas.")


if __name__ == "__main__":
    main()
