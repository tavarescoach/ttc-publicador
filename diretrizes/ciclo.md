# Ciclo temático de 3 dias (especificação aprovada em 24/10/2026)

Vale para toda sessão que mexa em pacote, feed, stories ou revisão. Estado da implementação no fim do arquivo.

## Decisões do Luan (24/10/2026)
- Um tema por ciclo de 3 dias, escolhido por fórmula fixa (abaixo), sem IA.
- FAM sai do sorteio: o estático das 7h é sempre sobre uma pessoa conhecida, ligada ao tema do ciclo. Concorrem 8 temas: FOR, EMA, EST, ESP (centrais) e GLP, LON, MEN, WEA (cruzados).
- 20h: carrossel no dia 2 do ciclo; foto pessoal nos dias 1 e 3.
- Stories automáticos novos (6h, 8h, 10h, 12h30) substituem os automáticos antigos. Stories com sticker (enquete, caixinha, quiz) viram opcionais na Tela Hoje: nada trava se o Luan não postar.
- Reels suspensos (sem editor de vídeo).
- Publicação sem aprovação prévia: o que passa na revisão entra agendado; o Luan só veta. Isso inclui temas de saúde (GLP-1, hormônio, suplemento, lesão, saúde mental), com a revisão de saúde mais rígida (abaixo).
- Foto de terceiros só com licença que permite uso comercial (Wikimedia Commons CC BY, CC BY-SA ou domínio público). Sem foto liberada, a arte sai tipográfica.
- Dados de saúde: só afirmações defensáveis, baseadas em evidência, com fonte.

## 1. Escolha do tema
- Quando: no último dia de cada ciclo, às 14h50 (depois da curadoria das 14h17). O post das 7h seguinte fica pronto com mais de 3 h de folga.
- Onde: `ciclo/escolher.py`, num robô do GitHub. Conta fixa, sem IA.
- A curadoria do Radar grava em cada item também `tema_editorial` (uma das 9 siglas) e `pessoa` (nome da pessoa conhecida no centro do fato, ou null).

Pontuação de cada tema:
1. Entram as notícias das últimas 72 h com nota >= 50 e `tema_editorial` igual ao tema.
2. Agrupar por `cluster`. Cada assunto vale a sua melhor notícia: nota/100 × peso da fonte (`radar/fontes.json`, 0,5 a 1,1; sem peso = 1,0) × recência (até 24 h = 1,0; 24–48 h = 0,6; 48–72 h = 0,3).
3. × (1 + 0,25 por canal extra no mesmo assunto), teto 2×. Assunto em alta (3+ canais): × 1,5.
4. Pontuação do tema = soma dos assuntos. Data de `radar/calendario.json` dentro do ciclo ligada ao tema: +30%.

Escolha, nesta ordem:
1. Temas dos 2 ciclos anteriores ficam de fora.
2. Se os 2 ciclos anteriores foram cruzados, só os centrais concorrem.
3. Maior pontuação vence. Empate: o tema usado há mais tempo. Tudo zero: o central usado há mais tempo.

## 2. Dados
`ciclos/ciclos.json` (fonte da verdade; o robô Sincronizar painel leva ao painel). Lista, mais novo por último:
```json
{"id": "c-2026-10-26", "inicio": "2026-10-26", "fim": "2026-10-28", "tema": "Longevidade", "sigla": "LON",
 "pontuacao": {"LON": 4.82, "FOR": 3.10}, "excluidos": ["EST", "FOR"], "motivo": "3 assuntos em alta",
 "noticias_base": ["id1"], "famosos": [{"nome": "...", "noticia_id": "...", "data": "..."}],
 "status": "escolhido | pacote_pronto | erro"}
```
`ciclos/rotacao.json`: trechos de time-lapse e fotos já usados, com data.

## 3. Grade diária
| Hora | Formato | Aponta para | Saída |
|---|---|---|---|
| 06:00 | Story: time-lapse de trabalho + frase de bom dia | respostas | auto |
| 07:00 | Estático: notícia de pessoa conhecida ligada ao tema, anuncia o carrossel das 12h | — | auto |
| 08:00 | Story: arte do post das 7h + "post novo no perfil" | post das 7h | auto (compartilhar pelo app é opcional) |
| 10:00 | Story: time-lapse de treino + CTA MÉTODO | direct | auto |
| 12:00 | Carrossel Decodificado (diretrizes/carrossel.md) | — | auto |
| 12:30 | Story: capa do carrossel + "deslize no perfil" | carrossel | auto |
| 20:00 | Dia 2: carrossel · dias 1 e 3: foto pessoal | — | auto |

Robô de publicação roda aos :07 e :37: o story das 6h sai às 6h07.

Estático das 7h:
- Notícia: radar das últimas 24 h; senão 72 h; senão 7 dias. A sessão confirma o fato numa segunda fonte.
- Foto: só Wikimedia Commons com licença comercial. Sem foto, arte tipográfica.
- Na arte: "Foto: autor / Wikimedia Commons (licença)" e "Fonte: veículo, data". Só o que a notícia afirma sobre a pessoa; nunca sugerir que ela usa ou recomenda o método.

Foto pessoal: nenhuma repete até as 300 terem saído. Publicada sem edição (só redimensionada). A sessão do pacote abre a foto e escreve legenda curta ligada ao tema, MÉTODO só no fim.

## 4. Acervo (Google Drive)
- Pasta "TTC Acervo": https://drive.google.com/drive/folders/1rIv77LwguHTyfA4CX_KrAqgbx2iT7I8U (pública para leitura por link, decisão do Luan).
- Subpastas: `fotos`, `timelapse-trabalho` (manhã no computador), `timelapse-treino`.
- O Luan sobe os originais quando quiser. O robô "Preparar acervo" baixa na véspera do ciclo só o que vai usar, trata e envia ao bucket `midia` (pasta do dia). O Supabase guarda só o que é publicado.

Rotação dos time-lapses:
- Trechos de 12 s (início avança de 12 em 12 s). Escolha: o trecho usado há mais tempo.
- Nunca o mesmo vídeo em dias seguidos no mesmo horário; nunca o mesmo trecho em 30 dias nem dentro do ciclo.
- O robô corta, grava a frase na tela (identidade LT, área segura), comprime abaixo de 50 MB e envia.

## 5. Revisão automática
- Stories passam por `render/revisar.py` com as mesmas barras dos carrosséis, mais: tela com mais de 15 palavras; story sem post ou CTA de destino.
- Estático do famoso barra sem fonte, sem crédito ou com licença fora de cc-by | cc-by-sa | dominio-publico.
- Saúde publica sozinha, mas barra: número sem fonte; verbo de prescrição ("tome", "use", dose, "substitua", "pare o remédio"); promessa de cura ou de prazo; nome de remédio sem fonte.
- Barrou: card em "Precisa de você" com o motivo.

## 6. Pacote do ciclo
Tarefa agendada única (substitui o pacote de sábado), todo dia às 15h07. Se não é véspera de ciclo em `ciclos/ciclos.json`, encerra. Na véspera, escreve os 3 dias de uma vez: 3 estáticos, 4 carrosséis, 2 legendas de foto, textos dos stories, `render/fontes/` de cada peça. Tudo com `tema`.

## Implementação
- [x] Etapa 1: especificação (este arquivo).
- [ ] Etapa 2: stories (rotação, telas, revisão estendida, publicação).
- [ ] Etapa 3: escolha do tema, pacote do ciclo, estático com fonte, carrosséis.
- [ ] Atualizar PIPELINE.md, temas.md e stories.md ao fim de cada etapa.
