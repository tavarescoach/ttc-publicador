"""Muda o horário de posts ainda não publicados, no painel (Supabase, conteudos) e no fila.json.

Uso: python ajustes/ajustar_horarios.py ajustes/horarios.json
horarios.json: [{"id": "...", "quando": "AAAA-MM-DDTHH:MM:00-03:00", "motivo": "..."}]
Nunca mexe em publicado nem cancelado. Depois de aplicado, o item ganha "aplicado_em".
"""
import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRT = dt.timezone(dt.timedelta(hours=-3))
URL = os.environ["SUPABASE_URL"].rstrip("/")
KEY = os.environ["SUPABASE_SERVICE_KEY"]
H = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}


def main(caminho):
    pedidos = json.load(open(caminho, encoding="utf-8"))
    fila_p = os.path.join(RAIZ, "fila.json")
    fila = json.load(open(fila_p, encoding="utf-8"))
    for a in pedidos:
        if a.get("aplicado_em"):
            continue
        cid = urllib.parse.quote(a["id"])
        req = urllib.request.Request(f"{URL}/rest/v1/conteudos?id=eq.{cid}&etapa=not.in.(publicado,cancelado)",
                                     data=json.dumps({"quando": a["quando"]}).encode(), method="PATCH",
                                     headers=dict(H, Prefer="return=representation"))
        with urllib.request.urlopen(req, timeout=60) as r:
            mudou = json.loads(r.read())
        for i in fila:
            if i.get("id") == a["id"] and i.get("status", "pendente") in ("pendente", "erro", "atrasado"):
                i["quando"] = a["quando"]
                i["status"] = "pendente"
                i.pop("erro", None)
        a["aplicado_em"] = dt.datetime.now(BRT).isoformat(timespec="minutes")
        print(f"{a['id']} -> {a['quando']} (painel: {len(mudou)} linha)")
    json.dump(fila, open(fila_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(pedidos, open(caminho, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
