"""Lista o acervo do Google Drive (pasta "TTC Acervo") e grava acervo/indice.json.

Usa a chave GDRIVE_API_KEY (Google Drive API, pasta pública por link). Só leitura.
Uso: python acervo/listar.py
"""
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

PASTA_RAIZ = "1rIv77LwguHTyfA4CX_KrAqgbx2iT7I8U"
SUBPASTAS = ["fotos", "timelapse-trabalho", "timelapse-treino"]
API = "https://www.googleapis.com/drive/v3/files"
CAMPOS = ("nextPageToken,files(id,name,mimeType,size,createdTime,modifiedTime,"
          "imageMediaMetadata(width,height,time),videoMediaMetadata(width,height,durationMillis))")
SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "indice.json")
BRT = dt.timezone(dt.timedelta(hours=-3))


def listar(pasta_id, chave):
    itens, token = [], None
    while True:
        params = {"q": f"'{pasta_id}' in parents and trashed=false", "fields": CAMPOS,
                  "pageSize": 1000, "key": chave}
        if token:
            params["pageToken"] = token
        try:
            with urllib.request.urlopen(f"{API}?{urllib.parse.urlencode(params)}", timeout=60) as r:
                d = json.loads(r.read())
        except urllib.error.HTTPError as e:
            sys.exit(f"Drive respondeu {e.code}: {e.read().decode(errors='replace')[:400]}")
        itens += d.get("files", [])
        token = d.get("nextPageToken")
        if not token:
            return itens


def main():
    chave = os.environ.get("GDRIVE_API_KEY")
    if not chave:
        sys.exit("Falta o segredo GDRIVE_API_KEY.")
    raiz = {f["name"]: f for f in listar(PASTA_RAIZ, chave)}
    indice = {"gerado_em": dt.datetime.now(BRT).isoformat(timespec="minutes"), "pastas": {}}
    for nome in SUBPASTAS:
        if nome not in raiz:
            print(f"aviso: subpasta {nome} não encontrada")
            indice["pastas"][nome] = []
            continue
        arquivos = [f for f in listar(raiz[nome]["id"], chave) if not f["mimeType"].endswith("folder")]
        arquivos.sort(key=lambda f: f["name"])
        indice["pastas"][nome] = arquivos
        print(f"{nome}: {len(arquivos)} arquivo(s)")
    with open(SAIDA, "w", encoding="utf-8") as f:
        json.dump(indice, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
