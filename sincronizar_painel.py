"""Sincroniza a fila de publicação com o painel (tabela `conteudos` no Supabase).

- fila.json   -> coluna da direita (pronto / agendado / publicado / erro / atrasado).
                 Atualiza sempre: o status do robô é a verdade.
- pautas.json -> coluna da esquerda (pauta / em_criacao / revisar). Opcional.
                 Só insere o que ainda não existe, para não desfazer o que você
                 moveu no painel.

Variáveis de ambiente:
  SUPABASE_URL          ex.: https://xyz.supabase.co
  SUPABASE_SERVICE_KEY  chave secreta (sb_secret_...)
  SIMULAR=1             opcional: só mostra o que enviaria
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

PASTA = os.path.dirname(os.path.abspath(__file__))
URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
SIMULAR = os.environ.get("SIMULAR") == "1"

STATUS_PARA_ETAPA = {
    "pendente": "agendado",
    "publicado": "publicado",
    "erro": "erro",
    "atrasado": "atrasado",
    "cancelado": "cancelado",
}
ETAPAS_ESQUERDA = {"pauta", "em_criacao", "revisar"}
CAMPOS = ["id", "data", "tipo", "pauta", "funil", "etapa", "quando", "arquivos", "legenda", "media_id", "capa", "link"]
CAMPOS_NOVOS = {"capa", "link"}  # se a tabela ainda não tiver essas colunas, envia sem elas


def ler(nome):
    caminho = os.path.join(PASTA, nome)
    if not os.path.exists(caminho):
        return []
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def primeira_linha(texto):
    for linha in (texto or "").splitlines():
        if linha.strip():
            return linha.strip()[:200]
    return None


def da_fila(item):
    quando = item.get("quando")
    linha = {
        "id": item["id"],
        "data": quando[:10] if quando else None,
        "tipo": item.get("tipo"),
        "pauta": item.get("pauta") or primeira_linha(item.get("legenda")) or item["id"],
        "funil": item.get("funil"),
        "etapa": STATUS_PARA_ETAPA.get(item.get("status", "pendente"), "agendado"),
        "quando": quando,
        "arquivos": item.get("arquivos", []),
        "legenda": item.get("legenda"),
        "media_id": item.get("media_id"),
        "capa": item.get("capa"),
        "link": item.get("permalink"),
    }
    return linha


def da_pauta(item):
    etapa = item.get("etapa", "pauta")
    if etapa not in ETAPAS_ESQUERDA:
        etapa = "pauta"
    return {
        "id": item["id"],
        "data": item.get("data"),
        "tipo": item.get("tipo"),
        "pauta": item.get("pauta") or item["id"],
        "funil": item.get("funil"),
        "etapa": etapa,
        "quando": item.get("quando"),
        "arquivos": item.get("arquivos", []),
        "legenda": item.get("legenda"),
        "media_id": None,
        "capa": None,
        "link": None,
    }


def enviar(linhas, modo, campos=CAMPOS):
    """modo: 'merge' atualiza o que existe; 'ignore' só insere o que é novo."""
    if not linhas:
        return
    original = linhas
    linhas = [{c: l.get(c) for c in campos} for l in linhas]
    if SIMULAR:
        print(f"[simulação] {modo}: {len(linhas)} linha(s)")
        for l in linhas:
            print(f"   {l['etapa']:<10} {l['id']}  — {l['pauta']}")
        return
    req = urllib.request.Request(
        f"{URL}/rest/v1/conteudos?on_conflict=id",
        data=json.dumps(linhas, ensure_ascii=False).encode(),
        method="POST",
        headers={
            "apikey": KEY,
            "Content-Type": "application/json",
            "Prefer": f"resolution={'merge' if modo == 'merge' else 'ignore'}-duplicates,return=minimal",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            print(f"OK ({modo}): {len(linhas)} linha(s), HTTP {r.status}")
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors='replace')[:500].replace("\n", " ")
        if campos is CAMPOS and any(c in msg for c in CAMPOS_NOVOS):
            print("::warning::Tabela sem as colunas capa/link. Enviando sem elas.")
            return enviar(original, modo, [c for c in CAMPOS if c not in CAMPOS_NOVOS])
        print(f"::error::ERRO ({modo}): HTTP {e.code} — {msg}")
        raise SystemExit(1)


def respostas_criacoes():
    """criacoes/respostas/<id>.json -> atualiza a criação no painel.
    Só aplica se a criação ainda estiver na vez do Claude, então reenviar é seguro."""
    pasta = os.path.join(PASTA, "criacoes", "respostas")
    if not os.path.isdir(pasta):
        return
    import datetime
    for nome in sorted(os.listdir(pasta)):
        if not nome.endswith(".json"):
            continue
        with open(os.path.join(pasta, nome), encoding="utf-8") as f:
            resp = json.load(f)
        cid = resp.pop("id", nome[:-5])
        resp.setdefault("vez", "luan")
        resp["atualizado_em"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if SIMULAR:
            print(f"[simulação] criação {cid} -> etapa {resp.get('etapa')}")
            continue
        req = urllib.request.Request(
            f"{URL}/rest/v1/criacoes?id=eq.{urllib.parse.quote(cid)}&vez=eq.claude",
            data=json.dumps(resp, ensure_ascii=False).encode(), method="PATCH",
            headers={"apikey": KEY, "Content-Type": "application/json", "Prefer": "return=representation"},
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                n = len(json.loads(r.read() or b"[]"))
            print(f"criação {cid}: {'atualizada' if n else 'já respondida, ignorada'}")
        except urllib.error.HTTPError as e:
            print(f"::error::criação {cid}: HTTP {e.code} — {e.read().decode(errors='replace')[:300]}")


def cancelados():
    """ids que o Luan cancelou no painel: nunca são recriados nem sobrescritos."""
    if SIMULAR:
        return set()
    req = urllib.request.Request(f"{URL}/rest/v1/conteudos?etapa=eq.cancelado&select=id", headers={"apikey": KEY})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return {l["id"] for l in json.loads(r.read())}
    except Exception as e:
        print(f"::warning::não li os cancelados ({e})")
        return set()


def main():
    if not SIMULAR and not (URL and KEY):
        print("Faltam SUPABASE_URL e SUPABASE_SERVICE_KEY.")
        return 1
    fora = cancelados()
    enviar([da_pauta(i) for i in ler("pautas.json") if i.get("id") not in fora], "ignore")
    enviar([da_fila(i) for i in ler("fila.json") if i.get("id") not in fora], "merge")
    respostas_criacoes()
    return 0


if __name__ == "__main__":
    sys.exit(main())
