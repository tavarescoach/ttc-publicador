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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from protagonista import revisar_protagonista  # Formato Protagonista e ficha da persona (26/11/2026)

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
# 3º campo: True = liberado no GANCHO (capa/slide 1, tela 1 do story e 1ª linha da legenda).
# Decisão do Luan em 06/11/2026: pergunta, provocação, contraste, autoironia, gíria e caixa alta liberados no gancho;
# no miolo as regras continuam.
VICIOS_IA = [
    (r"\bn[ãa]o (?:é|foi|era|s[óo]|está)\b[^.!?\n]{1,70}[.!?,;]\s+(?:é|foi|era|mas)\b", "contraste encenado (\"não é X. É Y.\")", True),
    (r"\bn[ãa]o é sobre\b", "contraste encenado (\"não é sobre…\")", True),
    (r"\bn[ãa]o porque\b[^.!?\n]*[.!?]\s*porque\b", "contraste encenado (\"não porque… porque…\")", True),
    (r"\bmas sim\b", "contraste encenado (\"mas sim\")", True),
    (r"\b(?:menos|nada de) [^.,!?\n]{1,25}[.,]\s*mais\b", "contraste encenado (\"menos X, mais Y\")", True),
    (r"\bsem [^,.!?\n]{1,30}, sem [^,.!?\n]{1,30}", "lista de ausências (\"sem X, sem Y\")", False),
    (r"\b(?:o resultado|a verdade|o segredo|a resposta|o motivo|a diferença|o detalhe|o problema)\?\s", "pergunta respondida pelo próprio texto", True),
    (r"\b(?:o segredo|a verdade|spoiler|a real|a melhor parte)\s*:", "revelação com dois-pontos", True),
    (r"isso muda tudo|simples assim|leia de novo|ninguém te conta|pouca gente sabe|vamos falar sobre|próximo nível|virar a chave|desbloque|jornada|potencializ|ressignific", "frase de fábrica", False),
]

# Gancho com alarme de saúde (medo como isca) não sai sozinho: vai para "Precisa de você".
ALARME_SAUDE = r"\b(?:mata|matar|matando|vai morrer|morrer|morre cedo|infarto|avc|c[âa]ncer|dem[êe]ncia|derrame|morte s[úu]bita)\b"
MAX_CAIXA_ALTA_GANCHO = 2  # palavras em caixa alta permitidas no gancho (fora siglas)


def _gancho(textos, legenda):
    """Separa o gancho (1º texto e 1ª linha da legenda) do miolo."""
    linhas = [l for l in (legenda or "").splitlines() if l.strip()]
    primeira = linhas[0] if linhas else ""
    resto_leg = "\n".join(linhas[1:])
    g = "\n".join(([textos[0]] if textos else []) + [primeira])
    m = "\n".join(textos[1:] + [resto_leg])
    return g, m


def _vicios(gancho, miolo):
    out = []
    for padrao, nome, livre_no_gancho in VICIOS_IA:
        alvo = miolo.lower() if livre_no_gancho else (gancho + "\n" + miolo).lower()
        m = re.search(padrao, alvo)
        if m:
            out.append(f'Soa como IA: {nome} em "{m.group(0).strip()[:60]}".')
    return out


def _caixa_alta(texto):
    return {w for w in re.findall(r"\b[A-ZÁÉÍÓÚÂÊÔÃÕÇ]{4,}\b", texto) if w not in SIGLAS}


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

    # vícios de texto de IA: no gancho, pergunta/contraste/provocação liberados (06/11/2026); no miolo, não
    textos = textos_slides(p)
    if p.get("formato") == "estatico_v2":  # a frase da arte é o gancho; a pauta repete a frase
        frase_v2 = " ".join(_txt(p.get(c)) for c in ("frase_branca", "frase_vermelha")).replace("\n", " ").strip()
        gancho, miolo = _gancho(textos or [frase_v2], legenda)
    else:
        gancho, miolo = _gancho(textos, legenda)
        miolo = miolo + "\n" + (p.get("pauta") or "") + "\n" + _txt(p.get("frase"))
    problemas += _vicios(gancho, miolo)
    if "—" in tudo:
        problemas.append("Travessão (—) no texto: troque por ponto, vírgula ou quebra de linha.")
    m = re.search(ALARME_SAUDE, gancho.lower())
    if m:
        problemas.append(f'Gancho com alarme de saúde ("{m.group(0)}"): provocação sim, medo não. Confira antes de sair.')

    # caixa alta: até 2 palavras no gancho da legenda (a capa já sai em caixa alta pelo modelo); no miolo, até 2
    linhas = [l for l in legenda.splitlines() if l.strip()]
    g_leg = _caixa_alta(linhas[0] if linhas else "")
    if len(g_leg) > MAX_CAIXA_ALTA_GANCHO:
        problemas.append("Caixa alta demais no gancho da legenda: " + ", ".join(sorted(g_leg)[:5]) + ".")
    gritos = set()
    for t in textos_slides(p)[1:] + ["\n".join(linhas[1:])]:
        gritos |= _caixa_alta(t)
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
    if formato == "estatico_v2":
        pr, av = revisar_estatico_v2(p, legenda)
        problemas += pr
        avisos += av
    elif formato == "estatico":
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

    # Formato Protagonista e ficha da persona (diretrizes/protagonista.md, seção 10)
    pr, av = revisar_protagonista(p)
    problemas += pr
    avisos += av

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


FUNCOES_V2 = {"dor", "erro", "crenca", "objecao", "valor"}
MAX_PALAVRAS_V2 = 12
REFERENCIA_OUTRO_POST = r"\bveja\b|\bàs 1\dh|\bno próximo post\b|\bcontinua (?:no|na|amanhã|às)\b|\barrasta|\blink no carrossel\b|\bno carrossel\b|\bmeio-dia\b"
PRAZO = r"\b\d+\s*(?:dias?|semanas?|meses|m[eê]s)\b"


def revisar_estatico_v2(p, legenda):
    """Estático v2 (diretrizes/estatico.md, 26/11/2026): uma ideia completa, da ficha da persona, sem famoso."""
    out, av = [], []
    for c in ("funcao", "persona", "campo_ficha", "angulo_complementar", "frase_branca", "frase_vermelha"):
        if not p.get(c):
            out.append(f"Estático v2 sem `{c}`.")
    if p.get("funcao") and p["funcao"] not in FUNCOES_V2:
        out.append(f"Função do estático fora da lista: {p['funcao']}.")
    if not p.get("foto"):
        out.append("Estático v2 sem foto de fundo.")
    frase = " ".join(_txt(p.get(c)) for c in ("frase_branca", "frase_vermelha"))
    n = len(re.findall(r"\w+", frase))
    if n > MAX_PALAVRAS_V2:
        out.append(f"Frase do estático com {n} palavras (máximo {MAX_PALAVRAS_V2}).")
    todo = (frase + "\n" + (legenda or "")).lower()
    m = re.search(REFERENCIA_OUTRO_POST, todo)
    if m:
        out.append(f'O estático depende de outro post ("{m.group(0)}"): ele precisa valer sozinho.')
    if "método" in todo or "metodo" in todo:
        out.append("MÉTODO no estático: o convite fica no carrossel e na foto pessoal.")
    if re.search(PRAZO, frase.lower()):
        out.append("Número com prazo na frase do estático.")
    if p.get("pessoa") or p.get("personagem"):
        out.append("Estático v2 não usa famoso: a foto da pessoa vai para a capa do carrossel.")
    if re.search(r"\w+,\s+\w+.*\be\b", _txt(p.get("frase_branca"))):
        av.append("A frase pode ter duas ideias (vírgula e \"e\"); confira.")
    return out, av


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
# Stories v3 (Linha Editorial v3 + decisões de 26/11/2026): limite de palavras por tela (título + texto)
MAX_PALAVRAS_V3 = {"abertura": 12, "virada": 30, "post_novo": 15, "resultado": 30, "convite": 20}
FONTE_VERIFICADA = re.compile(r"(doi\.org/|10\.\d{4,}/|pubmed\.ncbi\.nlm\.nih\.gov/|ncbi\.nlm\.nih\.gov/pmc/)", re.I)


def _regras_v3(t):
    """Regras das telas v3 (diretrizes/stories.md, bloco v3)."""
    p, tela = [], t.get("tela")
    titulo, texto = _txt(t.get("titulo")), _txt(t.get("texto"))
    if tela == "abertura" and re.match(r"\s*hoje\b", titulo, re.I):
        p.append('Abertura começa com "Hoje": só o título com a ideia central.')
    if tela in ("virada", "resultado"):
        tem_numero = bool(re.search(r"\d", titulo + " " + texto))
        if t.get("fonte") and not FONTE_VERIFICADA.search(t.get("link") or ""):
            p.append("Fonte sem link verificado (DOI ou PubMed) no plano.")
        if tem_numero and not t.get("fonte"):
            p.append("Número na tela sem artigo verificado: troque por aplicação prática sem número ou ponha a fonte.")
    if tela == "resultado" and not texto:
        p.append("Resultado sem critério que dá para medir (teste, carga, tempo ou dor de 0 a 10).")
    if tela == "convite":
        palavra = (t.get("palavra") or "").upper()
        if not palavra:
            p.append("Convite sem a palavra do tema do dia.")
        elif palavra not in titulo.upper():
            p.append(f'Convite não pede a palavra do tema ("{palavra}").')
        if re.search(r"\b(m[ée]todo|ponto a)\b", titulo, re.I) and palavra not in ("MÉTODO", "METODO", "PONTO A"):
            p.append("Convite com palavra fixa (MÉTODO/PONTO A): nos stories a palavra é a do tema do dia.")
    return p


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
    maximo = MAX_PALAVRAS_V3.get(t.get("tela"), MAX_PALAVRAS_STORY) if t.get("modelo") == "v3" else MAX_PALAVRAS_STORY
    if palavras > maximo:
        problemas.append(f"{palavras} palavras na tela (máximo {maximo}).")
    if t.get("modelo") == "v3":
        problemas += _regras_v3(t)
    if not tela:
        problemas.append("Tela sem texto.")
    if t.get("aponta") not in DESTINOS:
        problemas.append("Story sem destino (post do dia, direct, respostas ou perfil).")
    if t.get("aponta") == "post" and not t.get("post_id"):
        problemas.append("Story-ponte sem o post de destino.")

    for w in PROIBIDAS:
        if re.search(r"(?<!\w)" + re.escape(w) + r"(?!\w)", baixo):
            problemas.append(f'Palavra fora da marca: "{w}".')
    titulo = _txt(t.get("titulo"))
    g_story = titulo or (tela[0] if tela else "")
    m_story = "\n".join(x for x in tela if x != g_story)
    problemas += _vicios(g_story, m_story)
    if "—" in tudo:
        problemas.append("Travessão (—) no texto.")
    m = re.search(ALARME_SAUDE, g_story.lower())
    if m:
        problemas.append(f'Gancho com alarme de saúde ("{m.group(0)}"): provocação sim, medo não.')
    # caixa alta: 1 palavra liberada na primeira tela; nas outras, nenhuma
    corpo_caps = tela[1:] if t.get("rotulo") else tela
    gritos = _caixa_alta(" ".join(corpo_caps[1:])) if corpo_caps else set()
    if len(_caixa_alta(corpo_caps[0] if corpo_caps else "")) > 1:
        gritos |= _caixa_alta(corpo_caps[0])
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
