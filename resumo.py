"""Resumo da véspera: o que sai amanhã, o que espera o Luan e o que ele faz amanhã.

Lê o painel (Supabase) e grava resumo/amanha.md. Roda no robô "Resumo da véspera",
disparado pela tarefa agendada das 21h, que envia o texto para o celular do Luan.

Variáveis: SUPABASE_URL, SUPABASE_SERVICE_KEY
"""
import datetime as dt
import json
import os
import sys
import urllib.request

PASTA = os.path.dirname(os.path.abspath(__file__))
BRT = dt.timezone(dt.timedelta(hours=-3))
URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
TIPO = {"CARROSSEL": "Carrossel", "REELS": "Reels", "IMAGEM": "Estático", "STORY": "Story"}
DIAS = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]


def get(caminho):
    req = urllib.request.Request(f"{URL}/rest/v1/{caminho}", headers={"apikey": KEY, "Authorization": f"Bearer {KEY}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def local(iso):
    return dt.datetime.fromisoformat(iso).astimezone(BRT)


def revisoes():
    pasta = os.path.join(PASTA, "render", "revisoes")
    out = {}
    if os.path.isdir(pasta):
        for n in os.listdir(pasta):
            if n.endswith(".json"):
                with open(os.path.join(pasta, n), encoding="utf-8") as f:
                    r = json.load(f)
                out[r["id"]] = r
    return out


def main():
    agora = dt.datetime.now(BRT)
    amanha = (agora + dt.timedelta(days=1)).date()
    rotulo = f"{DIAS[amanha.weekday()]} {amanha:%d/%m}"
    conteudos = get("conteudos?select=id,pauta,tipo,etapa,quando&etapa=in.(agendado,pronto)")
    tarefas = get(f"tarefas?select=*&data=eq.{amanha.isoformat()}&order=ordem")
    rev = revisoes()

    sai = sorted((c for c in conteudos if c["etapa"] == "agendado" and c.get("quando") and local(c["quando"]).date() == amanha),
                 key=lambda c: c["quando"])
    precisa = sorted((c for c in conteudos if c["etapa"] == "pronto"), key=lambda c: c.get("quando") or "9")
    fazer = [t for t in tarefas if not t.get("apagada") and t.get("acao") != "aprovar"]

    linhas = [f"Amanhã, {rotulo}"]
    linhas.append("")
    if sai:
        linhas.append("Sai sozinho:")
        for c in sai:
            linhas.append(f"• {local(c['quando']):%H:%M} {TIPO.get(c['tipo'], c['tipo'])}: {(c.get('pauta') or c['id'])[:70]}")
        linhas.append("Para vetar: painel → Hoje → Vetar, até o horário do post.")
    else:
        linhas.append("Nada agendado para sair amanhã.")
    if precisa:
        linhas.append("")
        linhas.append(f"Precisa de você ({len(precisa)}):")
        for c in precisa[:5]:
            r = rev.get(c["id"]) or {}
            motivo = ((r.get("problemas") or []) + (r.get("atencao") or []) or ["revisar e aprovar"])[0]
            quando = f" ({local(c['quando']):%d/%m %H:%M})" if c.get("quando") else ""
            linhas.append(f"• {(c.get('pauta') or c['id'])[:60]}{quando}: {motivo}")
        if len(precisa) > 5:
            linhas.append(f"• e mais {len(precisa) - 5} no painel.")
    if fazer:
        linhas.append("")
        linhas.append("Você faz amanhã:")
        for t in fazer[:8]:
            hora = f"{t['horario']} " if t.get("horario") else ""
            linhas.append(f"• {hora}{t['titulo'][:80]}")
        if len(fazer) > 8:
            linhas.append(f"• e mais {len(fazer) - 8} na tela Hoje.")
    linhas.append("")
    linhas.append("Tela Hoje: https://ttc-painel.vercel.app/hoje.html")

    os.makedirs(os.path.join(PASTA, "resumo"), exist_ok=True)
    with open(os.path.join(PASTA, "resumo", "amanha.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")
    print("\n".join(linhas))
    return 0


if __name__ == "__main__":
    sys.exit(main())
