"""Confere roteiros de reels (narração e b-roll) antes de irem para a lista do dia.

Regras: .claude/skills/copy-social-ttc/references/narracao-broll.md (seções 3, 6, 7, 11 e 17).

Uso:
  python render/revisar_roteiro.py tarefas.json            # todos os itens de reels/gravação de hoje em diante
  python render/revisar_roteiro.py tarefas.json --todos    # inclui os passados
  python render/revisar_roteiro.py roteiro.txt             # um roteiro solto, no formato de blocos

Formato esperado (um bloco por plano):
  0–3 s · IMAGEM: ...
     VOZ: "..."        (texto exato)   ou   PONTOS: ... · ... (pontos de fala)
     TELA: ...
Um item pode ter vários reels separados por linhas "══ SEG 19/10 ══".

Sai com código 1 se houver problema (aviso não conta).
"""
import datetime as dt
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from revisar import VICIOS_IA  # noqa: E402

PAL_POR_S = 2.8          # ritmo medido do Luan (seção 3)
MAX_PALAVRAS_FRASE = 18
VICIOS_FALA = [
    (r"fica (aqui )?comigo|até o final", "promessa de retenção (\"fica comigo até o final\")"),
    (r"siga em frente", "fecho genérico (\"siga em frente\")"),
    (r"presta atenção|agora vem a parte|e tem mais|enquanto isso", "ponte de fábrica"),
    (r"\boi,? pessoal\b|\bfala,? galera\b|\bnesse vídeo\b|\bneste vídeo\b", "abertura de apresentação"),
    (r"\bassim como\b|\bmantém-se\b|\boutrossim\b|\bademais\b|vale ressaltar|nesse sentido", "construção de texto escrito"),
]
BLOCO = re.compile(r"^\s*(\d+(?:[.,]\d+)?)\s*[–-]\s*(\d+(?:[.,]\d+)?)\s*s\b")
PALAVRAS_VAZIAS = set("a o e é de da do das dos em no na nos nas um uma com por para pra que se seu sua você".split())


def limpar(t):
    t = re.sub(r"\*\*|//|\[[^\]]*\]", " ", t)
    return t.strip().strip('"“”').strip()


def palavras(t):
    return re.findall(r"[\wÀ-ÿ-]+", limpar(t))


def secoes(texto):
    """Divide o detalhe em reels (marcador ══ ... ══). Sem marcador, o texto todo é um reels."""
    partes = re.split(r"^\s*══\s*(.+?)\s*══\s*$", texto, flags=re.M)
    if len(partes) == 1:
        return [("", texto)]
    return [(partes[i].strip(), partes[i + 1]) for i in range(1, len(partes), 2)]


def ler_blocos(texto):
    blocos, atual = [], None
    for linha in texto.splitlines():
        m = BLOCO.match(linha)
        if m:
            atual = {"ini": float(m.group(1).replace(",", ".")), "fim": float(m.group(2).replace(",", ".")),
                     "imagem": "", "voz": "", "pontos": "", "tela": "", "silencio": "silêncio" in linha.lower()}
            blocos.append(atual)
            im = re.search(r"IMAGEM:\s*(.*)", linha)
            if im:
                atual["imagem"] = im.group(1)
            continue
        if atual is None:
            continue
        for campo in ("VOZ", "PONTOS", "TELA", "IMAGEM"):
            m2 = re.match(rf"\s*{campo}:\s*(.*)", linha)
            if m2:
                atual[campo.lower()] += " " + m2.group(1)
                if campo == "VOZ" and "silêncio" in m2.group(1).lower():
                    atual["silencio"] = True
    return blocos


def revisar_reels(nome, texto):
    probs, avisos = [], []
    blocos = ler_blocos(texto)
    if not blocos:
        return None, None  # item sem roteiro em blocos (ex.: lembrete de agenda): nada a conferir

    falas = [b for b in blocos if b["voz"].strip() and not b["silencio"]]
    n_pal = sum(len(palavras(b["voz"])) for b in falas)
    n_sil = sum(1 for b in blocos if b["silencio"])
    tem_pontos = any(b["pontos"].strip() for b in blocos)

    for b in blocos:
        rot = f'{b["ini"]:g}–{b["fim"]:g} s'
        voz = limpar(b["voz"])
        if not voz:
            continue
        for frase in re.split(r"[.!?]+", voz):
            n = len(palavras(frase))
            if n > MAX_PALAVRAS_FRASE:
                probs.append(f"{rot}: frase com {n} palavras na voz (máx. {MAX_PALAVRAS_FRASE}): \"{frase.strip()[:60]}…\"")
        if re.search(r"\d", voz):
            probs.append(f"{rot}: algarismo na voz; escreva como se fala (\"quarenta\", \"dezoito por cento\")")
        baixo = voz.lower()
        gancho = b["ini"] < 3  # 0–3 s: pergunta, provocação e contraste liberados (06/11/2026)
        for padrao, desc, livre in VICIOS_IA + [(p_, d_, False) for p_, d_ in VICIOS_FALA]:
            if livre and gancho:
                continue
            m = re.search(padrao, baixo)
            if m:
                probs.append(f"{rot}: {desc} em \"{m.group(0)[:50]}\"")
        tela = limpar(b["tela"]).lower()
        if tela:
            pv = {w for w in palavras(baixo) if w not in PALAVRAS_VAZIAS}
            pt = {w for w in palavras(tela) if w not in PALAVRAS_VAZIAS}
            if pt and len(pv & pt) / len(pt) >= 0.7:
                avisos.append(f"{rot}: a tela repete a voz; a tela deve resumir com outras palavras")

    if "—" in texto:
        probs.append("travessão (—) no roteiro: use ponto ou //")

    fim = max(b["fim"] for b in blocos)
    m = re.search(r"~\s*(\d+)\s*s", texto)
    declarado = float(m.group(1)) if m else fim
    if not tem_pontos and n_pal:
        estimado = n_pal / PAL_POR_S + n_sil
        if abs(estimado - declarado) > max(3, 0.25 * declarado):
            avisos.append(f"duração: {n_pal} palavras ≈ {estimado:.0f} s no ritmo do Luan (2,8 pal/s), "
                          f"mas o roteiro diz ~{declarado:.0f} s")
    if n_sil == 0:
        avisos.append("sem [silêncio] antes da frase-assinatura")
    if blocos[0]["fim"] - blocos[0]["ini"] > 3.5:
        avisos.append("gancho com mais de 3 s")
    if falas and not falas[0]["ini"] <= 0.5:
        avisos.append("a voz não entra no primeiro segundo")
    return probs, avisos


def itens_de(caminho, todos):
    if caminho.endswith(".json"):
        hoje = dt.date.today().isoformat()
        for i in json.load(open(caminho, encoding="utf-8")):
            if i.get("apagada") or i.get("formato") not in ("reels", "gravacao", "broll"):
                continue
            if not todos and (i.get("data") or "") < hoje:
                continue
            yield f'{i["id"]} · {i.get("titulo", "")[:60]}', i.get("detalhe") or ""
    else:
        yield os.path.basename(caminho), open(caminho, encoding="utf-8").read()


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    total_probs = 0
    for nome, texto in itens_de(argv[1], "--todos" in argv):
        for sec, corpo in secoes(texto):
            probs, avisos = revisar_reels(sec, corpo)
            if probs is None:
                continue
            if not probs and not avisos:
                print(f"OK   {nome}{' · ' + sec if sec else ''}")
                continue
            print(f"{'ERRO' if probs else 'AVISO'} {nome}{' · ' + sec if sec else ''}")
            for p in probs:
                print("   problema:", p)
            for a in avisos:
                print("   aviso:   ", a)
            total_probs += len(probs)
    return 1 if total_probs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
