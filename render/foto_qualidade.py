"""Qualidade de foto da linha Dor → Movimento (diretrizes/dor-movimento.md, seção 6.1, 26/11/2026).

Regras que barram:
  1. Rosto visível: toda foto mostra o rosto do Luan (frente ou perfil), detectado pelo YuNet.
  2. Enquadramento: o rosto fica inteiro dentro da metade, entre 8% e 55% da altura dela (acima do texto).
  3. Nitidez: a foto não é ampliada no recorte (largura útil >= 1080 px) e o rosto não está tremido.

Uso no render (render/render.py) e sozinho, para conferir uma foto:
  python render/foto_qualidade.py <foto.jpg> [foco_y em %, padrão 30]
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
MODELO = os.path.join(AQUI, "assets", "modelos", "face_detection_yunet_2023mar.onnx")

LARG, ALT = 1080, 720           # cada metade do slide
AMPLIACAO_MAX = 1.02            # acima disso a foto foi ampliada (menos de 1080 px úteis)
FAIXA_ROSTO = (0.08, 0.55)      # centro do rosto entre 8% e 55% da altura da metade
LIMITE_TEXTO = 0.70             # o bloco de texto ocupa a base da metade (de 70% para baixo)
ROSTO_MIN = 0.06                # rosto com menos de 6% da largura da metade: aviso (rosto pequeno)
CONFIANCA = 0.75                # confiança mínima do detector
# Nitidez: variância do Laplaciano no rosto (rosto grande reduzido para 200 px de largura; rosto pequeno na resolução original).
# Limite inicial; calibrar nos 3 primeiros carrosséis (diretrizes/dor-movimento.md).
NITIDEZ_MIN = 40.0


def _cv():
    import cv2  # opencv-python-headless
    return cv2


def rostos(img):
    """Rostos detectados: [(x, y, w, h, confiança)] em pixels da imagem original, maior primeiro."""
    cv2 = _cv()
    h, w = img.shape[:2]
    esc = min(1.0, 1280 / max(w, h))  # o detector é mais estável em imagem de até ~1280 px
    peq = cv2.resize(img, (int(w * esc), int(h * esc))) if esc < 1 else img
    det = cv2.FaceDetectorYN.create(MODELO, "", (peq.shape[1], peq.shape[0]), CONFIANCA, 0.3, 50)
    _, achados = det.detect(peq)
    out = []
    for f in achados if achados is not None else []:
        x, y, fw, fh, conf = f[0] / esc, f[1] / esc, f[2] / esc, f[3] / esc, float(f[-1])
        out.append((x, y, fw, fh, conf))
    return sorted(out, key=lambda r: -r[2] * r[3])


def nitidez(img, rosto):
    cv2 = _cv()
    x, y, w, h = [int(round(v)) for v in rosto[:4]]
    x, y = max(0, x), max(0, y)
    recorte = img[y:y + h, x:x + w]
    if recorte.size == 0:
        return 0.0
    cinza = cv2.cvtColor(recorte, cv2.COLOR_BGR2GRAY)
    if cinza.shape[1] > 200:  # rosto grande: reduz para 200 px (nunca amplia rosto pequeno, que borraria a medida)
        cinza = cv2.resize(cinza, (200, max(1, int(200 * cinza.shape[0] / cinza.shape[1]))), interpolation=cv2.INTER_AREA)
    return float(cv2.Laplacian(cinza, cv2.CV_64F).var())


def _foco_y(foco):
    """'center 30%' ou 30 -> 0.30 (posição vertical do recorte, como no background-position do CSS)."""
    if isinstance(foco, (int, float)):
        return max(0.0, min(1.0, foco / 100))
    for parte in str(foco or "").split():
        if parte.endswith("%"):
            try:
                return max(0.0, min(1.0, float(parte[:-1]) / 100))
            except ValueError:
                pass
    return 0.30


def melhor_foco(caminho, altura=ALT, alvo=0.32):
    """Foco vertical ('center N%') que põe o centro do maior rosto a `alvo` da altura do recorte. None sem rosto."""
    cv2 = _cv()
    img = cv2.imread(caminho)
    if img is None:
        return None
    h, w = img.shape[:2]
    achados = rostos(img)
    if not achados:
        return None
    esc = max(LARG / w, altura / h)
    sobra = h * esc - altura
    if sobra <= 1:
        return "center 50%"
    x, y, fw, fh, _ = achados[0]
    centro = (y + fh / 2) * esc
    p = (centro - alvo * altura) / sobra
    return f"center {max(0, min(100, round(p * 100)))}%"


def avaliar(caminho, foco="center 30%", altura=ALT, limite_texto=LIMITE_TEXTO):
    """Avalia uma foto recortada como metade (1080×720) ou slide cheio (altura=1440), com background-size: cover.

    Devolve {"problemas": [...], "avisos": [...], "largura_util": int, "nitidez": float|None, "rosto": bool}.
    """
    cv2 = _cv()
    img = cv2.imread(caminho)
    if img is None:
        return {"problemas": ["a foto não abriu"], "avisos": [], "largura_util": 0, "nitidez": None, "rosto": False}
    h, w = img.shape[:2]
    problemas, avisos = [], []

    # recorte "cover": escala para cobrir 1080×720 e corta o excesso pela posição do foco
    ALT = altura  # noqa: N806 (mesma conta para metade e slide cheio)
    esc = max(LARG / w, ALT / h)
    largura_util = int(round(LARG / esc))  # quantos px da foto original viram os 1080 da metade
    if esc > AMPLIACAO_MAX:
        problemas.append(f"foto ampliada no recorte ({largura_util} px úteis; o mínimo é {LARG})")
    desl_y = (h * esc - ALT) * _foco_y(foco)
    desl_x = (w * esc - LARG) * 0.5

    achados = rostos(img)
    # só conta rosto que aparece na metade recortada
    visiveis = []
    for r in achados:
        x0, y0 = r[0] * esc - desl_x, r[1] * esc - desl_y
        x1, y1 = x0 + r[2] * esc, y0 + r[3] * esc
        if x1 > 0 and x0 < LARG and y1 > 0 and y0 < ALT:
            visiveis.append((r, x0, y0, x1, y1))
    if not visiveis:
        problemas.append("rosto não aparece (de costas, cortado, coberto ou fora do recorte)")
        return {"problemas": problemas, "avisos": avisos, "largura_util": largura_util, "nitidez": None, "rosto": False}

    r, x0, y0, x1, y1 = visiveis[0]
    if x0 < 0 or x1 > LARG or y0 < 0 or y1 > ALT:
        problemas.append("rosto cortado pela borda da metade")
    centro = (y0 + y1) / 2 / ALT
    if not FAIXA_ROSTO[0] <= centro <= FAIXA_ROSTO[1]:
        problemas.append(f"rosto fora da faixa (centro a {centro:.0%} da metade; o certo é de 8% a 55%)")
    if y1 / ALT > limite_texto:
        problemas.append("o texto da metade cobre o rosto")
    if (x1 - x0) / LARG < ROSTO_MIN:
        avisos.append("rosto pequeno na foto")
    n = nitidez(img, r)
    if n < NITIDEZ_MIN:
        problemas.append(f"rosto sem nitidez (nota {n:.0f}; o mínimo é {NITIDEZ_MIN:.0f})")
    return {"problemas": problemas, "avisos": avisos, "largura_util": largura_util, "nitidez": round(n, 1), "rosto": True}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    import json
    foco = sys.argv[2] if len(sys.argv) > 2 else "center 30%"
    print(json.dumps(avaliar(sys.argv[1], foco if foco.endswith("%") or " " in foco else f"center {foco}%"),
                     ensure_ascii=False, indent=1))
