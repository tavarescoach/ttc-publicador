"""Saúde do sistema: gera um resumo para a faixa do topo do painel.

Confere:
- pacote da semana (plano + carrosséis no repositório);
- última execução de cada robô no GitHub (falhou ou não);
- token do Instagram (faz uma chamada simples à API para ver se ainda vale);
- fila: posts com erro ou atrasados, último post publicado e o próximo agendado.

Grava em materiais/saude/status.json (bucket privado do Supabase); o painel lê de lá.
Roda dentro do robô "Sincronizar painel". Nunca derruba o robô: qualquer falha vira aviso.

Variáveis: SUPABASE_URL, SUPABASE_SERVICE_KEY, GITHUB_TOKEN, GITHUB_REPOSITORY, IG_TOKEN
"""
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request

PASTA = os.path.dirname(os.path.abspath(__file__))
BRT = dt.timezone(dt.timedelta(hours=-3))
AGORA = dt.datetime.now(BRT)

ROBOS = {
    "publicar.yml": "Publicar no Instagram",
    "renderizar-artes.yml": "Renderizar artes",
    "sincronizar-painel.yml": "Sincronizar painel",
    "pacote-pdf.yml": "Plano em PDF",
    "radar.yml": "Radar de notícias",
    "preparar-reels.yml": "Preparar reels",
    "subir-midia.yml": "Subir mídia",
    "renovar-token.yml": "Renovar token",
}


def http_json(url, headers=None, timeout=30):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read() or b"null")


def segunda_alvo():
    """Sábado e domingo olham a semana que vem; os outros dias, a semana atual."""
    hoje = AGORA.date()
    if hoje.weekday() >= 5:
        return hoje + dt.timedelta(days=7 - hoje.weekday())
    return hoje - dt.timedelta(days=hoje.weekday())


def checar_pacote():
    seg = segunda_alvo()
    plano = os.path.exists(os.path.join(PASTA, "pacotes", f"pacote-{seg.isoformat()}.md"))
    datas = {(seg + dt.timedelta(days=i)).isoformat() for i in range(7)}
    pedidos = os.path.join(PASTA, "render", "pedidos")
    carrosseis = sorted(
        n for n in (os.listdir(pedidos) if os.path.isdir(pedidos) else [])
        if n.startswith("s-") and n[2:12] in datas
    )
    tarefas = []
    try:
        with open(os.path.join(PASTA, "tarefas.json"), encoding="utf-8") as f:
            tarefas = [t for t in json.load(f) if t.get("data") in datas]
    except Exception:
        pass
    ok = plano and carrosseis and tarefas
    if ok:
        msg = f"Semana de {seg:%d/%m}: plano, {len(carrosseis)} carrosséis e lista do dia entregues."
    else:
        falta = [n for n, tem in (("plano", plano), ("carrosséis", carrosseis), ("lista do dia", tarefas)) if not tem]
        msg = f"Semana de {seg:%d/%m}: falta {', '.join(falta)}."
    return {"ok": bool(ok), "semana": seg.isoformat(), "plano": plano,
            "carrosseis": len(carrosseis), "tarefas": len(tarefas), "msg": msg}


def checar_robos():
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY", "tavarescoach/ttc-publicador")
    if not token:
        return {"ok": None, "msg": "Sem acesso ao GitHub nesta execução.", "itens": []}
    h = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    itens = []
    for arq, nome in ROBOS.items():
        try:
            d = http_json(f"https://api.github.com/repos/{repo}/actions/workflows/{arq}/runs?per_page=5&status=completed", h)
        except Exception as e:
            itens.append({"robo": nome, "ok": None, "msg": f"não consegui ler ({e.__class__.__name__})"})
            continue
        runs = [r for r in d.get("workflow_runs", []) if r.get("conclusion") not in ("cancelled", "skipped")]
        if not runs:
            itens.append({"robo": nome, "ok": None, "msg": "sem execuções"})
            continue
        r = runs[0]
        ok = r.get("conclusion") == "success"
        itens.append({"robo": nome, "ok": ok, "quando": r.get("updated_at"),
                      "titulo": (r.get("display_title") or "")[:90], "link": r.get("html_url")})
    falhas = [i for i in itens if i["ok"] is False]
    msg = "Todos os robôs ok." if not falhas else "Falhou: " + ", ".join(i["robo"] for i in falhas) + "."
    return {"ok": not falhas, "msg": msg, "itens": itens}


def checar_token():
    tok = os.environ.get("IG_TOKEN")
    if not tok:
        return {"ok": None, "msg": "Token não disponível nesta execução."}
    try:
        d = http_json(f"https://graph.instagram.com/me?fields=username&access_token={tok}")
        return {"ok": True, "msg": f"Token válido (@{d.get('username', '?')}). Renova sozinho nos dias 1 e 15."}
    except urllib.error.HTTPError as e:
        return {"ok": False, "msg": f"Token recusado pela Meta (HTTP {e.code}). Precisa gerar um novo."}
    except Exception as e:
        return {"ok": None, "msg": f"Não consegui testar o token ({e.__class__.__name__})."}


def checar_fila():
    try:
        with open(os.path.join(PASTA, "fila.json"), encoding="utf-8") as f:
            fila = json.load(f)
    except Exception:
        return {"ok": None, "msg": "fila.json ilegível."}
    problemas = [i for i in fila if i.get("status") in ("erro", "atrasado")]
    publicados = sorted((i for i in fila if i.get("status") == "publicado"), key=lambda i: i.get("quando") or "")
    agora_iso = AGORA.isoformat()
    proximos = sorted((i for i in fila if i.get("status") in (None, "pendente") and (i.get("quando") or "") >= agora_iso[:16]),
                      key=lambda i: i.get("quando") or "")
    def nome(i):
        if i.get("pauta"):
            return i["pauta"][:80]
        linha = next((l.strip() for l in (i.get("legenda") or "").splitlines() if l.strip()), "")
        return (linha[:77] + "…") if len(linha) > 80 else (linha or i["id"])
    resumo = lambda i: i and {"id": i["id"], "tipo": i.get("tipo"), "quando": i.get("quando"),
                              "link": i.get("permalink"), "pauta": nome(i)}
    msg = "Nenhum post com erro." if not problemas else f"{len(problemas)} post(s) com erro ou atrasado."
    return {"ok": not problemas, "msg": msg,
            "problemas": [dict(resumo(i), status=i.get("status"), erro=(i.get("erro") or "")[:200]) for i in problemas],
            "ultimo": resumo(publicados[-1] if publicados else None),
            "proximo": resumo(proximos[0] if proximos else None)}


def enviar(status):
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    corpo = json.dumps(status, ensure_ascii=False, indent=1).encode()
    if not (url and key):
        print(corpo.decode())
        return
    req = urllib.request.Request(
        f"{url}/storage/v1/object/materiais/saude/status.json", data=corpo, method="POST",
        headers={"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json",
                 "x-upsert": "true", "cache-control": "no-cache"})
    with urllib.request.urlopen(req, timeout=30) as r:
        print(f"Saúde gravada no painel (HTTP {r.status}).")


def main():
    partes = {}
    for nome, fn in (("pacote", checar_pacote), ("robos", checar_robos), ("token", checar_token), ("fila", checar_fila)):
        try:
            partes[nome] = fn()
        except Exception as e:
            partes[nome] = {"ok": None, "msg": f"verificação falhou ({e.__class__.__name__})"}
    status = {"gerado_em": AGORA.isoformat(timespec="minutes"),
              "ok": all(p.get("ok") is not False for p in partes.values()), **partes}
    for nome, p in partes.items():
        print(f"{'OK ' if p.get('ok') else '!! ' if p.get('ok') is False else '?  '}{nome}: {p.get('msg')}")
    try:
        enviar(status)
    except Exception as e:
        print(f"::warning::não gravei a saúde no painel: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
