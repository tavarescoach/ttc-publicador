# Radar — curadoria (sessão em segundo plano)

Roda 2x por dia (~6h17 e ~14h17, Brasília), 30 min depois da coleta. Ninguém está olhando: não pergunte nada.

## Entrada
- `radar/coleta.json` — notícias pré-selecionadas (id, canal, titulo, link, imagem, publicado_em, resumo).
  O `resumo` é só para você entender o assunto: nunca copie esse texto para o pitch.
- `radar/preferencias.json` — o que o Luan salvou, descartou ou transformou em pauta. Temas parecidos com os descartados
  perdem pontos; parecidos com salvos/virou_pauta ganham.
- `diretrizes/marca.md` — marca, tom, público, oferta.

## Para cada notícia
- `nota` 0–100: encaixe com o público (executivo 30–45 e mulher 30–50 da Zona Sul do Rio), potencial de conteúdo que gere valor
  real e ponte para a venda, credibilidade da fonte, atualidade. Fofoca, política, crime e assuntos sem ponte com corpo/saúde/
  performance/rotina: abaixo de 30. Estudo novo sobre treino de força, sono, obesidade/GLP-1, longevidade, saúde do homem 35+,
  menopausa: tende a 70+.
- `tema`: saude | ciencia | tecnologia | esporte | cultura | comportamento | negocio
- `publico`: "executivo 30–45" | "mulher 30–50" | "ambos"
- `motivo`: 1 frase dizendo por que serve (ou não serve) ao público.
- `pitch` (só quando nota ≥ 50; senão null), com palavras SUAS:
  {"angulo": "o ângulo da marca (método acima de motivação, anti-caos)",
   "formato": "carrossel decodificado | reels mito x método | reels erro comum | bastidor | story/enquete | estático",
   "gancho": "frase de abertura pronta, até ~12 palavras, no tom da marca",
   "ponte": "como liga ao personal / Avaliação Estratégica"}
- `cluster`: um slug curto do ASSUNTO (ex.: "glp1-perda-muscular"). Notícias de canais diferentes sobre a mesma história recebem o
  mesmo cluster. `em_alta`: true quando o cluster aparece em 3 ou mais canais diferentes.
- Na dúvida sobre um fato, use WebFetch no link (no máximo ~5 por rodada, nas notas mais altas).

## Saída
1. Escreva `radar/curadoria/AAAA-MM-DD-HH.json` (horário de Brasília): {"gerado_em": "...", "itens": [ {id, canal, titulo, link,
   imagem, publicado_em, tema, nota, motivo, publico, pitch, cluster, em_alta}, ... ]} com TODAS as notícias da coleta.
2. Apague arquivos de curadoria com mais de 3 dias.
3. `git pull --rebase`, commit ("radar: curadoria AAAA-MM-DD HH h") e push. O robô "Radar de notícias" aplica no painel.
