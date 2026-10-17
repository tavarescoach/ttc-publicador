"""Gera o PDF do plano semanal a partir de pacotes/pacote-AAAA-MM-DD.md e guarda no bucket privado
"materiais" (pacotes/pacote-AAAA-MM-DD.pdf). O painel abre com link assinado.

Uso: python pacotes/gerar_pdf.py pacotes/pacote-2026-10-19.md [--local]
"""
import base64
import os
import sys
import urllib.parse
import urllib.request

import markdown
from playwright.sync_api import sync_playwright

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

CSS = """
@page{size:A4;margin:18mm 16mm 18mm 16mm}
*{box-sizing:border-box}
body{font-family:Inter,'Helvetica Neue',Arial,sans-serif;color:#0F172A;font-size:10.5pt;line-height:1.55;margin:0}
.capa{background:#07112A;color:#F8FAFC;padding:12mm 12mm 11mm;margin:0 0 8mm;border-radius:4px;border-bottom:3px solid #C1121F}
.capa img{height:30px}
.capa .eb{font-size:8.5pt;letter-spacing:3px;text-transform:uppercase;color:#FCA5A5;margin-top:12mm;font-weight:700}
.capa h1{font-size:26pt;line-height:1.1;margin:4mm 0 0;letter-spacing:-.02em;color:#fff;border:0}
.capa .sb{color:#94A3B8;margin-top:3mm;font-size:10pt}
h1{font-size:18pt;margin:8mm 0 3mm;letter-spacing:-.02em;border-bottom:2px solid #C1121F;padding-bottom:2mm}
h2{font-size:14pt;margin:7mm 0 2mm;letter-spacing:-.01em;page-break-after:avoid}
h3{font-size:11.5pt;margin:5mm 0 1.5mm;color:#C1121F;page-break-after:avoid}
h4{font-size:10.5pt;margin:4mm 0 1mm}
p{margin:1.5mm 0}
ul,ol{margin:1.5mm 0 1.5mm 5mm;padding:0}
li{margin:.6mm 0}
strong{color:#07112A}
blockquote{margin:3mm 0;padding:2.5mm 4mm;border-left:3px solid #C1121F;background:#F1F3F6;color:#1E293B}
table{border-collapse:collapse;width:100%;margin:3mm 0;font-size:9pt;page-break-inside:auto}
th{background:#07112A;color:#fff;text-align:left;padding:2mm;font-weight:600}
td{border-bottom:1px solid #E2E8F0;padding:2mm;vertical-align:top}
tr{page-break-inside:avoid}
code{background:#F1F3F6;padding:0 1mm;border-radius:2px;font-size:9pt}
hr{border:0;border-top:1px solid #E2E8F0;margin:6mm 0}
a{color:#C1121F;word-break:break-all}
"""


def main():
    md_path = sys.argv[1]
    nome = os.path.splitext(os.path.basename(md_path))[0]
    texto = open(md_path, encoding="utf-8").read()
    titulo = next((l.lstrip("# ").strip() for l in texto.splitlines() if l.startswith("# ")), nome)
    corpo = markdown.markdown("\n".join(l for l in texto.splitlines() if l.strip() != f"# {titulo}"),
                              extensions=["tables", "sane_lists"])
    logo = base64.b64encode(open(os.path.join(RAIZ, "render", "assets", "logo-lt.png"), "rb").read()).decode()
    html = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
<div class="capa"><img src="data:image/png;base64,{logo}" alt=""><div class="eb">Plano de conteúdo · @tavarescoach</div>
<h1>{titulo}</h1><div class="sb">Corpo forte, evolução sem acaso.</div></div>
{corpo}</body></html>"""
    saida = os.path.join(RAIZ, "pacotes", "_pdf")
    os.makedirs(saida, exist_ok=True)
    pdf = os.path.join(saida, nome + ".pdf")
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        pg = nav.new_page()
        pg.set_content(html, wait_until="networkidle")
        pg.pdf(path=pdf, format="A4", print_background=True, display_header_footer=True,
               header_template="<span></span>",
               footer_template='<div style="font-size:7pt;color:#94A3B8;width:100%;padding:0 16mm;display:flex;justify-content:space-between">'
                               f'<span>{titulo}</span><span><span class="pageNumber"></span>/<span class="totalPages"></span></span></div>',
               margin={"top": "18mm", "bottom": "18mm", "left": "16mm", "right": "16mm"})
        nav.close()
    print(f"PDF gerado: {pdf}")
    if "--local" in sys.argv:
        return 0
    with open(pdf, "rb") as f:
        req = urllib.request.Request(f"{URL}/storage/v1/object/materiais/pacotes/{urllib.parse.quote(nome)}.pdf",
                                     data=f.read(), method="POST",
                                     headers={"apikey": KEY, "Content-Type": "application/pdf", "x-upsert": "true"})
    urllib.request.urlopen(req, timeout=60).read()
    print(f"Enviado para materiais/pacotes/{nome}.pdf")
    return 0


if __name__ == "__main__":
    sys.exit(main())
