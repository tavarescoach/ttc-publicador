"""Coletor de métricas do Instagram (@tavarescoach) para o painel.

Lê a API do Instagram (mesmo token do robô de publicação) e grava:
- metricas/painel.json   resumo para o painel (também enviado a materiais/metricas/painel.json)
- metricas/historico.json um retrato por dia (seguidores, alcance), para séries e comparações

Guarda só números. Do direct, conta mensagens com MÉTODO (por dia e quantas pessoas),
sem guardar texto nem identificação de ninguém.

Variáveis: IG_TOKEN, SUPABASE_URL, SUPABASE_SERVICE_KEY (opcional: sem ela só grava no repositório)
"""
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

PASTA = os.path.dirname(os.path.abspath(__file__))
BRT = dt.timezone(dt.timedelta(hours=-3))
API = "https://graph.instagram.com/v23.0"
TOKEN = os.environ.get("IG_TOKEN", "")
AGORA = dt.datetime.now(BRT)
METODO = re.compile(r"\bm[ée]todo\b", re.I)
avisos = []


def api(caminho, **params):
    params["access_token"] = TOKEN
    url = f"{API}/{caminho}?{urllib.parse.urlencode(params)}"
    for tentativa in range(2):
        try:
            with urllib.request.urlopen(url, timeout=40) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            try:
                msg = json.loads(e.read()).get("error", {}).get("message", "")
            except Exception:
                msg = ""
            if e.code >= 500 and tentativa == 0:
                time.sleep(3)
                continue
            raise RuntimeError(f"HTTP {e.code} em {caminho}: {msg[:200]}")
    return {}


def ts(d):
    return int(d.timestamp())


def total(metric, desde, ate, **extra):
    """Valor total de uma métrica da conta entre duas datas (máx. 30 dias)."""
    try:
        d = api("me/insights", metric=metric, period="day", metric_type="total_value",
                since=ts(desde), until=ts(ate), **extra)
        item = (d.get("data") or [{}])[0]
        tv = item.get("total_value") or {}
        if extra.get("breakdown"):
            res = {}
            for b in tv.get("breakdowns") or []:
                for r in b.get("results") or []:
                    res[(r.get("dimension_values") or ["?"])[0]] = r.get("value", 0)
            return res
        return tv.get("value")
    except Exception as e:
        avisos.append(f"{metric}: {e}")
        return None


def conta():
    p = api("me", fields="user_id,username,followers_count,follows_count,media_count")
    janelas = {"24h": 1, "7d": 7, "30d": 30}
    out = {"username": p.get("username"), "seguidores": p.get("followers_count"),
           "seguindo": p.get("follows_count"), "posts": p.get("media_count"), "_uid": p.get("user_id")}
    for nome, dias in janelas.items():
        desde = AGORA - dt.timedelta(days=dias)
        fu = total("follows_and_unfollows", desde, AGORA, breakdown="follow_type") or {}
        ganhou, perdeu = fu.get("FOLLOWER"), fu.get("NON_FOLLOWER")
        out[f"ganhos_{nome}"] = ganhou
        out[f"perdidos_{nome}"] = perdeu
        out[f"saldo_{nome}"] = (ganhou or 0) - (perdeu or 0) if ganhou is not None or perdeu is not None else None
    for nome, dias in (("7d", 7), ("30d", 30)):
        desde = AGORA - dt.timedelta(days=dias)
        for m in ("reach", "views", "profile_views", "accounts_engaged", "total_interactions", "website_clicks"):
            out[f"{m}_{nome}"] = total(m, desde, AGORA)
    # semana anterior, para comparar alcance e interações
    ini, fim = AGORA - dt.timedelta(days=14), AGORA - dt.timedelta(days=7)
    out["reach_7d_anterior"] = total("reach", ini, fim)
    out["total_interactions_7d_anterior"] = total("total_interactions", ini, fim)
    out["profile_views_7d_anterior"] = total("profile_views", ini, fim)
    return out


def serie_seguidores(seg_atual):
    """Seguidores por dia nos últimos 30 dias, reconstruídos a partir do saldo diário."""
    hoje = AGORA.replace(hour=0, minute=0, second=0, microsecond=0)
    saldos = []
    for k in range(30):  # do dia mais recente para trás
        fim = AGORA if k == 0 else hoje - dt.timedelta(days=k - 1)
        ini = hoje - dt.timedelta(days=k)
        fu = total("follows_and_unfollows", ini, fim, breakdown="follow_type")
        if fu is None:
            break
        saldos.append((ini.date().isoformat(), (fu.get("FOLLOWER") or 0) - (fu.get("NON_FOLLOWER") or 0)))
    serie, valor = [], seg_atual
    for dia, saldo in saldos:  # valor no fim de cada dia
        serie.append({"dia": dia, "seguidores": valor, "saldo": saldo})
        valor -= saldo
    return list(reversed(serie))


def posts():
    lista = api("me/media", fields="id,caption,media_type,media_product_type,timestamp,permalink,thumbnail_url,media_url,like_count,comments_count", limit=40).get("data", [])
    out = []
    limite = AGORA - dt.timedelta(days=45)
    for m in lista:
        quando = dt.datetime.fromisoformat(m["timestamp"].replace("+0000", "+00:00"))
        if quando < limite and len(out) >= 12:
            break
        reels = m.get("media_product_type") == "REELS"
        metr = "reach,saved,shares,total_interactions,views" + (",ig_reels_avg_watch_time" if reels else "")
        ins = {}
        try:
            for item in api(f"{m['id']}/insights", metric=metr).get("data", []):
                ins[item["name"]] = (item.get("values") or [{}])[0].get("value")
        except Exception as e:
            avisos.append(f"insights {m['id']}: {e}")
        legenda = (m.get("caption") or "").strip()
        titulo = next((l.strip() for l in legenda.splitlines() if l.strip()), "")[:110]
        likes, coment = m.get("like_count") or 0, m.get("comments_count") or 0
        salv, comp, alc = ins.get("saved") or 0, ins.get("shares") or 0, ins.get("reach") or 0
        valor = salv * 3 + comp * 3 + coment * 2 + likes
        out.append({
            "id": m["id"], "quando": quando.astimezone(BRT).isoformat(timespec="minutes"),
            "tipo": "REELS" if reels else {"CAROUSEL_ALBUM": "CARROSSEL", "IMAGE": "IMAGEM", "VIDEO": "REELS"}.get(m.get("media_type"), m.get("media_type")),
            "titulo": titulo, "link": m.get("permalink"),
            "capa": m.get("thumbnail_url") or (m.get("media_url") if m.get("media_type") != "VIDEO" else None),
            "alcance": alc, "views": ins.get("views"), "curtidas": likes, "comentarios": coment,
            "salvos": salv, "compart": comp, "interacoes": ins.get("total_interactions"),
            "tempo_medio_s": round(ins["ig_reels_avg_watch_time"] / 1000, 1) if ins.get("ig_reels_avg_watch_time") else None,
            "valor": valor, "taxa": round(100 * valor / alc, 1) if alc else None,
            "parcial": (AGORA - quando) < dt.timedelta(hours=48),
        })
    return out


def metodo(uid):
    """Conta mensagens com MÉTODO no direct, por dia (últimos 30 dias). Só números."""
    por_dia, pessoas = {}, set()
    desde = AGORA - dt.timedelta(days=30)
    try:
        conv = api("me/conversations", platform="instagram", fields="id,updated_time", limit=50).get("data", [])
    except Exception as e:
        avisos.append(f"direct: {e}")
        return None
    for c in conv:
        try:
            if dt.datetime.fromisoformat(c["updated_time"].replace("+0000", "+00:00")) < desde:
                continue
            msgs = api(c["id"], fields="messages.limit(25){message,from,created_time}").get("messages", {}).get("data", [])
        except Exception as e:
            avisos.append(f"conversa: {e}")
            continue
        for m in msgs:
            de = (m.get("from") or {}).get("id")
            if not de or de == uid:
                continue
            quando = dt.datetime.fromisoformat(m["created_time"].replace("+0000", "+00:00")).astimezone(BRT)
            if quando < desde or not METODO.search(m.get("message") or ""):
                continue
            dia = quando.date().isoformat()
            chave = hashlib.sha256(f"{de}{dia}".encode()).hexdigest()[:12]
            por_dia.setdefault(dia, set()).add(chave)
            pessoas.add(hashlib.sha256(de.encode()).hexdigest()[:12])
    dias = {d: len(s) for d, s in sorted(por_dia.items())}
    lim7 = (AGORA - dt.timedelta(days=7)).date().isoformat()
    return {"por_dia": dias, "pessoas_30d": len(pessoas), "total_30d": sum(dias.values()),
            "total_7d": sum(v for d, v in dias.items() if d >= lim7)}


def enviar(painel):
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not (url and key):
        return
    req = urllib.request.Request(
        f"{url}/storage/v1/object/materiais/metricas/painel.json",
        data=json.dumps(painel, ensure_ascii=False).encode(), method="POST",
        headers={"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json",
                 "x-upsert": "true", "cache-control": "no-cache"})
    with urllib.request.urlopen(req, timeout=40) as r:
        print(f"Painel atualizado (HTTP {r.status}).")


def main():
    if not TOKEN:
        print("Falta IG_TOKEN.")
        return 1
    c = conta()
    uid = c.pop("_uid", None)
    serie = serie_seguidores(c["seguidores"]) if c.get("seguidores") is not None else []
    ps = posts()
    met = metodo(uid)
    recentes = [p for p in ps if p["quando"] >= (AGORA - dt.timedelta(days=30)).isoformat()]
    painel = {
        "gerado_em": AGORA.isoformat(timespec="minutes"),
        "conta": c,
        "serie_seguidores": serie,
        "posts": ps,
        "top": {
            "valor": [p["id"] for p in sorted(recentes, key=lambda p: -p["valor"])[:6]],
            "alcance": [p["id"] for p in sorted(recentes, key=lambda p: -(p["alcance"] or 0))[:6]],
            "salvos": [p["id"] for p in sorted(recentes, key=lambda p: -p["salvos"])[:6]],
            "compart": [p["id"] for p in sorted(recentes, key=lambda p: -p["compart"])[:6]],
        },
        "metodo": met,
        "avisos": avisos[:20],
    }
    with open(os.path.join(PASTA, "painel.json"), "w", encoding="utf-8") as f:
        json.dump(painel, f, ensure_ascii=False, indent=1)
    # histórico: um retrato por dia (o último do dia vale)
    hist_path = os.path.join(PASTA, "historico.json")
    try:
        with open(hist_path, encoding="utf-8") as f:
            hist = json.load(f)
    except Exception:
        hist = []
    hoje = AGORA.date().isoformat()
    hist = [h for h in hist if h.get("dia") != hoje] + [{
        "dia": hoje, "seguidores": c.get("seguidores"), "reach_7d": c.get("reach_7d"),
        "profile_views_7d": c.get("profile_views_7d"), "metodo_7d": (met or {}).get("total_7d")}]
    with open(hist_path, "w", encoding="utf-8") as f:
        json.dump(hist[-400:], f, ensure_ascii=False, indent=1)
    try:
        enviar(painel)
    except Exception as e:
        print(f"::warning::não enviei ao painel: {e}")
    print(f"Seguidores {c.get('seguidores')} · saldo 7d {c.get('saldo_7d')} · alcance 7d {c.get('reach_7d')} · "
          f"{len(ps)} posts · MÉTODO 7d {(met or {}).get('total_7d')} · {len(avisos)} aviso(s)")
    for a in avisos[:10]:
        print("aviso:", a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
