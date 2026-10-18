"""Radar — coleta de notícias para o painel (roda no GitHub Actions, 2x por dia).

1. Lê os feeds de radar/fontes.json (últimas 72h).
2. Pré-filtra pelo nicho (palavras-chave PT/EN) e guarda as melhores por canal.
3. Grava radar/coleta.json (o que a curadoria do Claude lê) e insere no Supabase (tabela radar)
   só o que é novo — nota, pitch e status já dados nunca são sobrescritos.
4. Coloca no Radar as datas do calendário que estão chegando (radar/calendario.json).
5. Exporta radar/preferencias.json (o que o Luan salvou e descartou) para a curadoria aprender.

Fontes: radar/fontes.json é a base. O botão "Fontes" do painel grava eventos em materiais/radar/fontes/*.json
(adicionar | remover | pausar | reativar). Aqui os eventos são aplicados em ordem; para sites novos o feed é
descoberto sozinho (RSS direto, <link rel="alternate">, caminhos comuns e, por último, Google Notícias site:).
O resultado (com o desempenho de cada fonte na coleta) vai para materiais/radar/fontes-ativas.json, que o painel
lê, e para radar/fontes-extras.json no repositório.

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
JANELA_LENTAS = {"Harvard Health": dt.timedelta(days=14), "The Art Newspaper": dt.timedelta(days=7)}
POR_CANAL = 10
MIN_PAINEL = 6  # mínimo por fonte adicionada pelo painel
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


# ---------- fontes adicionadas pelo painel ----------

def storage(metodo, caminho, corpo=None, tipo="application/json", upsert=False):
    h = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": tipo, "cache-control": "no-cache"}
    if upsert:
        h["x-upsert"] = "true"
    dados = corpo if isinstance(corpo, (bytes, type(None))) else json.dumps(corpo, ensure_ascii=False).encode()
    req = urllib.request.Request(f"{URL}/storage/v1/{caminho}", method=metodo, headers=h, data=dados)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def eventos_painel():
    """Eventos gravados pelo botão Fontes do painel, em ordem de criação."""
    if not (URL and KEY):
        return []
    try:
        lista = json.loads(storage("POST", "object/list/materiais", {
            "prefix": "radar/fontes", "limit": 1000, "offset": 0, "sortBy": {"column": "name", "order": "asc"}}))
    except Exception as e:
        print(f"[aviso] não li os eventos de fontes: {e}")
        return []
    evs = []
    for o in sorted(lista, key=lambda o: o["name"]):
        if not o["name"].endswith(".json"):
            continue
        try:
            ev = json.loads(storage("GET", "object/materiais/radar/fontes/" + urllib.parse.quote(o["name"])))
            ev["_arquivo"] = o["name"]
            evs.append(ev)
        except Exception as e:
            print(f"[aviso] evento {o['name']} ilegível: {e}")
    return evs


def aplicar_eventos(base, evs):
    nomes_base = {f["canal"] for f in base}
    extras, pausadas = {}, set()
    for ev in evs:
        a, c = ev.get("acao"), (ev.get("canal") or "").strip()[:60]
        if not c:
            continue
        if a == "adicionar":
            url = (ev.get("url") or "").strip()
            if c in nomes_base or not re.match(r"^https?://[^\s/]+\.[^\s]+$", url):
                continue
            extras[c] = {"canal": c, "url": url, "peso": float(ev.get("peso") or 1.0),
                         "adicionado_em": ev.get("quando"), "evento": ev["_arquivo"]}
            pausadas.discard(c)
        elif a == "remover":
            extras.pop(c, None)
            pausadas.discard(c)
        elif a == "pausar":
            pausadas.add(c)
        elif a == "reativar":
            pausadas.discard(c)
    return extras, pausadas


def baixar(url, limite=400_000):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,application/xml,*/*"})
    with urllib.request.urlopen(req, timeout=12) as r:
        return r.geturl(), r.read(limite).decode("utf-8", "replace")


def qtd_itens(url):
    try:
        return len(feedparser.parse(url, agent=UA).entries)
    except Exception:
        return 0


def tem_itens(url):
    return qtd_itens(url) > 0


def descobrir_feed(url):
    """Devolve (feeds, modo) para um endereço qualquer colado no painel."""
    if tem_itens(url):
        return [url], "rss"
    final, pg = url, ""
    try:
        final, pg = baixar(url)
        achados = []
        for tag in re.findall(r"<link\b[^>]*>", pg, flags=re.I):
            if re.search(r"rel=[\"']?alternate", tag, re.I) and re.search(r"(rss|atom)\+xml", tag, re.I):
                m = re.search(r"href=[\"']([^\"']+)", tag, re.I)
                if m:
                    achados.append(urllib.parse.urljoin(final, html.unescape(m.group(1))))
        for f in achados[:4]:
            if tem_itens(f):
                return [f], "descoberto"
    except Exception as e:
        print(f"[aviso] não abri {url}: {e}")
    raiz = urllib.parse.urlsplit(final)
    base_url = f"{raiz.scheme}://{raiz.netloc}"
    caminho = raiz.path.rstrip("/")
    tentativas = []
    for pre in ([caminho] if caminho else []) + [""]:
        tentativas += [f"{base_url}{pre}/feed", f"{base_url}{pre}/rss", f"{base_url}{pre}/feed.xml", f"{base_url}{pre}/rss.xml"]
    tentativas += [f"{base_url}/atom.xml", f"{base_url}/index.xml"]
    for f in tentativas:
        if tem_itens(f):
            return [f], "descoberto"
    dominio = raiz.netloc.removeprefix("www.")
    alvo = dominio + (caminho if caminho and caminho.count("/") <= 2 else "")
    lang = re.search(r"<html[^>]*\blang=[\"']?([a-zA-Z-]+)", pg or "", re.I)
    br = dominio.endswith(".br") or bool(lang and lang.group(1).lower().startswith("pt"))
    termos = "(saude+OR+treino+OR+exercicio+OR+sono+OR+estudo)" if br else "(health+OR+fitness+OR+exercise+OR+sleep+OR+study)"
    loc = "hl=pt-BR&gl=BR&ceid=BR:pt-419" if br else "hl=en-US&gl=US&ceid=US:en"
    # do mais específico ao mais amplo; fica com o primeiro que traz um volume útil (5+ matérias na semana)
    tentativas_gn = [f"site:{urllib.parse.quote(alvo)}+{termos}", f"site:{urllib.parse.quote(alvo)}"]
    if alvo != dominio:
        tentativas_gn += [f"site:{urllib.parse.quote(dominio)}+{termos}", f"site:{urllib.parse.quote(dominio)}"]
    melhor, melhor_n = None, -1
    for q in tentativas_gn:
        gn = f"https://news.google.com/rss/search?q={q}+when:7d&{loc}"
        n = qtd_itens(gn)
        if n >= 5:
            return [gn], "google_news"
        if n > melhor_n:
            melhor, melhor_n = gn, n
    return [melhor], "google_news"


def montar_fontes():
    base = json.load(open(os.path.join(AQUI, "fontes.json"), encoding="utf-8"))
    evs = eventos_painel()
    extras, pausadas = aplicar_eventos(base, evs)
    fontes = []
    for f in base:
        fontes.append({**f, "origem": "base", "ativa": f["canal"] not in pausadas, "modo": "rss"})
    for c, e in extras.items():
        feeds, modo = descobrir_feed(e["url"])
        print(f"Fonte do painel: {c} -> {modo} ({feeds[0]})")
        fontes.append({"canal": c, "dominio": urllib.parse.urlsplit(e["url"]).netloc.removeprefix("www."), "peso": e["peso"],
                       "feeds": feeds, "origem": "painel", "url": e["url"], "modo": modo, "ativa": c not in pausadas,
                       "adicionado_em": e["adicionado_em"]})
    return fontes, (evs[-1]["_arquivo"] if evs else None)


def publicar_fontes(fontes, relatorio, ultimo_evento):
    estado = {
        "atualizado_em": AGORA.isoformat(), "ultimo_evento": ultimo_evento,
        "fontes": [{k: f.get(k) for k in ("canal", "dominio", "url", "peso", "feeds", "origem", "modo", "ativa", "adicionado_em")}
                   | relatorio.get(f["canal"], {}) for f in fontes],
    }
    extras = [f for f in estado["fontes"] if f["origem"] == "painel" or not f["ativa"]]
    with open(os.path.join(AQUI, "fontes-extras.json"), "w", encoding="utf-8") as fh:
        json.dump(extras, fh, ensure_ascii=False, indent=1)
    if URL and KEY:
        storage("POST", "object/materiais/radar/fontes-ativas.json",
                json.dumps(estado, ensure_ascii=False).encode(), upsert=True)
        print(f"Fontes publicadas no painel: {sum(f['ativa'] for f in fontes)} ativas de {len(fontes)}.")


def coletar(fontes):
    saida, relatorio = [], {}
    for f in fontes:
        if not f.get("ativa", True):
            relatorio[f["canal"]] = {"coletadas": 0, "aproveitadas": 0}
            continue
        itens, vistos, falhas = [], set(), 0
        for url in f["feeds"]:
            try:
                d = feedparser.parse(url, agent=UA)
            except Exception as e:
                print(f"[aviso] {f['canal']}: {url} falhou ({e})")
                falhas += 1
                continue
            if not d.entries:
                print(f"[aviso] {f['canal']}: sem itens em {url}")
                falhas += 1
            for e in d.entries:
                titulo = limpar(e.get("title"))
                link = e.get("link")
                if not titulo or not link:
                    continue
                if "news.google.com" in url:  # "Título - Reuters" -> "Título"
                    titulo = re.sub(r"\s+[-–|]\s+[^-–|]{2,40}$", "", titulo)
                quando = data_item(e)
                if quando and AGORA - quando > JANELA_LENTAS.get(f["canal"], JANELA):
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
        if f.get("origem") == "painel" and len(bons) < MIN_PAINEL:
            # fonte escolhida pelo Luan (cultura, celebridades, negócios): o filtro de palavras do nicho corta quase tudo,
            # então completa com as mais recentes e deixa a curadoria do Claude julgar a ponte com corpo e saúde
            resto = sorted([i for i in itens if i not in bons], key=lambda x: x["publicado_em"] or "", reverse=True)
            bons += resto[:MIN_PAINEL - len(bons)]
        relatorio[f["canal"]] = {"coletadas": len(itens), "aproveitadas": len(bons),
                                 "falhou": falhas == len(f["feeds"])}
        saida.extend(bons)
    buscas = 0
    for i in saida:  # imagem de prévia quando o feed não traz
        if not i["imagem"] and buscas < 60:
            i["imagem"] = og_image(i["link"])
            buscas += 1
    print("Por canal (aproveitadas/coletadas):",
          json.dumps({c: f"{r['aproveitadas']}/{r['coletadas']}" for c, r in relatorio.items()}, ensure_ascii=False))
    return saida, relatorio


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
    fontes, ultimo_evento = montar_fontes()
    itens, relatorio = coletar(fontes)
    try:
        publicar_fontes(fontes, relatorio, ultimo_evento)
    except Exception as e:
        print(f"::warning::Não publiquei a lista de fontes: {e}")
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
