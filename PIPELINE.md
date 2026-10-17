# Pipeline do Estúdio (sessão em segundo plano)

Esta sessão é disparada pelo Estúdio de criação do Luan (página do claude.ai) através da tarefa agendada
"Pipeline do Estúdio". A mensagem extra da disparada diz o que fazer, num destes formatos:

    ESTUDIO pesquisa <doc_id>
    ESTUDIO gerar <doc_id>

Ninguém está olhando: não faça perguntas. Decida pela leitura mais razoável e registre no documento.
Responda e escreva sempre em português do Brasil.

## Recursos
- Repositório: tavarescoach/ttc-publicador (este). Clone, leia `diretrizes/marca.md` e `diretrizes/carrossel.md`.
- Estúdio (artifact): https://claude.ai/artifact/4qy326S1jHcMxz8Ycw4QbH — banco do artifact, coleção `criacoes`.
  Ler/escrever com a ferramenta ArtifactData (carregar via ToolSearch "select:ArtifactData"). Toda escrita leva `if_version`.
- Painel: https://ttc-painel.vercel.app (Supabase). Esta sessão NÃO alcança o Supabase direto: tudo passa pelos robôs do GitHub.
- Robô "Renderizar artes": cada push em `render/pedidos/*.json` gera os PNGs, sobe para o bucket e cria o card
  "Pronto para aprovar" no painel; guarda a prévia em `render/previas/<id>.jpg`.

## Documento da criação (coleção `criacoes`)
Campos: status (pesquisando | opcoes | rascunho | gerando | pronto | erro), vez (claude | luan), origem (pesquisa | material | ideias),
foco, entrada_resumo, opcoes [5 × {titulo, subtitulo, frases[2], tese, headlines[4 × {titulo, subtitulo}]}],
escolha {titulo, subtitulo, ...}, tese, headline {titulo, subtitulo}, formatos [carrossel | reels | broll | estatico | stories],
quando (ISO com -03:00, horário desejado), resultado {formato: id do card}, erro, atualizado_em.

## ESTUDIO pesquisa <doc_id>
1. `ArtifactData get` (collection `criacoes`, doc_id). Guarde `version`. Se status não for "pesquisando", pare.
2. Pesquise notícias, estudos recentes, trends e termos em alta ligados ao `foco` (ou ao nicho, se vazio). Confira as fontes.
3. Monte 5 opções DIFERENTES entre si (autoridade/ciência, mito x método, objeção, público feminino, prova/bastidor), cada uma com:
   - titulo (até 8 palavras), subtitulo (1 frase), frases (2 frases curtas de COMO explorar e ligar aos conteúdos e à venda — não frases de efeito);
   - tese: seções `## A tese`, `## O que a ciência mostra` (com fontes), `## Por que isso importa para o seu público` (executivo 30–45 e mulher 30–50),
     `## O custo escondido da crença errada`, `## Como o método aplica`, `## Objeções que esse tema responde`, `## Desdobramentos de conteúdo`,
     `## Cuidado de comunicação`. Use "- " em listas e **negrito**. Nada genérico.
   - headlines: 4 investigativas e culturais, com potencial viral (curiosidade, conexão). titulo = frase 1, subtitulo = frase 2.
4. `ArtifactData update` com {opcoes, status:"opcoes", vez:"luan", atualizado_em} e o `if_version`.

## ESTUDIO gerar <doc_id>
1. `ArtifactData get`. Se status não for "gerando", pare. Leia escolha, tese, headline, formatos, quando.
2. Para `carrossel`: escreva `render/pedidos/e-<doc_id>-carrossel.json` seguindo `diretrizes/carrossel.md`
   (id "e-<doc_id>-carrossel", data = dia de `quando`, quando, funil, pauta = headline.titulo, legenda, 9–10 slides).
   A capa usa a headline confirmada pelo Luan (título); destaque 1–3 palavras com **...**.
   Fatos e números: só os que estão na tese ou que você confirmar com pesquisa. Fotos conforme a seção Fotos.
3. `git pull --rebase`, commit e push. Espere o robô "Renderizar artes" terminar (`gh api .../actions/workflows/renderizar-artes.yml/runs`).
4. `git pull` e abra `render/previas/e-<doc_id>-carrossel.jpg` com Read. Confira: texto cortado, foto ruim, destaque errado.
   Se houver problema claro, corrija o JSON e faça push de novo (no máximo 1 correção).
5. Formatos ainda não automatizados (reels, broll, estatico, stories): acrescente em `pautas.json` (lista JSON; crie se não existir)
   `{id:"e-<doc_id>-<formato>", pauta: headline.titulo, legenda: headline.subtitulo, tipo (reels/broll→REELS, estatico→IMAGEM, stories→STORY), etapa:"pauta", data}`
   e faça push (o robô "Sincronizar painel" coloca na coluna da esquerda).
6. `ArtifactData update`: {status:"pronto", vez:"luan", resultado:{carrossel:"e-<doc_id>-carrossel", ...}, atualizado_em}.
   O Luan aprova no painel (Pronto para aprovar → Aprovar e agendar); o robô de publicação importa o aprovado.

## Se algo falhar
`ArtifactData update` com {status:"erro", vez:"luan", erro:"<o que aconteceu, em 1 frase>"}. Não deixe o documento em "gerando"/"pesquisando".

## Commits
Mensagens curtas em português. Sempre `git pull --rebase` antes do push (outros robôs commitam na mesma branch).
