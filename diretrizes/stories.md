# Stories do @tavarescoach: Diário do Ponto A ao B (v3, 26/11/2026)

> Substitui o arco manual de 18/10 e os stories de time-lapse com "bom dia" do ciclo (ciclo.md, seção 3). Linha editorial: `diretrizes/linha-editorial-v3.md`. Papéis da narrativa: `diretrizes/protagonista.md`. Texto: skill `copy-social-ttc`.
> Estado: regras de texto valem já para quem escreve stories. A troca da grade de stories no robô "Preparar stories" (`acervo/stories.py`, `acervo/config.json`) está pendente (linha-editorial-v3.md, seção 9); até lá, os horários antigos seguem, com o texto desta versão.

## 1. Princípios
- **100% robô.** O robô escolhe a mídia do acervo, escreve o texto por cima, revisa e publica. O Luan não grava nem posta nada; só veta.
- **Um dia = uma decisão**, da série do dia (linha-editorial-v3.md, seção 4), contada em 3 telas: a pergunta, a decisão com evidência e o resultado esperado com critério de avaliação.
- **Narrativa do Formato Protagonista:** tela 1 personagem e vilão; tela 2 o guia com a causa e o artigo; tela 3 o sucesso e como medir.
- **Honestidade:** nunca inventar aluno, número ou resultado. Personagem é situação típica ("quando o aluno chega dizendo…") ou fato com fonte.
- **Limite da API:** o robô não publica enquete, caixinha, quiz, sticker de link nem o post compartilhado clicável. A interação vem pela resposta ao story (cai no direct) e o aviso de post novo leva ao perfil.

## 2. Arco diário (3 telas da narrativa + 2 de apoio)
| Hora | Tela | Cena da mídia (`cena` no acervo) | Texto na tela | Limite |
|---|---|---|---|---|
| 07:30 | 1 · A pergunta do dia | `trabalhando` ou `treinando` (time-lapse) | A decisão do dia em 1 frase, começando por "Hoje:" | até 20 palavras |
| 10:00 | 2 · A decisão | `corrigindo-aluno` ou `demonstrando` | O que o Luan faz, com aplicação prática, + linha de fonte "Fonte: Autor et al., ano, revista" | até 30 palavras + fonte |
| 12:05 | Apoio · Post novo | imagem do carrossel do dia | "Post novo no perfil: o passo a passo completo." | até 12 palavras |
| 13:00 | 3 · Resultado e critério | `treinando` | Um resultado esperado + um critério que dá para medir (teste, carga, tempo, dor de 0 a 10) | até 30 palavras |
| 21:00 | Apoio · Convite | `olhando-para-camera` | "Responde este story com PONTO A e me conta sua meta." (variações aprovadas em `acervo/config.json`) | até 15 palavras |

Domingo (`um-por-cento`): as 3 decisões da semana com mais respostas, uma por tela, nos mesmos horários das telas 1–3. Sábado (`treino-do-luan`): as 3 telas contam uma decisão do treino do Luan na modalidade do dia, com mídia de treino dele.

Rampa: 5 telas/dia. Só sobe quando a queda de alcance da tela 1 para a 3 ficar abaixo de 20% por 2 semanas.

### Exemplo completo (`apaga-incendio`, quarta)
1. "Hoje: o que eu faço quando o aluno chega dizendo que o joelho parou de doer."
2. "Operou o LCA? Parar de doer não libera a volta. Eu testo força do quadríceps e salto, e só libero com a perna operada a 90% da outra." Fonte: Grindem et al., 2016, Br J Sports Med.
3. "No estudo, quem passou nos critérios teve 5,6% de nova lesão. Quem falhou, 38,2%. Critério: força e salto em 90% do outro lado."
Fonte verificada: https://pmc.ncbi.nlm.nih.gov/articles/PMC4912389 (doi 10.1136/bjsports-2016-096031).

## 3. Regras das 3 telas
- Tela 1: sempre uma situação de aluno ou do leitor ligada à série; nunca um aluno específico sem `autorizado`.
- Tela 2: só publica com artigo **verificado**: DOI ou PubMed/PMC aberto pela sessão e gravado no item (`fonte_url`, `fonte_doi`). Sem artigo verificado, a tela vira aplicação prática sem número e sem linha de fonte.
- Tela 3: o número vem do mesmo artigo da tela 2 e fica igual a ele. Nada de prazo que o artigo não sustente.
- Saúde (hormônio, suplemento, remédio/GLP-1, lesão, gravidez, menopausa): revisão de saúde mais rígida (ciclo.md, seção 5); quando citar tratamento, linha "Informação geral. Seu médico define o tratamento."
- Texto: Cena → Causa → Movimento; proibidos "não é X, é Y", travessão, pergunta respondida pelo próprio texto e os demais vícios da skill. Não repetir gancho ou convite dos últimos 7 dias.

## 4. Escolha da mídia (acervo)
- `acervo/tags.json` ganha, por mídia: `serie` (lista de séries em que cabe) e `cena` (`trabalhando`, `corrigindo-aluno`, `demonstrando`, `treinando`, `olhando-para-camera`).
- A tela pede uma cena; o robô sorteia entre as mídias dessa cena e da série, sem repetir a mesma mídia em 14 dias (`ciclos/rotacao.json`). Time-lapse: trechos diferentes a cada uso (regra de rotação de ciclo.md, seção 4).
- Fora: `evitar`, aluno sem `autorizado`, sem camisa (stories não levam foto sem camisa).
- Visual: 1080x1920, azul performance, cinza saúde, vermelho #C1121F só no destaque, Inter, logo LT; nada importante nos 250 px do topo nem nos 340 px da base; leitura em 3 s; caixa de texto acima ou abaixo dos rostos (detecção já existente).

## 5. Entrega (arquivos)
**Artes** — `render/stories/<AAAA-MM-DD>.json`, lista de telas:
```json
[{"arquivo": "midia/2026-12-02/story-1.png", "tela": 1, "serie": "apaga-incendio", "pilar": "MET", "tema": "LON",
  "rotulo": "Hoje", "titulo": "texto com **destaque** em vermelho", "texto": "linha de apoio (opcional)",
  "fonte": "Grindem et al., 2016, Br J Sports Med", "fonte_url": "https://...", "midia_acervo": "<id no tags.json>", "topo": 660}]
```
- O robô **Renderizar stories** gera os PNGs no push e sobe para o bucket. Conferência local: `python render/story.py render/stories/<data>.json` e abrir os PNGs com Read.

**Fila** — um item por tela no `fila.json` (indentação de 2 espaços):
`{"id": "<data>-story-N", "quando": "<data>T<HH:MM>:00-03:00", "tipo": "STORY", "arquivos": ["<data>/story-N.png"], "legenda": "", "status": "pendente"}`.
Antes, conferir que não há STORY pendente da mesma data com o mesmo id; nunca alterar item `publicado`.

**Painel** — cada tela entra em `tarefas.json` como "(automático, não precisa postar)", para o Luan poder vetar. Corrigir tarefa já enviada: marcar a antiga com `"apagada": true` e criar outra com id novo.

**Google Agenda** — desligada na v3 (não há ação do Luan nos stories).

## 6. Métricas
O robô coleta, por tela, antes de 24 h: alcance, respostas, saídas e avanços. Por dia: queda de alcance da tela 1 para a 3 e respostas PONTO A. Metas das semanas 1–2: queda menor que 20% e 1 resposta PONTO A por dia.
