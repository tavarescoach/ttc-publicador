"""Revisão do Formato Protagonista e da ficha da persona (diretrizes/protagonista.md, seção 10; aprovado em 26/11/2026).

Vale para estático e carrossel que tenham `protagonista` ou `narrativa`, e para todo estático/carrossel do ciclo
(id "k-...") com data a partir de INICIO. Usado por render/revisar.py; também roda sozinho:
    python render/protagonista.py render/pedidos/<id>.json
"""
import json
import os
import re
import sys
import unicodedata

INICIO = "2026-11-28"  # primeiro ciclo escrito no formato novo
AQUI = os.path.dirname(os.path.abspath(__file__))
PERSONAS_JSON = os.path.join(AQUI, "..", "diretrizes", "personas.json")
MIDIA = "supabase.co/storage/v1/object/public/midia/"
TIPOS = {"espelho", "ponte", "alerta"}
# campo da ficha_persona -> bloco da ficha em diretrizes/personas.json
FICHA = {"objetivo": "objetivos", "desejo": "desejos", "dor": "dores", "erro": "erros", "objecao": "objecoes"}
NO_TEXTO = ("desejo", "dor", "erro")  # estes precisam aparecer no texto do post (aviso por palavras em comum)
VOCE = re.compile(r"\b(?:voc[eê]s?|seu|sua|seus|suas|te|teu|tua)\b", re.I)
NUMERO_RESULTADO = re.compile(r"\d+(?:[.,]\d+)?\s*(?:kg|quilos?|%|cm|cent[ií]metros?|libras?)\b", re.I)
PRAZO = re.compile(r"\d+\s*(?:dias?|semanas?|mes(?:es)?)\b", re.I)
VAZIAS = {"para", "como", "quando", "mais", "menos", "sobre", "entre", "depois", "antes", "ainda", "porque",
          "muito", "pouco", "desde", "outro", "outra", "essa", "esse", "isso", "aquele", "aquela", "sempre"}


def _norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[\"'“”‘’()]", "", s)
    return re.sub(r"\s+", " ", s).strip(" .;:!?")


def _palavras(s):
    return {w for w in re.findall(r"[a-z]{5,}", _norm(s)) if w not in VAZIAS}


def carregar_personas(caminho=PERSONAS_JSON):
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def itens_validos(personas, persona, bloco):
    ficha = personas.get(persona) or {}
    itens = list(ficha.get(bloco) or [])
    if not itens:
        for outra in ficha.get("herda") or []:
            itens += (personas.get(outra) or {}).get(bloco) or []
    return itens


def _txt(v):
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        return "\n".join(_txt(x) for x in v)
    return ""


def _texto_slide(s):
    return "\n".join(_txt(s.get(k)) for k in ("rotulo", "titulo", "subtitulo", "texto", "nota", "numero", "unidade", "cta"))


def aplica(p):
    if p.get("formato") not in ("estatico", "carrossel", None):
        return False
    if p.get("formato") is None and not p.get("slides"):
        return False
    if p.get("protagonista") or p.get("narrativa"):
        return True
    data = str(p.get("data") or p.get("quando") or "")[:10]
    return str(p.get("id") or "").startswith("k-") and data >= INICIO


def revisar_protagonista(p, personas=None):
    """Devolve (problemas, avisos)."""
    if not aplica(p):
        return [], []
    personas = personas or carregar_personas()
    problemas, avisos = [], []
    prot = p.get("protagonista") or {}
    nar = p.get("narrativa") or {}
    slides = p.get("slides") or []
    carrossel = p.get("formato") != "estatico"

    # protagonista
    if not prot:
        problemas.append("Formato Protagonista: falta o campo `protagonista` (tipo, persona, desejo, vilão, nível de consciência).")
    else:
        if prot.get("tipo") not in TIPOS:
            problemas.append("Formato Protagonista: `protagonista.tipo` precisa ser espelho, ponte ou alerta.")
    persona = prot.get("persona") or nar.get("persona")
    if not persona or persona.startswith("_") or persona not in personas:
        problemas.append("Formato Protagonista: persona ausente ou desconhecida (rafael, thiago ou feminina).")
        persona = None

    # narrativa
    if not nar:
        problemas.append("Formato Protagonista: falta a ficha `narrativa`.")
    for campo in ("desejo", "vilao", "sucesso"):
        if nar and not str(nar.get(campo) or "").strip():
            problemas.append(f"Ficha narrativa sem `{campo}`.")
    for campo in ("desejo", "vilao"):
        v = str(nar.get(campo) or prot.get(campo) or "")
        if v and (" e " in f" {v} " or "," in v):
            avisos.append(f"`{campo}` parece ter mais de uma ideia (\"e\" ou vírgula): um desejo e um vilão por post.")
    if nar and not str(nar.get("cta_transicao") or "").strip():
        avisos.append("Ficha narrativa sem `cta_transicao` (salvar, responder, mandar para alguém).")

    # ficha da persona: nível de consciência + um item de cada bloco, copiado de diretrizes/personas.json
    ficha = nar.get("ficha_persona") or {}
    if not ficha:
        problemas.append("Falta `narrativa.ficha_persona` (consciencia, objetivo, desejo, dor, erro, objecao da persona).")
    else:
        nc = ficha.get("consciencia", prot.get("nivel_consciencia"))
        if not isinstance(nc, int) or not 1 <= nc <= 5:
            problemas.append("ficha_persona: `consciencia` precisa ser um número de 1 a 5.")
        elif prot.get("nivel_consciencia") not in (None, nc):
            avisos.append("Nível de consciência diferente em `protagonista` e em `ficha_persona`.")
        if persona:
            for campo, bloco in FICHA.items():
                v = ficha.get(campo)
                if not str(v or "").strip():
                    problemas.append(f"ficha_persona sem `{campo}`.")
                    continue
                validos = itens_validos(personas, persona, bloco)
                if _norm(v) not in {_norm(x) for x in validos}:
                    problemas.append(f"ficha_persona: `{campo}` não está na ficha de {persona} "
                                     f"(diretrizes/personas.json, bloco {bloco}). Copie um item da lista.")

    # o post usa desejo, dor e erro da ficha no texto (aviso: o texto pode parafrasear)
    corpo = _norm("\n".join(_texto_slide(s) for s in slides) + "\n" + (p.get("legenda") or ""))
    palavras_corpo = set(re.findall(r"[a-z]{5,}", corpo))
    for campo in NO_TEXTO:
        alvo = _palavras(ficha.get(campo))
        if alvo and not alvo & palavras_corpo:
            avisos.append(f"A `{campo}` da ficha da persona não aparece no texto do post (nem por palavras-chave).")
    obj = _palavras(ficha.get("objecao"))
    if carrossel and obj and not obj & palavras_corpo:
        avisos.append("A objeção da ficha da persona não aparece no slide do guia nem na legenda.")

    if not carrossel:
        return problemas, avisos

    # personagem em até 3 slides
    capa = slides[0] if slides else {}
    nome = str(nar.get("personagem_nome") or capa.get("pessoa") or "").strip()
    if nome:
        chave = _norm(nome.split()[-1]) if len(nome.split()) > 1 else _norm(nome)
        com_nome = [i for i, s in enumerate(slides, 1) if re.search(r"\b" + re.escape(chave) + r"\b", _norm(_texto_slide(s)))]
        if len(com_nome) > 3:
            problemas.append(f"O personagem ({nome}) aparece em {len(com_nome)} slides; o máximo é 3 (o herói é o leitor).")
    else:
        avisos.append("Sem `narrativa.personagem_nome` nem `pessoa` na capa: não deu para contar o personagem nos slides.")

    # o leitor entra no slide 2
    if len(slides) >= 4 and not any(VOCE.search(_texto_slide(s)) for s in slides[1:4]):
        problemas.append("Nenhum \"você\" entre os slides 2 e 4: o leitor precisa entrar no slide 2.")

    # slide 9 = o guia, com foto do Luan
    if len(slides) >= 9:
        s9 = slides[8]
        foto = s9.get("foto_url") or s9.get("foto") or ""
        if s9.get("tipo") != "texto_foto" or MIDIA not in foto:
            problemas.append("Slide 9 (o guia) precisa ser `texto_foto` com foto do Luan do acervo.")

    # promessa com número e prazo no fim do arco
    for i, s in enumerate(slides[7:10], 8):
        t = _texto_slide(s)
        if NUMERO_RESULTADO.search(t) and PRAZO.search(t):
            problemas.append(f"Slide {i}: promessa com número e prazo. Sucesso é identidade, nunca número com prazo.")

    # aluno em primeira pessoa só com autorização
    for i, s in enumerate(slides, 1):
        if s.get("narrador") == "aluno" and not s.get("aluno_autorizado"):
            problemas.append(f"Slide {i}: fala de aluno sem `aluno_autorizado: true`.")
    return problemas, avisos


if __name__ == "__main__":
    for caminho in sys.argv[1:]:
        with open(caminho, encoding="utf-8") as f:
            pr, av = revisar_protagonista(json.load(f))
        print(json.dumps({"arquivo": caminho, "problemas": pr, "avisos": av}, ensure_ascii=False, indent=1))
