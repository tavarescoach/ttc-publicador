"""Coleta ampla para a auditoria do Instagram (@tavarescoach).

Diferente de metricas/coletar.py (painel, 40 posts), esta coleta é para análise:
- todos os posts dos últimos DIAS (padrão 60), com legenda inteira e insights completos
  (alcance, views, curtidas, comentários, salvos, compartilhamentos, seguidores ganhos,
  visitas ao perfil, tempo médio assistido dos reels)
- alcance, views, visitas ao perfil, interações e saldo de seguidores dia a dia
- público: cidade, país, idade e gênero dos seguidores e do público engajado

Grava auditoria/dados/AAAA-MM-DD.json e auditoria/dados/ultimo.json. Só números e textos
públicos dos próprios posts; nada do direct.

Variáveis: IG_TOKEN. Opcional: DIAS (padrão 60).
"""
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

PASTA = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(PASTA, "dados")
BRT = dt.timezone(dt.timedelta(hours=-3))
API = "https://graph.instagram.com/v23.0"
TOKEN = os.environ.get("IG_TOKEN", "")
DIAS = int(os.environ.get("DIAS", "60") or 60)
AGORA = dt.datetime.now(BRT)
avisos = []


def api(caminho, **params):
    params["access_token"] = TOKEN
    url = caminho if caminho.startswith("http") else f"{API}/{caminho}?{urllib.parse.urlencode(params)}"
    for tentativa in range(3):
        try:
            with urllib.request.urlopen(url, timeout=40) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            try:
                msg = json.loads(e.read()).get("error", {}).get("message", "")
            except Exception:
                msg = ""
            if e.code >= 500 and tentativa < 2:
                time.sleep(3)
                continue
            raise RuntimeError(f"HTTP {e.code}: {msg[:200]}")
        except urllib.error.URLError:
            if tentativa < 2:
                time.sleep(3)
                continue
            raise
    return {}


def ts(d):
    return int(d.timestamp())


def insights_post(mid, reels):
    """Pede o conjunto completo; se a API recusar alguma métrica, cai para o básico."""
    base = ["reach", "views", "saved", "shares", "total_interactions", "likes", "comments"]
    extra = ["ig_reels_avg_watch_time", "ig_reels_video_view_total_time"] if reels else ["follows", "profile_visits", "profile_activity"]
    for conjunto in (base + extra, base + extra[:1], base):
        try:
            d = api(f"{mid}/insights", metric=",".join(conjunto))
            out = {}
            for item in d.get("data", []):
                v = (item.get("values") or [{}])[0].get("value")
                if v is None:
                    v = (item.get("total_value") or {}).get("value")
                out[item["name"]] = v
            return out
        except Exception as e:
            ultimo = str(e)
    avisos.append(f"insights {mid}: {ultimo}")
    return {}


def posts():
    limite = AGORA - dt.timedelta(days=DIAS)
    campos = "id,caption,media_type,media_product_type,timestamp,permalink,thumbnail_url,media_url,like_count,comments_count,children{media_type}"
    d = api("me/media", fields=campos, limit=50)
    out = []
    while True:
        for m in d.get("data", []):
            quando = dt.datetime.fromisoformat(m["timestamp"].replace("+0000", "+00:00")).astimezone(BRT)
            if quando < limite:
                return out
            reels = m.get("media_product_type") == "REELS"
            ins = insights_post(m["id"], reels)
            tipo = "REELS" if reels else {"CAROUSEL_ALBUM": "CARROSSEL", "IMAGE": "IMAGEM", "VIDEO": "VIDEO"}.get(m.get("media_type"), m.get("media_type"))
            out.append({
                "id": m["id"], "quando": quando.isoformat(timespec="minutes"), "tipo": tipo,
                "produto": m.get("media_product_type"),
                "n_slides": len((m.get("children") or {}).get("data", [])) or None,
                "legenda": m.get("caption") or "", "link": m.get("permalink"),
                "capa": m.get("thumbnail_url") or (m.get("media_url") if m.get("media_type") != "VIDEO" else None),
                "curtidas": m.get("like_count") or ins.get("likes") or 0,
                "comentarios": m.get("comments_count") or ins.get("comments") or 0,
                "alcance": ins.get("reach"), "views": ins.get("views"),
                "salvos": ins.get("saved"), "compart": ins.get("shares"),
                "interacoes": ins.get("total_interactions"),
                "seguiu": ins.get("follows"), "visitas_perfil": ins.get("profile_visits"),
                "atividade_perfil": ins.get("profile_activity"),
                "tempo_medio_s": round(ins["ig_reels_avg_watch_time"] / 1000, 1) if ins.get("ig_reels_avg_watch_time") else None,
            })
        nxt = (d.get("paging") or {}).get("next")
        if not nxt:
            return out
        d = api(nxt)


def total(metric, desde, ate, **extra):
    try:
        d = api("me/insights", metric=metric, period="day", metric_type="total_value",
                since=ts(desde), until=ts(ate), **extra)
        tv = ((d.get("data") or [{}])[0].get("total_value")) or {}
        if extra.get("breakdown"):
            res = {}
            for b in tv.get("breakdowns") or []:
                for r in b.get("results") or []:
                    res[(r.get("dimension_values") or ["?"])[0]] = r.get("value", 0)
            return res
        return tv.get("value")
    except Exception as e:
        avisos.append(f"{metric} {desde.date()}: {e}")
        return None


def diario():
    hoje = AGORA.replace(hour=0, minute=0, second=0, microsecond=0)
    out = []
    for k in range(min(DIAS, 60), -1, -1):
        ini = hoje - dt.timedelta(days=k)
        fim = min(ini + dt.timedelta(days=1), AGORA)
        dia = {"dia": ini.date().isoformat()}
        for m in ("reach", "views", "profile_views", "total_interactions", "accounts_engaged", "website_clicks"):
            dia[m] = total(m, ini, fim)
        fu = total("follows_and_unfollows", ini, fim, breakdown="follow_type") or {}
        dia["ganhos"], dia["perdidos"] = fu.get("FOLLOWER"), fu.get("NON_FOLLOWER")
        out.append(dia)
    return out


def publico():
    out = {}
    for metrica in ("follower_demographics", "engaged_audience_demographics"):
        out[metrica] = {}
        for quebra in ("city", "country", "age", "gender"):
            res = None
            for extra in ({"timeframe": "this_month"}, {"timeframe": "last_30_days"}, {}):
                try:
                    d = api("me/insights", metric=metrica, period="lifetime", metric_type="total_value",
                            breakdown=quebra, **extra)
                    tv = ((d.get("data") or [{}])[0].get("total_value")) or {}
                    res = {}
                    for b in tv.get("breakdowns") or []:
                        for r in b.get("results") or []:
                            res[(r.get("dimension_values") or ["?"])[0]] = r.get("value", 0)
                    break
                except Exception as e:
                    ultimo = str(e)
            if res is None:
                avisos.append(f"{metrica}/{quebra}: {ultimo}")
            out[metrica][quebra] = res
    return out


def main():
    if not TOKEN:
        sys.exit("IG_TOKEN ausente")
    p = api("me", fields="username,followers_count,follows_count,media_count")
    dados = {
        "gerado_em": AGORA.isoformat(timespec="minutes"), "dias": DIAS,
        "conta": {"username": p.get("username"), "seguidores": p.get("followers_count"),
                  "seguindo": p.get("follows_count"), "posts": p.get("media_count")},
        "posts": posts(), "diario": diario(), "publico": publico(), "avisos": avisos,
    }
    os.makedirs(SAIDA, exist_ok=True)
    for nome in (AGORA.date().isoformat() + ".json", "ultimo.json"):
        with open(os.path.join(SAIDA, nome), "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=1)
    print(f"{len(dados['posts'])} posts, {len(dados['diario'])} dias, {len(avisos)} avisos")
    for a in avisos[:15]:
        print("aviso:", a)


if __name__ == "__main__":
    main()
