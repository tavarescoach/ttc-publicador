"""Radar — coleta de notícias para o painel (roda no GitHub Actions, 2x por dia).

1. Lê os feeds de radar/fontes.json (últimas 72h).
2. Pré-filtra pelo nicho (palavras-chave PT/EN) e guarda as melhores por canal.
3. Grava radar/coleta.json (o que a curadoria do Claude lê) e insere no Supabase (tabela radar)
   só o que é novo — nota, pitch e status já dados nunca são sobrescritos.
4. Coloca no Radar as datas do calendário que estão chegando (radar/calendario.json).
5. Exporta radar/preferencias.json (o que o Luan salvou e descartou) para a curadoria aprender.

Variáveis: SUPABASE_URL, SUPABASE_SERVICE_KEY (sem elas, só gera o arquivo).
"""
import calendar
import datetime as dt
import hashlib
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request

import feedparser

AQUI = os.path.dirname(os.path.abspath(__file__))
URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
BRT = dt.timezone(dt.timedelta(hours=-3))
AGORA = dt.datetime.now(dt.timezone.utc)
JANELA = dt.timedelta(hours=72)
POR_CANAL = 10
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36 ttc-radar"

# palavras do nicho -> peso (pt e en, minúsculas, sem acento tratado abaixo)
NICHO = {
    3: ["exercise", "exercicio", "workout", "treino", "strength", "forca", "muscle", "musculo", "musculacao", "resistance training",
        "weight training", "fitness", "sarcopenia", "hipertrofia", "hypertrophy", "creatine", "creatina", "protein", "proteina",
        "longevity", "longevidade", "personal trainer", "academia", "gym"],
    2: ["sleep", "sono", "obesity", "obesidade", "weight loss", "emagrec", "ozempic", "wegovy", "mounjaro", "glp-1", "semaglutide",
        "tirzepatide", "metabolism", "metabolismo", "testosterone", "testosterona", "menopause", "menopausa", "diabetes", "insulin",
        "heart", "coracao", "cardio", "blood pressure", "pressao", "cholesterol", "colesterol", "aging", "envelhec", "bone", "osso",
        "osteopor", "injury", "lesao", "running", "corrida", "marathon", "maratona", "diet", "dieta", "nutrition", "nutricao",
        "fat", "gordura", "body", "corpo", "walking", "caminhada", "steps", "passos", "stress", "estresse", "burnout",
        "alcohol", "alcool", "supplement", "suplement", "vitamin", "vitamina", "posture", "postura", "back pain", "dor nas costas"],
    1: ["health", "saude", "wellness", "bem-estar", "brain", "cerebro", "mental", "study", "estudo", "research", "pesquisa",
        "scientists", "cientistas", "wearable", "smartwatch", "oura", "whoop", "garmin", "athlete", "atleta", "sport", "esporte",
        "football", "futebol", "olympic", "olimpi", "doctor", "medico", "hormone", "hormonio", "energy", "energia", "productivity",
        "produtividade", "work", "trabalho", "ai ", "inteligencia artificial"],
}
FORA = ["horoscop", "celebrity", "celebridade", "bbb", "novela", "recipe", "receita de", "crime", "shooting", "election",
        "eleicao", "war ", "guerra", "murder", "assassin"]


def sem_acento(t):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", t.lower()) if unicodedata.category(c) != "Mn")


def pontuar(texto, peso_canal):
    t = sem_acento(texto)
    if any(f in t for f in FORA):
        return 0
    p = sum(w for w, termos in NICHO.items() for k in termos if k in t)
    return round(p * peso_canal, 2)


def limpar(t):
    t = re.sub(r"<[^>]+>", " ", t or "")
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def data_item(e):
    for k in ("published_parsed", "updated_parsed"):
        if e.get(k):
            return dt.datetime.fromtimestamp(calendar.timegm(e[k]), dt.timezone.utc)
    return None


def imagem_feed(e):
    for k in ("media_content", "media_thumbnail"):
        for m in e.get(k) or []:
            if m.get("url"):
                return m["url"]
    for l in e.get("links") or []:
        if (l.get("type") or "").startswith("image") and l.get("href"):
            return l["href"]
    m = re.search(r'<img[^>]+src="([^"]+)"', e.get("summary", "") or "")
    return m.group(1) if m else None


def og_image(link):
    if not link or "news.google.com" in link:
        return None
    try:
        req = urllib.request.Request(link, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=8) as r:
            pg = r.read(300_000).decode("utf-8", "replace")
        m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', pg) or \
            re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image', pg)
        return html.unescape(m.group(1)) if m else None
    except Exception:
        return None


def coletar():
    fontes = json.load(open(os.path.join(AQUI, "fontes.json"), encoding="utf-8"))
    saida, relatorio = [], {}
    for f in fontes:
        itens, vistos = [], set()
        for url in f["feeds"]:
            try:
                d = feedparser.parse(url, agent=UA)
            except Exception as e:
                print(f"[aviso] {f['canal']}: {url} falhou ({e})")
                continue
            if not d.entries:
                print(f"[aviso] {f['canal']}: sem itens em {url}")
            for e in d.entries:
                titulo = limpar(e.get("title"))
                link = e.get("link")
                if not titulo or not link:
                    continue
                if "news.google.com" in url:  # "Título - Reuters" -> "Título"
                    titulo = re.sub(r"\s+[-–|]\s+[^-–|]{2,40}$", "", titulo)
                quando = data_item(e)
                if quando and AGORA - quando > JANELA:
                    continue
                chave = sem_acento(titulo)[:80]
                if chave in vistos:
                    continue
                vistos.add(chave)
                resumo = limpar(e.get("summary"))[:400]
                itens.append({
                    "id": hashlib.sha1(link.encode()).hexdigest()[:16],
                    "canal": f["canal"], "titulo": titulo, "link": link,
                    "imagem": imagem_feed(e), "publicado_em": quando.isoformat() if quando else None,
                    "resumo": resumo, "pre": pontuar(titulo + " " + resumo, f.get("peso", 1)),
                })
        itens.sort(key=lambda x: (x["pre"], x["publicado_em"] or ""), reverse=True)
        bons = [i for i in itens if i["pre"] > 0][:POR_CANAL]
        relatorio[f["canal"]] = f"{len(bons)}/{len(itens)}"
        saida.extend(bons)
    buscas = 0
    for i in saida:  # imagem de prévia quando o feed não traz
        if not i["imagem"] and buscas < 60:
            i["imagem"] = og_image(i["link"])
            buscas += 1
    print("Por canal (aproveitadas/coletadas):", json.dumps(relatorio, ensure_ascii=False))
    return saida


def calendario_proximo():
    cal = json.load(open(os.path.join(AQUI, "calendario.json"), encoding="utf-8"))
    hoje = AGORA.astimezone(BRT).date()
    out = []
    for c in cal:
        for ano in (hoje.year, hoje.year + 1):
            mi, di = map(int, c["inicio"].split("-"))
            mf, df = map(int, c["fim"].split("-"))
            ini = dt.date(ano, mi, di)
            fim = dt.date(ano if (mf, df) >= (mi, di) else ano + 1, mf, df)
            if ini - dt.timedelta(days=21) <= hoje <= fim:
                out.append({
                    "id": f"cal-{c['slug']}-{ini.year}", "canal": "Calendário", "titulo": c["titulo"], "link": None,
                    "imagem": None, "publicado_em": dt.datetime(ini.year, ini.month, ini.day, 9, tzinfo=BRT).isoformat(),
                    "tema": c["tema"], "nota": c["nota"], "motivo": "Data do calendário que conversa com o seu público.",
                    "publico": c["publico"], "pitch": c["pitch"], "calendario": True, "curado": True,
                })
    return out


def supa(metodo, caminho, corpo=None, prefer=None):
    h = {"apikey": KEY, "Content-Type": "application/json"}
    if prefer:
        h["Prefer"] = prefer
    req = urllib.request.Request(f"{URL}/rest/v1/{caminho}", method=metodo, headers=h,
                                 data=json.dumps(corpo, ensure_ascii=False).encode() if corpo is not None else None)
    with urllib.request.urlopen(req, timeout=60) as r:
        t = r.read()
        return json.loads(t) if t else None


def main():
    itens = coletar()
    with open(os.path.join(AQUI, "coleta.json"), "w", encoding="utf-8") as f:
        json.dump({"coletado_em": AGORA.isoformat(), "itens": itens}, f, ensure_ascii=False, indent=1)
    print(f"{len(itens)} notícias pré-selecionadas.")
    if not (URL and KEY):
        return 0
    campos = ["id", "canal", "titulo", "link", "imagem", "publicado_em"]
    try:
        supa("POST", "radar?on_conflict=id", [{c: i[c] for c in campos} for i in itens],
             "resolution=ignore-duplicates,return=minimal")
        cal = calendario_proximo()
        if cal:
            supa("POST", "radar?on_conflict=id", cal, "resolution=merge-duplicates,return=minimal")
        print(f"Supabase: {len(itens)} notícias (só as novas entram) e {len(cal)} datas do calendário.")
        limite = (AGORA - dt.timedelta(days=14)).isoformat()
        supa("DELETE", f"radar?coletado_em=lt.{urllib.parse.quote(limite)}&status=in.(novo,descartado)&calendario=is.false",
             prefer="return=minimal")
        pref = supa("GET", "radar?status=in.(salvo,descartado,virou_pauta)&select=titulo,canal,tema,status&order=coletado_em.desc&limit=150")
        with open(os.path.join(AQUI, "preferencias.json"), "w", encoding="utf-8") as f:
            json.dump(pref, f, ensure_ascii=False, indent=1)
    except Exception as e:
        print(f"::error::Supabase: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
