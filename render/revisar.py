"""Revisão automática de um conteúdo antes de ir para o painel.

Decide se o conteúdo entra direto como "agendado" (o Luan só veta se quiser)
ou se vai para "Precisa de você", com os motivos.

- problemas: impedem o agendamento automático (texto cortado, palavra proibida, número sem fonte...).
- atencao: temas que o Luan escolheu revisar sempre (prova com aluno). Saúde publica sozinha, com a revisão de saúde.
- avisos: não impedem; só aparecem no painel.

Usado por render/render.py. Também roda sozinho: python render/revisar.py render/pedidos/<id>.json
"""
import datetime as dt
import json
import re
import sys

BRT = dt.timezone(dt.timedelta(hours=-3))
JANELA_MIN_H = 3  # horas mínimas entre a revisão e a publicação para dar tempo de vetar

PROIBIDAS = ["bora", "foco força e fé", "foco, força e fé", "no pain no gain", "monstro", "shape", "maromba",
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
        for c in ("titulo", "texto", "nota", "rotulo", "numero", "unidade", "cta", "subtitulo"):
            if s.get(c):
                out.append(_txt(s[c]))
    return out


def revisar(p, cortes=None, fotos_falharam=None, agora=None):
    agora = agora or dt.datetime.now(BRT)
    reels = p.get("formato") == "reels"
    slides = p.get("slides", [])
    legenda = p.get("legenda") or ""
    tudo = "\n".join(textos_slides(p) + [legenda, p.get("pauta") or ""])
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
            banco = foto.startswith(("render/", "file://")) or re.search(r"pexels\.com|unsplash\.com", foto)
            if foto and not banco:
                if not capa.get("credito") or not capa.get("licenca"):
                    problemas.append("Foto da capa de fora dos bancos sem crédito ou licença registrada.")
                elif capa.get("licenca") not in LICENCAS_OK:
                    problemas.append(f"Foto da capa com licença '{capa.get('licenca')}': só vale licença com uso comercial "
                                     "(cc-by, cc-by-sa, dominio-publico). Troque a foto ou faça a capa sem foto.")
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

    ok = not problemas and not atencao
    return {
        "id": p.get("id"),
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
    if c.get("foto"):
        foto = c.get("foto_url") or c.get("foto") or ""
        banco = re.search(r"pexels\.com|unsplash\.com", foto)
        if not banco:
            if not c.get("credito") or "foto:" not in c.get("credito", "").lower():
                out.append("Estático com foto e sem o crédito \"Foto: autor / origem (licença)\" na arte.")
            if c.get("licenca") not in LICENCAS_OK:
                out.append(f"Foto do estático com licença '{c.get('licenca')}': só cc-by, cc-by-sa ou domínio público.")
            if not c.get("pagina_origem"):
                out.append("Foto do estático sem a página de origem (pagina_origem).")
    if "método" in _txt(c).lower():
        out.append("O estático é editorial: sem MÉTODO na arte (vai na legenda).")
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
