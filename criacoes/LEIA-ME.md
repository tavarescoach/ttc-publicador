# Criações (botão Criar do painel)

- `pendentes.json` — gerado pelo robô "Exportar criações": o que está na vez do Claude.
- `materiais/` — PDFs e arquivos enviados pelo painel.
- `respostas/<id>.json` — o que o Claude devolve. O robô "Sincronizar painel" aplica no Supabase
  (só se a criação ainda estiver na vez do Claude).

Formato das respostas:
- etapa `entrada` -> `{"id", "etapa": "opcoes", "opcoes": [{"titulo","subtitulo","frases":[f1,f2],"tese":"...","headlines":[{"titulo","subtitulo"} x4]} x5]}`
  (tese e headlines de cada opção vêm prontas: ao escolher 1–5, o painel pula direto para as headlines; só a opção 6, escrita pelo Luan, volta para a etapa `tese`)
- etapa `tese`    -> `{"id", "etapa": "headlines", "tese": "texto (## títulos e - listas)", "headlines": [{"titulo","subtitulo"} x4]}`
- etapa `formatos` -> Fase C (criação dos formatos).
