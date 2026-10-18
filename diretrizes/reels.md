# Direção — Reels enviado pelo Luan (capa + legenda)

O vídeo já vem gravado e editado pelo Luan. O Claude NÃO edita o vídeo: cria a capa e a legenda e agenda para aprovação.
Base do conteúdo: `render/reels/<id>/info.json` (tema, notas do Luan, funil, duração, transcrição do áudio) e os quadros `quadro-1..8.jpg`.

## Capa (1080x1920, render/capa-reels.html)
- Fundo: o melhor quadro do vídeo. Critérios: o Luan ou o aluno visível e nítido, rosto ou movimento claro, sem desfoque, sem legenda queimada do vídeo atrás do título (prefira quadros com a parte de baixo limpa), sem pessoa de olhos fechados ou careta.
  Abra os quadros com Read antes de escolher.
- `rotulo` (opcional): tipo do reels em 2–3 palavras — "Mito x Método", "Erro comum", "Bastidor técnico", "Pergunta de aluno", "Prova".
- `titulo`: o gancho do vídeo em até 7 palavras (máx. ~40 caracteres), em CAIXA ALTA pelo próprio modelo. 1–2 palavras em **destaque** (vermelho).
  Use a Causa ou a Cena da fórmula da marca (skill copy-social-ttc), afirmativa, sem "não é X, é Y". Pode ser a primeira frase dita no vídeo (transcrição), encurtada.
- `subtitulo` (opcional): 1 frase curta que completa o gancho.
- Tudo importante fica na faixa central (o grid do perfil corta em 3:4). O modelo já respeita isso.

## Legenda
- 1ª linha: gancho (diferente do título da capa, mas da mesma ideia).
- 3–5 linhas curtas com o porquê / o ponto principal do vídeo, fiéis ao que ele fala (transcrição) e às notas.
- CTA pelo funil: topo → "Salva para o seu próximo treino." / "Manda para quem precisa ouvir isso."; meio → "Segue para mais critério no seu treino." ou caixinha; fundo → "Me manda MÉTODO no direct."
- 3–5 hashtags de nicho e bairro (#personaltrainerrj #treinodeforca #copacabana #ipanema ...).
- Tom de voz: diretrizes/marca.md e a skill `.claude/skills/copy-social-ttc/SKILL.md` (situação B: a voz do Luan está na transcrição, preserve as palavras dele). Sem promessa com prazo, sem emoji em excesso, sem travessão.
- CTA MÉTODO também na legenda (a revisão automática exige): depois do CTA do funil, uma linha "me manda MÉTODO no direct" quando fizer sentido.
- Se a transcrição vier vazia (vídeo só com música), apoie-se no tema e nas notas e descreva o que os quadros mostram, sem inventar fala.

## Agendamento
- `quando` = o horário sugerido pelo Luan no envio (info.json). O Luan confirma ao aprovar.
