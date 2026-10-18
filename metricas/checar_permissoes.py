"""Testa o que o token do Instagram consegue ler (perfil, mídia, insights, mensagens).
Grava metricas/permissoes.json (sem o token). Usado antes de ligar o coletor de métricas."""
import datetime as dt
import json
import os
import urllib.error
import urllib.parse
import urllib.request

TOKEN = os.environ["IG_TOKEN"]
API = "https://graph.instagram.com/v23.0"
SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "permissoes.json")


def chamar(caminho, **params):
    params["access_token"] = TOKEN
    url = f"{API}/{caminho}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return {"ok": True, "amostra": json.loads(r.read())}
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read()).get("error", {})
        except Exception:
            err = {}
        return {"ok": False, "http": e.code, "codigo": err.get("code"), "msg": (err.get("message") or "")[:300]}
    except Exception as e:
        return {"ok": False, "msg": str(e)[:300]}


res = {"testado_em": dt.datetime.now(dt.timezone(dt.timedelta(hours=-3))).isoformat(timespec="minutes")}
res["perfil"] = chamar("me", fields="user_id,username,followers_count,follows_count,media_count")
res["midias"] = chamar("me/media", fields="id,timestamp,media_type,media_product_type,permalink", limit=5)
ids = [m["id"] for m in (res["midias"].get("amostra") or {}).get("data", [])] if res["midias"]["ok"] else []
tipos = {m["id"]: m.get("media_product_type") for m in (res["midias"].get("amostra") or {}).get("data", [])} if ids else {}
if ids:
    feed = next((i for i in ids if tipos.get(i) == "FEED"), ids[0])
    res["insights_post"] = chamar(f"{feed}/insights", metric="reach,saved,shares,likes,comments,total_interactions,views")
    reel = next((i for i in ids if tipos.get(i) == "REELS"), None)
    if reel:
        res["insights_reels"] = chamar(f"{reel}/insights", metric="reach,saved,shares,views,ig_reels_avg_watch_time")
res["insights_conta"] = chamar("me/insights", metric="reach,profile_views,follows_and_unfollows,website_clicks",
                               period="day", metric_type="total_value")
res["conversas"] = chamar("me/conversations", platform="instagram", limit=1)
# não guardar conteúdo de mensagens nem dados de terceiros
if res["conversas"].get("ok"):
    res["conversas"]["amostra"] = {"quantidade_na_pagina": len(res["conversas"]["amostra"].get("data", []))}
with open(SAIDA, "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
for k, v in res.items():
    if isinstance(v, dict):
        print(k, "OK" if v.get("ok") else f"FALHOU {v.get('http')} {v.get('codigo')} {v.get('msg')}")
