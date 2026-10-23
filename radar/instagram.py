"""Radar — reels fora da curva dos perfis de referência (Instagram Business Discovery, roda no GitHub Actions).

Perfis lidos (sem repetir):
  1. radar/perfil-interesse.json -> instagram.perfis (o que a curadoria aprendeu e os parecidos que ela achou)
  2. referências do botão "Ensinar o radar" que são perfil do Instagram (radar/referencias.json)
  3. radar/perfis-instagram.json (perfis do nicho que a curadoria mantém)
  4. variável PERFIS (separados por vírgula), para testes pelo disparo manual

Para cada perfil: os últimos posts com curtidas e comentários. "Fora da curva" = reels dos últimos 30 dias cujo
engajamento (curtidas + comentários) é pelo menos 2x a mediana dos posts do próprio perfil. Assim o sinal é o
formato que funcionou para quem já tem público, e não o tamanho do perfil. Visualizações de terceiros não vêm na API.

Saída: radar/instagram.json (a curadoria do Claude lê; seção "Instagram" de radar/CURADORIA.md) e a mesma cópia em
materiais/radar/instagram.json, que o Radar mostra: à esquerda os 9 perfis em alta, à direita os posts em alta.
Perfil em alta = soma das razões dos posts fora da curva + taxa de engajamento (mediana / seguidores, em %).
Variáveis: FB_TOKEN (app "TTC Radar", login do Facebook) e IG_BUSINESS_ID (@tavarescoach).
FB_TOKEN pode ser o token da Página ou o token de usuário estendido (60 dias); com o de usuário, o robô pega o token da
Página a cada rodada (só em memória). Token vencido: o Radar mantém a última leitura (até 3 dias) e mostra o aviso no painel.
Só funciona com perfis profissionais (empresa ou criador); os pessoais voltam com erro e seguem listados.
"""
import datetime as dt
import hashlib
import json
import os
import re
import statistics
import sys
import urllib.error
import urllib.parse
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
API = "https://graph.facebook.com/v23.0"
TOKEN = os.environ.get("FB_TOKEN", "")
IG_ID = os.environ.get("IG_BUSINESS_ID", "")
AGORA = dt.datetime.now(dt.timezone.utc)
JANELA = dt.timedelta(days=30)
LIMITE_POSTS = 30
MAX_PERFIS = 40
RAZAO_MIN = 2.0
MIN_POSTS = 6  # menos que isso, a mediana não diz nada
CAMPOS_MIDIA = "caption,media_type,media_product_type,like_count,comments_count,timestamp,permalink,thumbnail_url,media_url"
SUPA = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPA_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
CTA = re.compile(r"\b(?i:comment|comente|comenta|digite|escreva)\s+[\"“']?[A-ZÀ-Ú]{3,}")


def usuario(txt):
    """'@fulano', 'fulano' ou 'https://instagram.com/fulano/' -> 'fulano' (None se não der)."""
    t = (txt or "").strip()
    m = re.match(r"^(?:https?://)?(?:www\.|m\.)?instagram\.com/([^/?#]+)", t, re.I)
    if m:
        t = m.group(1)
    t = t.lstrip("@").lower()
    if t in ("reel", "reels", "p", "tv", "explore", "stories") or not re.fullmatch(r"[a-z0-9._]{1,30}", t):
        return None
    return t


def perfis():
    vistos, out = set(), []

    def add(u, origem):
        u = usuario(u)
        if u and u not in vistos:
            vistos.add(u)
            out.append({"usuario": u, "origem": origem})

    for u in (os.environ.get("PERFIS") or "").split(","):
        add(u, "teste")
    try:
        for r in json.load(open(os.path.join(AQUI, "referencias.json"), encoding="utf-8")):
            if r.get("tipo") == "instagram_perfil" or (r.get("tipo") is None and re.search(r"instagram\.com/(?!reel|p/|tv)", r.get("url") or "")):
                add(r.get("url"), "referencia")
    except Exception:
        pass
    try:
        pf = json.load(open(os.path.join(AQUI, "perfil-interesse.json"), encoding="utf-8"))
        for u in (pf.get("instagram") or {}).get("perfis", []):
            add(u, "aprendido")
    except Exception:
        pass
    try:
        for u in json.load(open(os.path.join(AQUI, "perfis-instagram.json"), encoding="utf-8")).get("perfis", []):
            add(u, "nicho")
    except Exception:
        pass
    return out[:MAX_PERFIS]


def descobrir(u):
    campos = (f"business_discovery.username({u})"
              f"{{username,name,biography,profile_picture_url,followers_count,media_count,media.limit({LIMITE_POSTS}){{{CAMPOS_MIDIA}}}}}")
    url = f"{API}/{IG_ID}?" + urllib.parse.urlencode({"fields": campos, "access_token": TOKEN})
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.load(r)["business_discovery"], None
    except urllib.error.HTTPError as e:
        try:
            msg = json.load(e).get("error", {}).get("message", str(e))
        except Exception:
            msg = str(e)
        return None, msg[:200]
    except Exception as e:
        return None, str(e)[:200]


def quando(ts):
    return dt.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S%z") if ts else None


def api_get(caminho, **params):
    url = f"{API}/{caminho}?" + urllib.parse.urlencode({**params, "access_token": TOKEN})
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.load(r), None
    except urllib.error.HTTPError as e:
        try:
            return None, json.load(e).get("error", {}).get("message", str(e))[:200]
        except Exception:
            return None, str(e)[:200]
    except Exception as e:
        return None, str(e)[:200]


def preparar_token():
    """Token de usuário -> usa o token da Página do @tavarescoach nesta rodada. Devolve a mensagem de erro se o token
    não vale mais (vencido ou revogado), senão None."""
    global TOKEN
    contas, erro = api_get("me/accounts", fields="access_token,instagram_business_account", limit=50)
    if erro and ("access token" in erro.lower() or "session has expired" in erro.lower()):
        return erro
    for c in (contas or {}).get("data", []):
        if (c.get("instagram_business_account") or {}).get("id") == IG_ID and c.get("access_token"):
            TOKEN = c["access_token"]
            print("::add-mask::" + TOKEN)
            print("Token de usuário: usando o token da Página nesta rodada.")
            break
    return None


def tipo(m):
    if m.get("media_product_type") == "REELS" or m.get("media_type") == "VIDEO":
        return "reels"
    return "carrossel" if m.get("media_type") == "CAROUSEL_ALBUM" else "foto"


def publicar(dados):
    if not (SUPA and SUPA_KEY):
        return
    try:
        req = urllib.request.Request(f"{SUPA}/storage/v1/object/materiais/radar/instagram.json", method="POST",
            data=json.dumps(dados, ensure_ascii=False).encode(),
            headers={"apikey": SUPA_KEY, "Authorization": f"Bearer {SUPA_KEY}", "Content-Type": "application/json",
                     "x-upsert": "true", "cache-control": "no-cache"})
        urllib.request.urlopen(req, timeout=30).read()
        print("Instagram publicado no Radar.")
    except Exception as e:
        print(f"::warning::Não publiquei o Instagram no Radar: {e}")


def main():
    if not (TOKEN and IG_ID):
        print("Sem FB_TOKEN/IG_BUSINESS_ID: pulei o Instagram.")
        return 0
    erro_token = preparar_token()
    if erro_token:
        print(f"::warning::Token do Instagram (FB_TOKEN) inválido: {erro_token}")
    lista = perfis()
    print(f"Perfis acompanhados: {len(lista)}")
    # limite de chamadas da Meta: os perfis que não deu para ler agora ficam com a última leitura (até 3 dias)
    try:
        antes = json.load(open(os.path.join(AQUI, "instagram.json"), encoding="utf-8"))
    except Exception:
        antes = {}
    velho = dt.datetime.fromisoformat(antes["coletado_em"]) if antes.get("coletado_em") else None
    cache_ok = velho and AGORA - velho < dt.timedelta(days=3)
    perfis_antes = {x["usuario"].lower(): x for x in antes.get("perfis", []) if not x.get("erro")} if cache_ok else {}
    saida_perfis, posts = [], []
    limite = False
    for p in lista:
        if erro_token:
            d, erro = None, "token vencido (pulado)"
        else:
            d, erro = (None, "(#4) limite da Meta (pulado)") if limite else descobrir(p["usuario"])
        if erro and ("(#4)" in erro or "(#17)" in erro or "(#32)" in erro or "request limit" in erro.lower()
                     or "token" in erro.lower() or "session has expired" in erro.lower()):
            limite = True
            ant = perfis_antes.get(p["usuario"])
            if ant:
                saida_perfis.append({**ant, "origem": p["origem"], "da_leitura_anterior": True})
                posts += [x for x in antes.get("posts", []) if x.get("perfil", "").lower() == "@" + p["usuario"]]
                print(f"[aviso] @{p['usuario']}: limite da Meta, mantive a leitura anterior")
                continue
        if erro:
            print(f"[aviso] @{p['usuario']}: {erro}")
            saida_perfis.append({**p, "erro": erro})
            continue
        midias = (d.get("media") or {}).get("data", [])
        eng = [(m.get("like_count") or 0) + (m.get("comments_count") or 0) for m in midias]
        mediana = statistics.median(eng) if len(eng) >= MIN_POSTS else None
        seg = d.get("followers_count") or 0
        meus = []
        for m, e in zip(midias, eng):
            t = quando(m.get("timestamp"))
            if not t or AGORA - t > JANELA or not mediana:
                continue
            razao = round(e / mediana, 1)
            if razao < RAZAO_MIN:
                continue
            link = m.get("permalink") or ""
            tp = tipo(m)
            meus.append({
                "id": "ig-" + hashlib.sha1(link.split("?")[0].encode()).hexdigest()[:14],
                "perfil": "@" + d.get("username", p["usuario"]), "seguidores": seg, "tipo": tp,
                "link": link, "legenda": (m.get("caption") or "")[:600],
                "imagem": m.get("thumbnail_url") if tp == "reels" else (m.get("media_url") or m.get("thumbnail_url")),
                "publicado_em": t.isoformat(), "curtidas": m.get("like_count"), "comentarios": m.get("comments_count"),
                "mediana_perfil": mediana, "razao": razao,
                # "comente X que eu te mando" infla os comentários: a curadoria desconta
                "cta_comentario": bool(CTA.search(m.get("caption") or "")),
            })
        posts += meus
        taxa = round(100 * mediana / seg, 2) if mediana and seg else None
        pontos = round(sum(x["razao"] for x in meus) + min(taxa or 0, 10), 1)
        saida_perfis.append({**p, "usuario": d.get("username", p["usuario"]), "nome": d.get("name"),
                             "foto": d.get("profile_picture_url"), "bio": (d.get("biography") or "")[:200],
                             "seguidores": seg, "posts_lidos": len(midias), "mediana": mediana, "taxa_engajamento": taxa,
                             "fora_da_curva": len(meus), "maior_razao": max((x["razao"] for x in meus), default=None),
                             "pontos": pontos})
        print(f"@{p['usuario']}: {len(midias)} posts, mediana {mediana}, taxa {taxa}%, {len(meus)} fora da curva")
    posts.sort(key=lambda r: r["razao"], reverse=True)
    saida_perfis.sort(key=lambda x: (x.get("erro") is None, x.get("pontos") or 0), reverse=True)
    if erro_token and not any(not x.get("erro") for x in saida_perfis):
        print("Token vencido e sem leitura anterior: mantive o arquivo como estava.")
        return 1
    dados = {"coletado_em": AGORA.isoformat() if not erro_token else antes.get("coletado_em", AGORA.isoformat()),
             "aviso": ("O token do Instagram venceu: o Radar está mostrando a última leitura. Gere um token novo "
                       "(Explorador da Graph API, app TTC Radar, estendido) e salve no segredo FB_TOKEN.") if erro_token else None,
             "criterio": f"posts de até {JANELA.days} dias com engajamento >= {RAZAO_MIN}x a mediana do perfil",
             "perfis": saida_perfis, "posts": posts[:40]}
    with open(os.path.join(AQUI, "instagram.json"), "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=1)
    publicar(dados)
    print(f"{len(posts)} posts fora da curva.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
