"""Robô de publicação do Instagram — Luan Tavares Treinador.

Lê a fila (fila.json), publica o que já passou do horário e marca o resultado.
Usa só a biblioteca padrão do Python.

Variáveis de ambiente (vêm dos segredos do GitHub):
  IG_TOKEN      token da API do Instagram (login do Instagram)
  IG_USER_ID    ID da conta do Instagram
  MIDIA_BASE    URL pública do bucket, ex.: https://xyz.supabase.co/storage/v1/object/public/midia
  IG_API_VER    opcional, versão da API (padrão v23.0)
  SIMULAR=1     opcional: não chama a API, só mostra o que faria
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

FILA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fila.json")
BRT = timezone(timedelta(hours=-3))
JANELA_ATRASO = timedelta(hours=12)  # passou disso, não publica mais e marca "atrasado"
TIPOS = {"IMAGEM", "CARROSSEL", "REELS", "STORY"}
EXT_VIDEO = (".mp4", ".mov")

SIMULAR = os.environ.get("SIMULAR") == "1"
TOKEN = os.environ.get("IG_TOKEN", "")
IG_ID = os.environ.get("IG_USER_ID", "")
BASE_MIDIA = os.environ.get("MIDIA_BASE", "").rstrip("/")
API = "https://graph.instagram.com/" + os.environ.get("IG_API_VER", "v23.0")


class ErroPublicacao(Exception):
    pass


def agora():
    return datetime.now(BRT)


def url_midia(caminho):
    if caminho.startswith("http"):
        return caminho
    return f"{BASE_MIDIA}/{urllib.parse.quote(caminho)}"


def e_video(caminho):
    return caminho.lower().endswith(EXT_VIDEO)


def chamar(metodo, caminho, params):
    if SIMULAR:
        print(f"    [simulação] {metodo} {caminho} {json.dumps({k: v for k, v in params.items()}, ensure_ascii=False)[:200]}")
        return {"id": "simulado", "status_code": "FINISHED"}
    params = dict(params, access_token=TOKEN)
    dados = urllib.parse.urlencode(params).encode()
    url = f"{API}/{caminho}"
    if metodo == "GET":
        req = urllib.request.Request(f"{url}?{dados.decode()}")
    else:
        req = urllib.request.Request(url, data=dados, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        corpo = e.read().decode(errors="replace")
        raise ErroPublicacao(f"API respondeu {e.code}: {corpo[:500]}") from None


def conferir_arquivo(caminho):
    if SIMULAR:
        return
    req = urllib.request.Request(url_midia(caminho), method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            if r.status != 200:
                raise ErroPublicacao(f"arquivo não encontrado: {caminho}")
    except urllib.error.HTTPError:
        raise ErroPublicacao(f"arquivo não encontrado no bucket: {caminho}") from None


def esperar_pronto(container_id, limite_seg=600):
    """Vídeos precisam ser processados pelo Instagram antes de publicar."""
    inicio = time.time()
    while True:
        st = chamar("GET", container_id, {"fields": "status_code,status"})
        code = st.get("status_code")
        if code == "FINISHED":
            return
        if code in ("ERROR", "EXPIRED"):
            raise ErroPublicacao(f"Instagram não processou a mídia: {st.get('status')}")
        if time.time() - inicio > limite_seg:
            raise ErroPublicacao("tempo esgotado esperando o Instagram processar o vídeo")
        time.sleep(10)


def criar_container(params):
    return chamar("POST", f"{IG_ID}/media", params)["id"]


def params_comuns(item):
    p = {}
    if item.get("legenda") and item["tipo"] != "STORY":
        p["caption"] = item["legenda"]
    if item.get("colaboradores") and item["tipo"] != "STORY":
        p["collaborators"] = json.dumps(item["colaboradores"])
    return p


def publicar(item):
    tipo = item["tipo"]
    arquivos = item["arquivos"]
    for a in arquivos + ([item["capa"]] if item.get("capa") else []):
        conferir_arquivo(a)

    if tipo == "IMAGEM":
        cid = criar_container({"image_url": url_midia(arquivos[0]), **params_comuns(item)})
    elif tipo == "REELS":
        p = {"media_type": "REELS", "video_url": url_midia(arquivos[0]),
             "share_to_feed": "true" if item.get("no_feed", True) else "false", **params_comuns(item)}
        if item.get("capa"):
            p["cover_url"] = url_midia(item["capa"])
        cid = criar_container(p)
        esperar_pronto(cid)
    elif tipo == "STORY":
        a = arquivos[0]
        chave = "video_url" if e_video(a) else "image_url"
        cid = criar_container({"media_type": "STORIES", chave: url_midia(a)})
        if e_video(a):
            esperar_pronto(cid)
    elif tipo == "CARROSSEL":
        if not 2 <= len(arquivos) <= 10:
            raise ErroPublicacao("carrossel precisa de 2 a 10 arquivos")
        filhos = []
        for a in arquivos:
            if e_video(a):
                f = criar_container({"media_type": "VIDEO", "video_url": url_midia(a), "is_carousel_item": "true"})
                esperar_pronto(f)
            else:
                f = criar_container({"image_url": url_midia(a), "is_carousel_item": "true"})
            filhos.append(f)
        cid = criar_container({"media_type": "CAROUSEL", "children": ",".join(filhos), **params_comuns(item)})
        esperar_pronto(cid)
    else:
        raise ErroPublicacao(f"tipo desconhecido: {tipo}")

    esperar_pronto(cid)
    for tentativa in range(6):
        try:
            return chamar("POST", f"{IG_ID}/media_publish", {"creation_id": cid}).get("id")
        except ErroPublicacao as e:
            if "9007" in str(e) and tentativa < 5:
                time.sleep(10)
                continue
            raise


def buscar_link(media_id):
    """Link público do post (permalink). Falha aqui nunca derruba a publicação."""
    if SIMULAR or not media_id:
        return None
    try:
        return chamar("GET", media_id, {"fields": "permalink"}).get("permalink")
    except ErroPublicacao:
        return None


def validar(item):
    for campo in ("id", "quando", "tipo", "arquivos"):
        if campo not in item:
            raise ErroPublicacao(f"item sem o campo '{campo}'")
    if item["tipo"] not in TIPOS:
        raise ErroPublicacao(f"tipo inválido: {item['tipo']} (use {', '.join(sorted(TIPOS))})")
    quando = datetime.fromisoformat(item["quando"])
    if quando.tzinfo is None:
        quando = quando.replace(tzinfo=BRT)
    return quando


def main():
    if not SIMULAR and not (TOKEN and IG_ID and BASE_MIDIA):
        print("Faltam segredos: IG_TOKEN, IG_USER_ID e MIDIA_BASE.")
        return 1
    with open(FILA, encoding="utf-8") as f:
        fila = json.load(f)

    t = agora()
    erros = 0
    mudou = False
    for item in fila:
        if item.get("status", "pendente") != "pendente":
            continue
        try:
            quando = validar(item)
        except (ErroPublicacao, ValueError) as e:
            item.update(status="erro", erro=str(e))
            erros += 1
            mudou = True
            print(f"[ERRO] {item.get('id')}: {e}")
            continue
        if quando > t:
            continue
        if t - quando > JANELA_ATRASO:
            item.update(status="atrasado", erro="passou mais de 12h do horário; republique ajustando 'quando'")
            mudou = True
            print(f"[ATRASADO] {item['id']}")
            continue
        print(f"Publicando {item['id']} ({item['tipo']}, marcado para {item['quando']})")
        try:
            media_id = publicar(item)
            item.update(status="publicado", media_id=media_id, publicado_em=agora().isoformat(timespec="minutes"))
            link = buscar_link(media_id)
            if link:
                item["permalink"] = link
            item.pop("erro", None)
            print(f"  OK, media_id={media_id}")
        except ErroPublicacao as e:
            item.update(status="erro", erro=str(e))
            erros += 1
            print(f"  [ERRO] {e}")
        mudou = True

    # completa o link de posts publicados antes desta função existir (até 10 por rodada)
    for item in [i for i in fila if i.get("status") == "publicado" and i.get("media_id") and not i.get("permalink")][:10]:
        link = buscar_link(item["media_id"])
        if link:
            item["permalink"] = link
            mudou = True

    if mudou and not SIMULAR:
        with open(FILA, "w", encoding="utf-8") as f:
            json.dump(fila, f, ensure_ascii=False, indent=2)
            f.write("\n")
    pendentes = sum(1 for i in fila if i.get("status", "pendente") == "pendente")
    print(f"Fim. Pendentes na fila: {pendentes}. Erros nesta rodada: {erros}.")
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
