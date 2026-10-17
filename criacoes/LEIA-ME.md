# Criações (botão Criar do painel)

- `pendentes.json` — gerado pelo robô "Exportar criações": o que está na vez do Claude.
- `materiais/` — PDFs e arquivos enviados pelo painel.
- `respostas/<id>.json` — o que o Claude devolve. O robô "Sincronizar painel" aplica no Supabase
  (só se a criação ainda estiver na vez do Claude).

Formato das respostas:
- etapa `entrada` -> `{"id", "etapa": "opcoes", "opcoes": [{"titulo","subtitulo","frases":[f1,f2]} x5]}`
- etapa `tese`    -> `{"id", "etapa": "headlines", "tese": "texto (## títulos e - listas)", "headlines": [{"titulo","subtitulo"} x4]}`
- etapa `formatos` -> Fase C (criação dos formatos).
