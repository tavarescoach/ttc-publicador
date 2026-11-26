# Stories do @tavarescoach — como planejar e entregar

> **Vale primeiro (26/11/2026): Linha Editorial v3 + refinamentos do Luan.** Onde conflitar com o resto deste arquivo, vale este bloco. Doc completo: "Linha Editorial v3 — Evolução sem acaso" (claude.ai/artifact/Y4ksMStNr3BQmAgomNtTDQ). Templates no Canva: "Templates Stories v3 — Abertura, Virada, Ponto A→B, Post novo, Convite (26/11)".
>
> - **Arco diário, 100% robô (sem enquete, caixinha nem sticker):** 07:30 Abertura · 10:00 Virada (a decisão + artigo) · 12:05 Post novo · 13:00 Ponto A→B (resultado esperado + critério que dá para medir) · 21:00 Convite.
> - **Abertura (tela 1):** só o título com a ideia central do dia, até 12 palavras. Sem "Hoje:" e sem rótulo de dia. Ex.: "O joelho parou de doer. Já pode voltar?"
> - **Virada (tela 2):** até 30 palavras + linha de fonte (autor, ano, revista). Só publica com artigo verificado (DOI ou PubMed); sem artigo, aplicação prática sem número.
> - **Ponto A→B (tela 3):** um resultado esperado + um critério mensurável (teste, carga, tempo, dor de 0 a 10). Sem promessa de prazo que o artigo não sustente.
> - **Convite (21:00):** "Responde este story com [PALAVRA DO TEMA] e me conta…". A palavra-chave muda todo dia e é ligada ao conteúdo (ex.: JOELHO ou LCA no dia do joelho), nunca uma palavra fixa. Registre a palavra e a data no painel para medir a origem.
> - **Mídia (estética aprovada em 26/11, a dos templates do Canva):** foto de academia escura em tom azul-marinho em todas as telas. Fontes: `render/assets/fundos` (as fotos do template, já no tom; o robô também usa cada uma espelhada), pasta `banco` do Drive (fotos de banco de academia que o Luan quiser somar) e fotos do acervo etiquetadas com contexto treino/ttc. O robô aplica o mesmo tom (preto e branco + azul-marinho) a toda foto que não vem do template. Viagem, praia, casa ou foto sem etiqueta nunca entra. Time-lapse continua possível pelo plano (`fotos`) ou pela config (`video:<slot>`), com o mesmo tom. A foto de banco nunca é apresentada como o Luan, o TTC ou um aluno.
> - **Robô (desde 26/11):** `acervo/stories.py` com `"modelo": "v3"` em `acervo/config.json` monta as 5 telas sozinho às 18h do dia anterior, a partir do **plano do dia** `ciclos/stories/<AAAA-MM-DD>.json`. Sem plano, sai só o Post novo (se houver carrossel às 12h). Fundo: time-lapse do acervo; foto só de academia (ver Mídia), sem repetir em 14 dias (mesma rotação do feed). A palavra do convite é registrada em `metricas/palavras.json` e no card do painel.
> - **Plano do dia** (quem escreve: a sessão que monta o conteúdo do dia; valide com `python -c "import json;json.load(open(...))"`):
>   `{"data": "2026-12-01", "serie": "Apaga-incêndio", "tema": "LON", "palavra": "JOELHO",`
>   ` "abertura": {"titulo": "O joelho parou de doer. **Já pode voltar?**"},`
>   ` "virada": {"titulo": "...até 30 palavras, um destaque em **...**", "fonte": "Grindem et al., 2016, Br J Sports Med", "link": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4912389/"},`
>   ` "resultado": {"titulo": "...", "criterio": "Critério: força e salto em 90% do outro lado.", "fonte": "...", "link": "..."},`
>   ` "convite": {"titulo": "opcional; padrão: Responde este story com **<palavra>** e me conta em que fase você está."},`
>   ` "fotos": {"virada": "opcional: URL ou drive_id de uma foto específica"}}`
>   `link` precisa ser DOI ou PubMed/PMC aberto e conferido. Sem artigo verificado, a virada não leva número. Teste local: `python acervo/stories.py <data> --ensaio` (prévias em `render/previas/stories/<data>/`).
> - **Visual (o dos templates do Canva):** texto direto sobre a foto, sem caixa, alinhado à esquerda na metade de baixo; barra vermelha, rótulo cinza #94A3B8, título branco #F8FAFC (96 px; 76 px quando longo), destaque vermelho #C1121F, linha de fonte em cinza; logo LT em cima; rodapé "@tavarescoach · Evolução sem acaso.". Post novo: texto em cima, capa do carrossel em cartão embaixo. Nada importante nos 250 px do topo nem nos 340 px da base.

> Em transição para o ciclo temático (diretrizes/ciclo.md): quando `acervo/config.json` tiver "ativo": true, os stories automáticos são os do robô "Preparar stories" (6h, 8h, 10h, 12h30) e os stories com sticker deste arquivo viram opcionais. Até lá, vale o que está abaixo.

Regra de operação dos stories. Vale para o pacote semanal e para qualquer sessão que monte stories. Estratégia completa: doc `claude/stories-estrategia.md` do Project. Texto: skill `copy-social-ttc` (seção 9 e vícios de IA).

## 1. Princípios
- **Os stories distribuem o feed.** Todo story pertence a uma pauta que sai no dia, saiu ontem ou sai amanhã.
- **A fonte da verdade é a fila real**, não o plano: `fila.json` (status `pendente`, horário em `quando`) + `render/pedidos/<id>-carrossel.json` (capa, slides, legenda). Leia o que de fato vai ao ar em cada dia antes de escrever.
- **Loop aberto:** o story faz a pergunta; a resposta está no post ou no story seguinte.
- **Um objetivo por dia, pelo funil do post principal:** topo = levar ao post (toques na ponte) · meio = respostas (votos, caixinha) · fundo = MÉTODO no direct.
- **Honestidade:** nunca inventar aluno, número ou resultado de enquete. O resultado da enquete é sempre escrito pelo Luan, com o número real.

## 2. Arco do dia
Dia com post (6 stories nas semanas 1–2 da rampa):
1. **Abertura** (manhã, MANUAL): vídeo curto de bastidor + a Cena da pauta em uma frase.
2. **Ponte** (5–10 min depois de cada post do dia, MANUAL): post compartilhado pelo app (avião de papel → Adicionar ao story) + texto curto que abre o loop. Só a ponte nativa leva ao post; imagem publicada pelo robô não é clicável.
3. **Interação** (antes do post principal, MANUAL): enquete, quiz ou caixinha sobre a cena da pauta, sobre arte de fundo.
4. **Aprofundamento** (tarde, MANUAL): arte de fundo com a Causa (frase-assinatura) + o número real da enquete, que o Luan escreve no espaço vazio.
5. **Conversão** (noite, AUTO): convite MÉTODO ligado ao tema, ou caixinha que puxa conversa.

Dia sem post: metade **eco** da pauta anterior (respostas da caixinha, aplicação prática, objeção) e metade **prelúdio** da próxima (a cena, a pergunta, "amanhã eu mostro"). Não invente pauta: o prelúdio usa o próximo post da fila.

Rampa: 6/dia (até 01/11) · 9/dia (02–15/11: + bastidor de tarde, aplicação prática, objeção) · 12/dia (a partir de 16/11: + quiz, prova com autorização, resposta da caixinha anterior).

Tema de saúde (hormônio, suplemento, remédio/GLP-1, lesão, gravidez, menopausa): o dia todo é MANUAL (sem story automático), e as artes levam "Informação geral. Seu médico define o tratamento." quando citam tratamento.

Não repetir enquete, gancho ou texto de convite dos últimos 7 dias.

## 3. Texto
- Até 15 palavras por tela, uma ideia, leitura em 3 s.
- Fórmula Cena → Causa → Movimento. A enquete usa a Cena; o aprofundamento entrega a Causa. Proibido "não é X, é Y", travessão, pergunta respondida pelo próprio texto e os demais vícios da skill.
- Pergunta de sticker é pergunta de verdade.

## 4. Entrega (arquivos)
**Artes** — `render/stories/<AAAA-MM-DD>.json`, lista de telas:
```json
[{"arquivo": "midia/2026-10-26/story-fundo-enquete.png", "rotulo": "Pergunta do dia",
  "titulo": "texto com **destaque** em vermelho", "texto": "linha de apoio (opcional)", "topo": 620}]
```
- Nomes: `story-fundo-enquete.png`, `story-fundo-resultado.png`, `story-fundo-caixinha.png` (fundos para o Luan usar no app) e `story-1.png`, `story-2.png`… (automáticos, publicados pelo robô).
- `topo` (px): ~620 em fundo de sticker (espaço livre embaixo para o sticker), ~1000 em fundo de resultado (espaço livre em cima para o número), ~660 nos automáticos.
- O robô **Renderizar stories** gera os PNGs no push e sobe para o bucket. Para conferir antes, `python render/story.py render/stories/<data>.json` gera localmente; abra os PNGs com Read.

**Automáticos** — um item por `story-N.png` no `fila.json` (indentação de 2 espaços):
`{"id": "<data>-story-N", "quando": "<data>T<HH:MM>:00-03:00", "tipo": "STORY", "arquivos": ["<data>/story-N.png"], "legenda": "", "status": "pendente"}`.
Antes, confira que não há STORY pendente da mesma data com o mesmo id; nunca altere item `publicado`.

**Manuais** — itens em `tarefas.json` (indentação de 1 espaço), um por story manual:
`{"id": "<data>-sN", "data": "<data>", "ordem": 10+N, "formato": "stories", "titulo": "Story HH:MM · bloco: assunto", "detalhe": "...", "acao": "manual", "horario": "HH:MM"}`.
O `detalhe` traz sempre: objetivo do dia (no primeiro), O QUE FILMAR ou COMO FAZER no app, o TEXTO NA TELA exato, as opções do sticker e o link da arte de fundo:
`https://txiszakrpssubgvzpdcx.supabase.co/storage/v1/object/public/midia/<data>/<arquivo>`.
Automáticos também entram como tarefa, com "(automático, não precisa postar)" no título, para o Luan saber o que sai.

**Corrigir uma tarefa já enviada:** o painel só insere ids novos. Marque a antiga com `"apagada": true` (o robô Sincronizar painel a esconde) e crie outra com id novo.

**Google Agenda** — um evento por dia (não um por story), 15 min antes do primeiro story, 10 min, disponibilidade livre, lembrete popup na hora. Título "Stories do dia · <tema>". Descrição: objetivo do dia, a lista "HH:MM bloco: texto curto" e o link https://ttc-painel.vercel.app/hoje.html. Antes de criar, procure eventos "Stories do dia" na mesma data para não duplicar.
