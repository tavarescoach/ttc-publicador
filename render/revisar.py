"""Revisão automática de um conteúdo antes de ir para o painel.

Decide se o conteúdo entra direto como "agendado" (o Luan só veta se quiser)
ou se vai para "Precisa de você", com os motivos.

- problemas: impedem o agendamento automático (texto cortado, palavra proibida, número sem fonte...).
- atencao: temas que o Luan escolheu revisar sempre (prova com aluno; saúde, hormônio, suplemento).
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

    if not reels:
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
        # fundos: nunca 3 iguais seguidos
        fundos = [s.get("fundo") for s in slides if s.get("tipo") != "capa"]
        for a, b, c in zip(fundos, fundos[1:], fundos[2:]):
            if a and a == b == c:
                avisos.append("Três slides seguidos com o mesmo fundo.")
                break

    # temas que sempre passam pelo Luan
    if p.get("prova") or any(re.search(r, baixo) for r in PROVA):
        atencao.append("Prova com aluno: confirme a autorização antes de publicar.")
    achados = sorted({re.search(r, baixo).group(0) for r in SENSIVEIS if re.search(r, baixo)})
    if achados:
        atencao.append("Tema de saúde (" + ", ".join(achados[:4]) + "): revise o tom antes de publicar.")

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


if __name__ == "__main__":
    for caminho in sys.argv[1:]:
        with open(caminho, encoding="utf-8") as f:
            r = revisar(json.load(f))
        print(json.dumps(r, ensure_ascii=False, indent=1))
