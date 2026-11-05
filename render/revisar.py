"""Revisão automática de um conteúdo antes de ir para o painel.

Decide se o conteúdo entra direto como "agendado" (o Luan só veta se quiser)
ou se vai para "Precisa de você", com os motivos.

- problemas: impedem o agendamento automático (texto cortado, palavra proibida, número sem fonte...).
- atencao: temas que o Luan escolheu revisar sempre (prova com aluno). Saúde publica sozinha, com a revisão de saúde.
- avisos: não impedem; só aparecem no painel.

Usado por render/render.py. Também roda sozinho: python render/revisar.py render/pedidos/<id>.json
"""
import datetime as dt
import glob
import json
import os
import re
import sys

BRT = dt.timezone(dt.timedelta(hours=-3))
JANELA_MIN_H = 3  # horas mínimas entre a revisão e a publicação para dar tempo de vetar

# "bora" e "shape" liberados em 02/11/2026: voz informal no gancho e na legenda (diretrizes/conteudo.md)
PROIBIDAS = ["foco força e fé", "foco, força e fé", "no pain no gain", "monstro", "maromba",
             "projeto verão", "resultado garantido", "garantimos", "100% garantido", "últimas vagas", "só hoje"]
SENSIVEIS = [r"horm[oô]n", r"testosteron", r"estrog[eê]n", r"suplement", r"creatina", r"\bwhey\b", r"glp-?1",
             r"ozempic", r"mounjaro", r"wegovy", r"semaglut", r"tirzepat", r"rem[eé]dio", r"medicament",
             r"anaboliz", r"esteroid", r"\btrt\b", r"\bdiabet", r"hipertens", r"gravidez|gestante|p[oó]s-parto",
             r"menopaus", r"\bles[aã]o\b|\bles[oõ]es\b"]
PROVA = [r"\b(meu|minha|nosso|nossa) alun[oa]", r"\balun[oa]s? do ttc\b", r"antes e depois", r"\bcaso real do ttc\b"]
SIGLAS = {"MÉTODO", "METODO", "TTC", "BJSM", "BMJ", "JAMA", "OMS", "IMC", "HIIT", "LISS", "USP", "UFRJ", "FIFA",
          "NBA", "WNBA", "NFL", "VO2", "GLP-1", "ACSM", "NSCA", "PDF", "CEO", "EUA", "RJ", "SP", "DNA", "TV", "UFC",
          "NIH", "CDC", "NHS", "MIT", "UCLA", "MMA", "LT"}
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")

# Foto de terceiros: só licença que permite uso comercial (decisão do Luan, 24/10/2026)
LICENCAS_OK = {"cc-by", "cc-by-sa", "dominio-publico", "cc0"}
# Desde 02/11/2026 (decisão do Luan, diretrizes/conteudo.md): foto da notícia como reprodução ou divulgação oficial,
# sempre com crédito na arte e página de origem.
LICENCAS_EDITORIAIS = {"reproducao", "divulgacao"}
MIDIA = "supabase.co/storage/v1/object/public/midia/"  # fotos do acervo do Luan (bucket)
MAX_PALAVRAS_MEME = 8
# Foto repetida (05/11/2026: estático e carrossel do mesmo dia saíram com a mesma foto do Bruninho).
# A mesma foto não entra em dois posts do feed dentro desta janela, nem por outro link (comparação por imagem).
JANELA_FOTO_DIAS = 21
HASH_PARECIDA = 10  # bits diferentes no dHash de 64 bits; até isso, é a mesma foto
AQUI = os.path.dirname(os.path.abspath(__file__))

# Vícios de texto de IA (skill copy-social-ttc, seção 4). Barram o agendamento automático.
VICIOS_IA = [
    (r"\bn[ãa]o (?:é|foi|era|s[óo]|está)\b[^.!?\n]{1,70}[.!?,;]\s+(?:é|foi|era|mas)\b", "contraste encenado (\"não é X. É Y.\")"),
    (r"\bn[ãa]o é sobre\b", "contraste encenado (\"não é sobre…\")"),
    (r"\bn[ãa]o porque\b[^.!?\n]*[.!?]\s*porque\b", "contraste encenado (\"não porque… porque…\")"),
    (r"\bmas sim\b", "contraste encenado (\"mas sim\")"),
    (r"\b(?:menos|nada de) [^.,!?\n]{1,25}[.,]\s*mais\b", "contraste encenado (\"menos X, mais Y\")"),
    (r"\bsem [^,.!?\n]{1,30}, sem [^,.!?\n]{1,30}", "lista de ausências (\"sem X, sem Y\")"),
    (r"\b(?:o resultado|a verdade|o segredo|a resposta|o motivo|a diferença|o detalhe|o problema)\?\s", "pergunta respondida pelo próprio texto"),
    (r"\b(?:o segredo|a verdade|spoiler|a real|a melhor parte)\s*:", "revelação com dois-pontos"),
    (r"isso muda tudo|simples assim|leia de novo|ninguém te conta|pouca gente sabe|vamos falar sobre|próximo nível|virar a chave|desbloque|jornada|potencializ|ressignific", "frase de fábrica"),
]


def _txt(s):
    return re.sub(r"\*\*", "", str(s or ""))


def textos_slides(p):
    out = []
    for s in p.get("slides", []):
        for c in ("titulo", "texto", "nota", "rotulo", "numero", "unidade", "cta", "subtitulo", "frase"):
            if s.get(c):
                out.append(_txt(s[c]))
    return out


def _norm_foto(u):
    u = re.sub(r"[?#].*$", "", str(u or "")).replace("http://", "https://")
    if "/object/public/" in u:  # bucket: midia/<data>/<arquivo>, igual ao "arquivo" das fotos pessoais
        u = u.split("/object/public/", 1)[1]
    return u


def fotos_do_pedido(p):
    """[(slide, foto normalizada)] de um pedido: slides, meme e foto pessoal."""
    out = []
    if p.get("foto"):
        out.append((1, _norm_foto(p.get("foto"))))
    if p.get("arquivo"):
        out.append((1, "midia/" + p["arquivo"]))
    for i, sl in enumerate(p.get("slides") or [], 1):
        u = sl.get("foto_url") or sl.get("foto")
        if u and not str(u).startswith("file://"):
            out.append((i, _norm_foto(u)))
    return [(i, u) for i, u in out if u]


def _dist(a, b):
    try:
        return bin(int(a, 16) ^ int(b, 16)).count("1")
    except (TypeError, ValueError):
        return 99


def _data(x):
    try:
        return dt.date.fromisoformat(str(x)[:10])
    except ValueError:
        return None


def fotos_repetidas(p, hashes=None, raiz=None, janela=JANELA_FOTO_DIAS):
    """Problemas de foto já usada em outro post do feed (mesmo link ou mesma imagem) dentro da janela."""
    raiz = raiz or os.path.dirname(AQUI)
    meu_id, minha = p.get("id"), _data(p.get("data") or p.get("quando"))
    if not minha:
        return []
    meu_q = str(p.get("quando") or minha)
    perto = lambda d: d and abs((d - minha).days) <= janela
    # quem sai primeiro fica com a foto: só conta post que sai antes deste (ou no mesmo horário, com id menor)
    antes = lambda o: (str(o.get("quando") or o.get("data") or ""), str(o.get("id"))) < (meu_q, str(meu_id))
    usados = {}  # foto normalizada -> id
    for arq in glob.glob(os.path.join(raiz, "render", "pedidos", "*.json")):
        try:
            o = json.load(open(arq, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if o.get("id") == meu_id or str(o.get("id", "")).startswith(("teste", "e-teste")):
            continue
        if perto(_data(o.get("data") or o.get("quando"))) and antes(o):
            for _, u in fotos_do_pedido(o):
                usados.setdefault(u, o.get("id"))
    out, vistos = [], set()
    for i, u in fotos_do_pedido(p):
        if u in usados and u not in vistos:
            vistos.add(u)
            out.append(f"Slide {i}: foto já usada em {usados[u]}. Troque por outra foto da pessoa ou do acervo.")
    if hashes:
        for arq in glob.glob(os.path.join(raiz, "render", "revisoes", "*.json")):
            try:
                r = json.load(open(arq, encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if (r.get("id") == meu_id or not perto(_data(r.get("data"))) or not antes(r)
                    or str(r.get("id", "")).startswith(("teste", "e-teste"))):
                continue
            for f in r.get("fotos") or []:
                for i, h in hashes.items():
                    if _dist(h, f.get("hash")) <= HASH_PARECIDA and i not in vistos:
                        vistos.add(i)
                        out.append(f"Slide {i}: a mesma imagem já saiu em {r['id']}. Troque por outra foto.")
    return out


def revisar(p, cortes=None, fotos_falharam=None, agora=None, hashes=None):
    agora = agora or dt.datetime.now(BRT)
    reels = p.get("formato") == "reels"
    slides = p.get("slides", [])
    legenda = p.get("legenda") or ""
    tudo = "\n".join(textos_slides(p) + [legenda, p.get("pauta") or "", _txt(p.get("frase"))])
    baixo = tudo.lower()
    problemas, atencao, avisos = [], [], []

    # horário
    quando = p.get("quando")
    try:
        q = dt.datetime.fromisoformat(quando) if quando else None
    except ValueError:
        q = None
    if not q:
        problemas.append("Sem dia e horário de publicação.")
    elif q < agora + dt.timedelta(hours=JANELA_MIN_H):
        problemas.append(f"Horário muito próximo ({q.astimezone(BRT):%d/%m %H:%M}): sem tempo para você vetar.")

    # texto cortado (medido na renderização)
    for n in cortes or []:
        problemas.append(f"Texto cortado no slide {n}.")
    for n in fotos_falharam or []:
        problemas.append(f"A foto do slide {n} não baixou.")

    # palavras proibidas da marca
    for w in PROIBIDAS:
        if re.search(r"(?<!\w)" + re.escape(w) + r"(?!\w)", baixo):
            problemas.append(f'Palavra fora da marca: "{w}".')

    # vícios de texto de IA (slides, legenda e título)
    for padrao, nome in VICIOS_IA:
        m = re.search(padrao, baixo)
        if m:
            problemas.append(f'Soa como IA: {nome} em "{m.group(0).strip()[:60]}".')
    if "—" in tudo:
        problemas.append("Travessão (—) no texto: troque por ponto, vírgula ou quebra de linha.")

    # caixa alta em texto corrido (a capa já sai em caixa alta pelo modelo)
    gritos = set()
    for t in textos_slides(p)[1:] + [legenda]:
        for w in re.findall(r"\b[A-ZÁÉÍÓÚÂÊÔÃÕÇ]{4,}\b", t):
            if w not in SIGLAS:
                gritos.add(w)
    if len(gritos) > 2:
        problemas.append("Caixa alta em texto corrido: " + ", ".join(sorted(gritos)[:5]) + ".")

    # emoji
    if len(EMOJI.findall(legenda)) > 3:
        problemas.append("Emoji em excesso na legenda.")

    # legenda e hashtags
    if len(legenda.strip()) < 40:
        problemas.append("Legenda vazia ou curta demais.")
    tags = re.findall(r"#\w+", legenda)
    if not tags:
        avisos.append("Legenda sem hashtags.")
    elif len(tags) > 8:
        problemas.append(f"Hashtags demais ({len(tags)}); o padrão é 3 a 5.")

    formato = p.get("formato")
    if formato == "estatico":
        problemas += revisar_estatico(p)
    elif formato == "meme":
        problemas += revisar_meme(p)
        if "MÉTODO" not in legenda.upper():
            avisos.append("Legenda do meme sem MÉTODO.")
    elif formato == "foto":
        if not p.get("arquivo"):
            problemas.append("Foto pessoal sem arquivo.")
        if "MÉTODO" not in legenda.upper():
            avisos.append("Legenda da foto sem MÉTODO.")
    elif not reels:
        # estrutura do carrossel
        if not slides:
            problemas.append("Carrossel sem slides.")
        elif len(slides) > 10:
            problemas.append(f"{len(slides)} slides: o Instagram aceita no máximo 10.")
        elif len(slides) < 5:
            avisos.append(f"Só {len(slides)} slides (o padrão é 9 a 10).")
        if slides and slides[-1].get("tipo") != "cta":
            problemas.append("O último slide não é o convite (CTA).")
        if slides and slides[-1].get("tipo") == "cta" and "MÉTODO" not in (slides[-1].get("cta") or "Me manda **MÉTODO** no direct."):
            problemas.append("O convite final não tem MÉTODO.")
        if "MÉTODO" not in legenda.upper():
            problemas.append("A legenda não tem o CTA MÉTODO.")
        # números precisam de fonte
        for i, s in enumerate(slides, 1):
            if s.get("tipo") == "numero" and not s.get("fonte"):
                problemas.append(f"Slide {i}: número sem fonte.")
        # números da legenda precisam bater com os slides
        nums_slides = set(re.findall(r"\d+(?:[.,]\d+)?", " ".join(textos_slides(p))))
        for n in set(re.findall(r"(\d+(?:[.,]\d+)?)\s*%", legenda)):
            if n not in nums_slides:
                problemas.append(f"A legenda cita {n}% e esse número não aparece nos slides.")
        # foto da capa: crédito, licença e nada promocional
        capa = slides[0] if slides and slides[0].get("tipo") == "capa" else None
        if capa:
            foto = capa.get("foto_url") or capa.get("foto") or ""
            banco = foto.startswith(("render/", "file://")) or re.search(r"pexels\.com|unsplash\.com", foto) or MIDIA in foto
            if not foto and _vai_buscar(capa):
                avisos.append("Foto da capa será buscada no render (Commons ou reprodução).")
            elif not foto:
                problemas.append("Capa sem foto: a capa precisa de rosto (famoso, Luan ou aluno autorizado).")
            elif not banco:
                problemas += _licenca_foto(capa, "da capa")
        # slide "o que eu faço" com foto do Luan (diretrizes/carrossel.md v2)
        if not any(MIDIA in (s.get("foto_url") or s.get("foto") or "") for s in slides):
            avisos.append("Sem foto do Luan do acervo (slide \"o que eu faço\").")
            if "método" in _txt(capa).lower():
                problemas.append("A capa tem MÉTODO: o convite fica só no último slide.")
        # fundos: nunca 3 iguais seguidos
        fundos = [s.get("fundo") for s in slides if s.get("tipo") != "capa"]
        for a, b, c in zip(fundos, fundos[1:], fundos[2:]):
            if a and a == b == c:
                avisos.append("Três slides seguidos com o mesmo fundo.")
                break

    # temas que sempre passam pelo Luan
    if p.get("prova") or any(re.search(r, baixo) for r in PROVA):
        atencao.append("Prova com aluno: confirme a autorização antes de publicar.")
    # saúde publica sozinha desde 24/10/2026 (diretrizes/ciclo.md), mas passa pela revisão de saúde
    achados = sorted({re.search(r, baixo).group(0) for r in SENSIVEIS if re.search(r, baixo)})
    if achados:
        tem_fonte = any(s.get("fonte") for s in slides) or bool(p.get("fontes"))
        problemas += revisar_saude(tudo, tem_fonte)
        avisos.append("Tema de saúde (" + ", ".join(achados[:4]) + "): passou pela revisão de saúde.")

    # foto repetida em outro post do feed (vale para todos os formatos)
    problemas += fotos_repetidas(p, hashes=hashes)

    ok = not problemas and not atencao
    return {
        "id": p.get("id"),
        "data": p.get("data") or str(p.get("quando") or "")[:10],
        "fotos": [{"slide": i, "hash": h} for i, h in sorted((hashes or {}).items())],
        "decisao": "agendado" if ok else "precisa",
        "problemas": problemas,
        "atencao": atencao,
        "avisos": avisos,
        "quando": quando,
        "revisado_em": agora.isoformat(timespec="minutes"),
    }


def revisar_estatico(p):
    """Estático das 7h (ciclo temático): notícia de pessoa conhecida, com fonte e crédito visíveis na arte."""
    out = []
    slides = p.get("slides") or []
    if not slides or slides[0].get("tipo") != "capa":
        return ["Estático sem a arte (slide de capa)."]
    c = slides[0]
    if not c.get("fonte"):
        out.append("Estático sem a fonte da notícia na arte (veículo e data).")
    if not c.get("link_noticia"):
        out.append("Estático sem o link da notícia (link_noticia).")
    if not c.get("foto") and _vai_buscar(c):
        pass  # o render busca no Commons ou usa a reprodução; se não achar, marca foto_nao_achada
    elif not c.get("foto"):
        out.append("Estático sem foto: a capa precisa do rosto da pessoa (Commons ou reprodução com crédito).")
    else:
        foto = c.get("foto_url") or c.get("foto") or ""
        banco = re.search(r"pexels\.com|unsplash\.com", foto) or MIDIA in foto
        if not banco:
            if not c.get("credito") or "foto:" not in c.get("credito", "").lower():
                out.append("Estático com foto e sem o crédito \"Foto: autor / origem\" na arte.")
            out += _licenca_foto(c, "do estático")
    if "método" in _txt(c).lower():
        out.append("O estático é editorial: sem MÉTODO na arte (vai na legenda).")
    return out


def _vai_buscar(c):
    """Pedido ainda não renderizado: a foto vem do Commons (pessoa) ou da reprodução (foto_reproducao)."""
    return bool((c.get("pessoa") or c.get("foto_reproducao")) and not c.get("foto_nao_achada"))


def _licenca_foto(c, onde):
    """Foto de terceiros: licença livre, ou reprodução/divulgação com crédito e origem (02/11/2026)."""
    lic = c.get("licenca")
    if not c.get("credito") or not lic:
        return [f"Foto {onde} sem crédito ou licença registrada."]
    if lic in LICENCAS_OK:
        return [] if c.get("pagina_origem") or onde == "da capa" else [f"Foto {onde} sem a página de origem (pagina_origem)."]
    if lic in LICENCAS_EDITORIAIS:
        out = []
        if not (c.get("pagina_origem") or c.get("link_noticia")):
            out.append(f"Foto {onde} em reprodução sem a página de origem.")
        if lic == "reproducao" and "reprodu" not in c.get("credito", "").lower():
            out.append(f"Foto {onde} em reprodução sem \"Reprodução\" no crédito.")
        return out
    return [f"Foto {onde} com licença '{lic}': use cc-by, cc-by-sa, domínio público, cc0, divulgação ou reprodução com crédito."]


def revisar_meme(p):
    """Meme (diretrizes/conteudo.md, seção 5): frase curta + foto do Luan."""
    out = []
    frase = _txt(p.get("frase"))
    n = len(re.findall(r"\w+", frase))
    if not frase:
        out.append("Meme sem frase.")
    elif n > MAX_PALAVRAS_MEME:
        out.append(f"Frase do meme com {n} palavras (máximo {MAX_PALAVRAS_MEME}).")
    if not p.get("foto"):
        out.append("Meme sem foto.")
    elif MIDIA not in str(p.get("foto")) and not str(p.get("foto")).startswith(("file://", "render/")):
        out.append("A foto do meme precisa ser do acervo do Luan (bucket midia).")
    return out


# ---------------------------------------------------------------- stories
MAX_PALAVRAS_STORY = 15
DESTINOS = {"post", "direct", "respostas", "perfil"}


def revisar_story(t, agora=None):
    """Revisa uma tela de story (dict com rotulo, titulo, texto, quando, aponta).

    Mesmas barras do carrossel para o texto, mais: até 15 palavras na tela e destino definido
    (post do dia, direct, respostas ou perfil). Saúde não vai para o Luan: só barra número sem fonte.
    """
    agora = agora or dt.datetime.now(BRT)
    tela = [_txt(t.get(c)) for c in ("rotulo", "titulo", "texto") if t.get(c)]
    tudo = "\n".join(tela)
    baixo = tudo.lower()
    problemas, avisos = [], []

    try:
        q = dt.datetime.fromisoformat(t["quando"]) if t.get("quando") else None
    except ValueError:
        q = None
    if not q:
        problemas.append("Sem dia e horário de publicação.")
    elif q < agora + dt.timedelta(hours=JANELA_MIN_H):
        problemas.append(f"Horário muito próximo ({q.astimezone(BRT):%d/%m %H:%M}): sem tempo para você vetar.")

    palavras = len(re.findall(r"\w+", " ".join(_txt(t.get(c)) for c in ("titulo", "texto") if t.get(c))))
    if palavras > MAX_PALAVRAS_STORY:
        problemas.append(f"{palavras} palavras na tela (máximo {MAX_PALAVRAS_STORY}).")
    if not tela:
        problemas.append("Tela sem texto.")
    if t.get("aponta") not in DESTINOS:
        problemas.append("Story sem destino (post do dia, direct, respostas ou perfil).")
    if t.get("aponta") == "post" and not t.get("post_id"):
        problemas.append("Story-ponte sem o post de destino.")

    for w in PROIBIDAS:
        if re.search(r"(?<!\w)" + re.escape(w) + r"(?!\w)", baixo):
            problemas.append(f'Palavra fora da marca: "{w}".')
    for padrao, nome in VICIOS_IA:
        m = re.search(padrao, baixo)
        if m:
            problemas.append(f'Soa como IA: {nome} em "{m.group(0).strip()[:60]}".')
    if "—" in tudo:
        problemas.append("Travessão (—) no texto.")
    gritos = {w for w in re.findall(r"\b[A-ZÁÉÍÓÚÂÊÔÃÕÇ]{4,}\b", " ".join(tela[1:] if t.get("rotulo") else tela)) if w not in SIGLAS}
    if gritos:
        problemas.append("Caixa alta em texto corrido: " + ", ".join(sorted(gritos)[:5]) + ".")
    if len(EMOJI.findall(tudo)) > 1:
        problemas.append("Emoji em excesso.")
    if re.search(r"\d+(?:[.,]\d+)?\s*%", tudo) and not t.get("fonte"):
        problemas.append("Percentual na tela sem fonte.")
    problemas += revisar_saude(tudo, bool(t.get("fonte")))

    return {"id": t.get("id"), "decisao": "agendado" if not problemas else "precisa", "problemas": problemas,
            "atencao": [], "avisos": avisos, "quando": t.get("quando"),
            "revisado_em": agora.isoformat(timespec="minutes")}


# Revisão de saúde (decisão do Luan, 24/10/2026): tema de saúde publica sozinho, mas barra o que não é defensável.
PRESCRICAO = [r"\btome\b", r"\btomar\b \d", r"\buse\b \d", r"\bdose\b", r"\bdosagem\b", r"\bsubstitua\b",
              r"\bpare (?:o|de tomar)\b", r"\bsuspenda\b", r"\bmg\b", r"\bcomprimido"]
PROMESSA = [r"\bcura\b", r"\bcurar\b", r"\bgarant", r"\bem \d+ (?:dias|semanas)\b.*\b(?:perde|elimina|queima)",
            r"\b(?:perca|elimine|queime) \d+ ?kg"]
REMEDIOS = r"ozempic|mounjaro|wegovy|semaglut|tirzepat|saxenda|liraglut|metformin|finasterid|minoxidil"


def revisar_saude(texto, tem_fonte):
    baixo = texto.lower()
    out = []
    for r in PRESCRICAO:
        m = re.search(r, baixo)
        if m:
            out.append(f'Saúde: linguagem de prescrição ("{m.group(0)}"). Fale do que a evidência mostra, sem orientar uso.')
            break
    for r in PROMESSA:
        m = re.search(r, baixo)
        if m:
            out.append(f'Saúde: promessa de resultado ("{m.group(0)[:40]}").')
            break
    if re.search(REMEDIOS, baixo) and not tem_fonte:
        out.append("Saúde: nome de remédio sem fonte registrada.")
    return out


if __name__ == "__main__":
    for caminho in sys.argv[1:]:
        with open(caminho, encoding="utf-8") as f:
            r = revisar(json.load(f))
        print(json.dumps(r, ensure_ascii=False, indent=1))
