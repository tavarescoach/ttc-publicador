"""Prepara um reels enviado pelo painel para o Claude criar capa e legenda.

Uso: python render/preparar_reels.py <conteudo_id>

1. Lê o card na tabela conteudos (arquivos[0] = "materiais:<caminho do vídeo no bucket materiais>").
2. Baixa o vídeo do bucket privado "materiais" e copia para o bucket público "midia"
   em <data>/<id>/reels.<ext> (a API do Instagram precisa de URL pública).
3. Extrai 8 quadros (render/reels/<id>/quadro-N.jpg) e transcreve o áudio (faster-whisper, pt).
4. Grava render/reels/<id>/info.json com tudo o que o Claude precisa.
Variáveis: SUPABASE_URL, SUPABASE_SERVICE_KEY
"""
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
URL = os.environ["SUPABASE_URL"].rstrip("/")
KEY = os.environ["SUPABASE_SERVICE_KEY"]


def req(caminho, metodo="GET", dados=None, cab=None):
    r = urllib.request.Request(f"{URL}{caminho}", data=dados, method=metodo, headers={"apikey": KEY, **(cab or {})})
    with urllib.request.urlopen(r, timeout=300) as resp:
        return resp.read()


def main():
    cid = sys.argv[1]
    linhas = json.loads(req(f"/rest/v1/conteudos?id=eq.{urllib.parse.quote(cid)}&select=*"))
    if not linhas:
        print(f"::error::card {cid} não encontrado no painel")
        return 1
    c = linhas[0]
    origem = next((a for a in (c.get("arquivos") or []) if a.startswith("materiais:")), None)
    if not origem:
        print(f"::error::card {cid} sem vídeo enviado (arquivos não tem 'materiais:...')")
        return 1
    caminho = origem.split(":", 1)[1]
    ext = os.path.splitext(caminho)[1].lower() or ".mp4"
    pasta = os.path.join(AQUI, "reels", cid)
    os.makedirs(pasta, exist_ok=True)
    video = os.path.join("/tmp", f"{cid}{ext}")

    with open(video, "wb") as f:
        f.write(req("/storage/v1/object/materiais/" + urllib.parse.quote(caminho)))
    tam = os.path.getsize(video)
    print(f"vídeo baixado: {tam/1e6:.1f} MB")

    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video],
                               capture_output=True, text=True).stdout.strip() or 0)
    quadros = []
    for k, frac in enumerate([0.04, 0.12, 0.25, 0.38, 0.5, 0.62, 0.75, 0.9], 1):
        saida = os.path.join(pasta, f"quadro-{k}.jpg")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{dur*frac:.2f}", "-i", video, "-frames:v", "1",
                        "-vf", "scale=720:-2", "-q:v", "3", saida], check=True)
        quadros.append(f"render/reels/{cid}/quadro-{k}.jpg")

    transcricao = ""
    try:
        from faster_whisper import WhisperModel
        modelo = WhisperModel("small", device="cpu", compute_type="int8")
        segs, _ = modelo.transcribe(video, language="pt", vad_filter=True)
        transcricao = " ".join(s.text.strip() for s in segs).strip()
    except Exception as e:
        print(f"::warning::sem transcrição ({e})")

    data = (c.get("quando") or "")[:10] or c.get("data") or "sem-data"
    destino = f"{data}/{cid}/reels{ext}"
    tipo = "video/quicktime" if ext == ".mov" else "video/mp4"
    with open(video, "rb") as f:
        req("/storage/v1/object/midia/" + urllib.parse.quote(destino), "POST", f.read(),
            {"Content-Type": tipo, "x-upsert": "true"})
    print(f"vídeo copiado para midia/{destino}")

    info = {
        "id": cid, "pauta": c.get("pauta"), "notas": c.get("legenda"), "quando": c.get("quando"), "data": data,
        "funil": c.get("funil"), "duracao_s": round(dur, 1), "tamanho_mb": round(tam / 1e6, 1),
        "video_bucket": destino, "quadros": quadros, "transcricao": transcricao,
    }
    with open(os.path.join(pasta, "info.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    print(f"pronto: render/reels/{cid}/info.json ({len(transcricao)} caracteres de transcrição)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
