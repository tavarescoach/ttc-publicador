# Pipeline do Estúdio (sessão em segundo plano)

> Ciclo temático de 3 dias (aprovado em 24/10/2026, em implementação): ver `diretrizes/ciclo.md`. Onde ele contradiz regras antigas deste arquivo (aprovação de saúde, pacote de sábado, stories), vale o ciclo.
>
> **Formato Protagonista (aprovado em 26/11/2026):** todo post que parte de notícia segue `diretrizes/protagonista.md`
> e escolhe uma persona de `diretrizes/personas.md` (`rafael`, `thiago` ou `feminina`). A notícia traz o personagem, o
> leitor é o herói, o Luan e o método são o guia. Onde ele contradiz o arco antigo do carrossel (`diretrizes/carrossel.md`
> v2, "executivo 30–45 e mulher 30–50"), vale o Protagonista. Fotos, voz, fontes e revisão da v2 continuam valendo.

Esta sessão é disparada pelo Estúdio de criação do Luan (página do claude.ai) através da tarefa agendada
"Pipeline do Estúdio". A mensagem extra da disparada diz o que fazer, num destes formatos:

    ESTUDIO pesquisa <doc_id>
    ESTUDIO rascunhos <doc_id>
    ESTUDIO gerar <doc_id>
    ESTUDIO reels <id>

Ninguém está olhando: não faça perguntas. Decida pela leitura mais razoável e registre no documento.
Responda e escreva sempre em português do Brasil.

## Recursos
- Repositório: tavarescoach/ttc-publicador (este). Clone, leia `diretrizes/marca.md`, `diretrizes/carrossel.md`, `diretrizes/protagonista.md`, `diretrizes/personas.md` e a skill de texto `.claude/skills/copy-social-ttc/SKILL.md` (todo texto segue ela; a revisão automática barra os vícios de IA da seção 4).
- Estúdio (artifact): https://claude.ai/artifact/4qy326S1jHcMxz8Ycw4QbH — banco do artifact, coleção `criacoes`.
  Ler/escrever com a ferramenta ArtifactData (carregar via ToolSearch "select:ArtifactData"). Toda escrita leva `if_version`.
- Painel: https://ttc-painel.vercel.app (Supabase). Esta sessão NÃO alcança o Supabase direto: tudo passa pelos robôs do GitHub.
- Robô "Renderizar artes": cada push em `render/pedidos/*.json` gera os PNGs, sobe para o bucket e cria o card
  "Pronto para aprovar" no painel; guarda a prévia em `render/previas/<id>.jpg`.

## Contexto do Estúdio (coleção `contexto`)
Coleção `contexto`: `instagram` (desempenho real), `radar` (assuntos em alta) e `aprendizado` (headline escolhida x
resultado). O Estúdio usa esses docs para avaliar as headlines e reavalia na tela as que chegarem sem `formato_ideal`,
`risco` ou notas de `historico`/`atualidade`. No início de toda execução, rode `python3 metricas/estudio_contexto.py`
e grave `instagram` e `radar` com `ArtifactData` (`list` em `contexto` para as versões, depois `batch` de `set` com
`file_path` e `if_version`). O doc `aprendizado` é atualizado pela curadoria do Radar.

## Documento da criação (coleção `criacoes`)
Campos: status (pesquisando | opcoes | rascunhos | gerando | pronto | erro), vez (claude | luan), origem (pesquisa | material | ideias),
foco, entrada_resumo, opcoes [5 × {titulo, subtitulo, frases[2], objetivo, potencial, tese, headlines[4 × {titulo, subtitulo}]}],
reportagem, fontes, recomendada (ver pesquisa),
escolha {titulo, subtitulo, ...}, tese, headline {titulo, subtitulo}, formatos [carrossel | reels | broll | estatico | stories],
quando (ISO com -03:00, horário desejado), resultado {formato: id do card}, erro, atualizado_em.
headlines_tese [4 × {titulo, subtitulo, notas, total, formato_ideal, risco}] e hreco {indice, motivo, ajuste}: as headlines da tese escolhida.
saidas {blogpost | video_aula | ementa | reels_direcao | teleprompter | broll_narracao}: cada uma {status: gerando | pronto | erro, texto, palavras, erro, escrito_em}.
  O Estúdio mostra essas saídas assim que existem; quem escreve é a sessão (ESTUDIO rascunhos).


## ESTUDIO pesquisa <doc_id>
1. `ArtifactData get` (collection `criacoes`, doc_id). Guarde `version`. Se status não for "pesquisando", pare.
2. Pesquise notícias, estudos recentes, trends e termos em alta ligados ao `foco` (ou ao nicho, se vazio). Confira as fontes.
   **Notícia do Radar:** se o `foco` começa com `radar:<id>` (pode vir seguido de ` | direção extra`), procure o item com esse id em
   `radar/curadoria/*.json` (o mais recente) ou em `radar/coleta.json`. Leia a matéria com WebFetch no `link` e confira os fatos em
   outra fonte. As 5 opções partem DESSA notícia, cada uma com um ângulo diferente (ciência/decodificado, mito x método, objeção,
   público feminino, bastidor/prova), e a tese cita a reportagem como ponto de partida, sem copiar trechos dela.
   **Filtro de protagonista** (`diretrizes/protagonista.md`, seção 3): cada opção que parte de notícia leva
   `protagonista` {tipo (espelho | ponte | alerta), persona (rafael | thiago | feminina), desejo, vilao, nivel_consciencia}.
   Se não der para escrever desejo e vilão em uma linha, a opção é de topo (`potencial.venda` "baixo", objetivo de alcance).
3. Monte 5 opções DIFERENTES entre si. Cada opção também traz os campos do contrato da tese-mãe (`diretrizes/tese-mae.md`): `tipo_pauta` (noticia | tese | guia), `emocao` (admiracao | indignacao | reconhecimento | urgencia_perda | pertencimento), `lacuna` (o que a manchete promete e o conteúdo entrega) e `passo_final` (um só, com a razão). Decida esses campos pela skill `acao-emocional-ttc`. Cada opção:  (autoridade/ciência, mito x método, objeção, público feminino, prova/bastidor), cada uma com:
   - titulo (até 8 palavras), subtitulo (1 frase), frases (2 frases curtas de COMO explorar e ligar aos conteúdos e à venda — não frases de efeito);
   - tese: seções `## A tese`, `## O que a ciência mostra` (com fontes), `## Por que isso importa para o seu público` (a persona da opção, com desejo, vilão, problema interno e erro tirados de `diretrizes/personas.md`),
     `## O custo escondido da crença errada`, `## Como o método aplica`, `## Objeções que esse tema responde`, `## Desdobramentos de conteúdo`,
     `## Cuidado de comunicação`. Use "- " em listas e **negrito**. Nada genérico.
   - headlines: 4 investigativas e culturais, com potencial viral (curiosidade, conexão). titulo = frase 1, subtitulo = frase 2.
     Se a reportagem de partida tiver uma pessoa conhecida no centro do fato, pelo menos 2 das 4 headlines nomeiam a pessoa.
     Cada headline leva `notas` {curiosidade, clareza, marca, publico, venda} (0–10 cada, seja exigente e diferencie) e
     `publico_alvo` (executivo | mulher | ambos, valores que o Estúdio já lê) e `persona` (rafael | thiago | feminina;
     rafael e thiago = executivo, feminina = mulher).
     Headline de notícia segue os ganchos por tipo (seção 8 do Protagonista) e termina no leitor. A opção leva `recomendada_h` {indice (1–4), motivo (2 frases), ajuste
     {titulo, subtitulo} ou null}: a headline que melhor equilibra parar o scroll, salvamento e venda, com uma versão
     melhorada se couber. Quesitos: curiosidade (para o scroll), clareza (entende em 2 s), marca (tom LT, sem clickbait),
     publico (desejo, dores e erros da persona escolhida), venda (ponte para Avaliação Estratégica / MÉTODO).
     Quando houver o doc `contexto/instagram`, inclua também `historico` (0–10: semelhança de estrutura, tema e tom com os
     posts de maior valor e taxa do perfil, ignorando os de baixo desempenho) e `referencia` (título exato do post mais
     parecido, ou "" se nenhum).
   - objetivo: o objetivo que a opção mais atende, em 2–4 palavras (ex.: "Alcance e viralização", "Venda: quebra objeção");
   - potencial: {alcance, engajamento, venda}, cada um "alto" | "medio" | "baixo" (alcance = views/viralização; engajamento = salvar,
     comentar, compartilhar; venda = direct com MÉTODO / Avaliação Estratégica). Seja honesto: nem tudo é alto.
   Campos do documento (valem para as 5 opções; o Estúdio mostra no topo da tela "Escolha a pauta"):
   - reportagem: {titulo (original), titulo_pt (tradução fiel), veiculo (com autor se houver), data (DD/MM/AAAA), link} — a matéria
     de partida (do Radar ou a principal da pesquisa). Se não houver uma matéria central, null.
   - fontes: 2 a 5 principais, conferidas, mais forte primeiro: [{tipo: estudo|diretriz|comunicado|reportagem, titulo, autores,
     publicacao (revista/veículo), ano, link}]. Estudo: prefira link do PubMed/PMC ou DOI. Sem link confiável, link "".
   - recomendada: {indice (1–5), motivo (2–3 frases: por que equilibra alcance, engajamento e venda, timing do assunto e o que pegar
     das outras opções para fechar a peça), headline {titulo, subtitulo} (uma das 4 da opção), formato (formato principal sugerido)}.
4. `ArtifactData update` com {opcoes, reportagem, fontes, recomendada, status:"opcoes", vez:"luan", atualizado_em} e o `if_version`.

## ESTUDIO gerar <doc_id>
1. `ArtifactData get`. Se status não for "gerando", pare. Leia escolha, tese, headline, formatos, quando.
2. Para `carrossel`: escreva `render/pedidos/e-<doc_id>-carrossel.json` seguindo `diretrizes/carrossel.md`
   (id "e-<doc_id>-carrossel", data = dia de `quando`, quando, funil, pauta = headline.titulo, legenda, 9–10 slides).
   A capa usa a headline confirmada pelo Luan (título); destaque 1–3 palavras com **...**.
   Pauta que partiu de notícia: preencha antes `protagonista` e a ficha `narrativa` (seção 4 de `diretrizes/protagonista.md`)
   no pedido e siga o arco de 10 slides e a legenda das seções 6 e 7 (slide 9 = guia, `texto_foto` com foto do Luan).
   Antes do push, confira à mão as regras da seção 10 (o revisar.py ainda não as checa).
   Fatos e números: só os que estão na tese ou que você confirmar com pesquisa. Fotos: se a pauta partiu de reportagem com pessoa conhecida no centro do fato, a capa
   segue a seção "Capa de pauta de notícia com pessoa conhecida" de diretrizes/carrossel.md (foto da pessoa, `credito`,
   `licenca`), mesmo que a headline confirmada não cite o nome; nesse caso mantenha a headline do Luan. Nos demais casos,
   seção Fotos.
   Escreva também `render/fontes/e-<doc_id>-carrossel.json` com os links dos estudos e notícias usados (formato em
   diretrizes/carrossel.md, seção Fontes). Se veio do Radar, inclua a matéria do Radar como "noticia".
3. `git pull --rebase`, commit e push. Espere o robô "Renderizar artes" terminar (`gh api .../actions/workflows/renderizar-artes.yml/runs`).
4. `git pull` e abra `render/previas/e-<doc_id>-carrossel.jpg` com Read. Confira: texto cortado, foto ruim, destaque errado.
   Se houver problema claro, corrija o JSON e faça push de novo (no máximo 1 correção).
5. Formatos ainda não automatizados (reels, broll, estatico, stories): acrescente em `pautas.json` (lista JSON; crie se não existir)
   `{id:"e-<doc_id>-<formato>", pauta: headline.titulo, legenda: headline.subtitulo, tipo (reels/broll→REELS, estatico→IMAGEM, stories→STORY), etapa:"pauta", data}`
   e faça push (o robô "Sincronizar painel" coloca na coluna da esquerda).
   Para reels e broll, escreva também o ROTEIRO: acrescente em `tarefas.json` (indentação de 1 espaço, id novo "AAAA-MM-DD-eN")
   um item {data, ordem, formato:"reels", acao:"reels", titulo:"Gravar reels: <headline>", detalhe:<roteiro>} com o roteiro
   em blocos Tempo · IMAGEM · VOZ · TELA, intenção da voz, lista de planos e contagem de palavras, seguindo
   `.claude/skills/copy-social-ttc/references/narracao-broll.md` (seção 12). Ele aparece na tela Hoje e no guia Como gravar.
   Antes do push, rode `python render/revisar_roteiro.py tarefas.json` e corrija todo "problema" do roteiro novo.
6. `ArtifactData update`: {status:"pronto", vez:"luan", resultado:{carrossel:"e-<doc_id>-carrossel", ...}, atualizado_em}.
   Revisão automática (render/revisar.py, roda no robô "Renderizar artes"): se passar, o card entra AGENDADO sozinho e o Luan só veta se quiser;
   se não passar, ou se for prova com aluno ou tema de saúde/hormônio/suplemento, vai para "Precisa de você" com o motivo
   (render/revisoes/<id>.json). Antes do push, rode `python render/revisar.py render/pedidos/<id>.json` e corrija os "problemas".

## ESTUDIO rascunhos <doc_id>
Disparada quando o Luan escolhe a pauta (tese central) no Estúdio. Escreve as saídas em rascunho para ele comparar.
Não publica, não agenda e não mexe em fila.json, pautas.json nem render/pedidos. Carrossel não é gerado aqui.
1. `ArtifactData get`. Se status não for "rascunhos", pare. Leia escolha, tese e headlines_tese.
2. Grave a tese-mãe em `tese-mae/<doc_id>.json` seguindo `diretrizes/tese-mae.md` (aprovacao.status "aguarda_aprovacao"). Preencha
   emocao, lacuna e passo_final com a skill `acao-emocional-ttc`. Se a tese tiver número sem fonte confirmada, marque em pontos_de_cuidado.
3. Para cada chave de `saidas` com status "gerando", escreva o texto e atualize o campo com `ArtifactData update` (use if_version):
   - `blogpost`: título, subtítulo e corpo com seções; tamanho pelo tipo_pauta (seção "Tamanho do blogpost").
   - `video_aula`: pauta para YouTube (capítulos, promessa, prova, método, CTA).
   - `ementa`: pontos de live ou podcast, tempo por bloco e perguntas-gatilho.
   - `reels_direcao`: direção de gravação em 5 partes, com duração pelo funil.
   - `teleprompter`: texto para a boca, derivado de reels_direcao.
   - `broll_narracao`: narração em VOZ/PONTOS com planos de imagem (formato de `.claude/skills/copy-social-ttc/references/narracao-broll.md`).
   Cada saída vira `{status: "pronto", texto, palavras, erro: null, escrito_em}`, ou `{status: "erro", erro: "motivo"}` se não der.
4. Texto segue `copy-social-ttc` e a revisão de vícios de IA. Número só entra com fonte confirmada. Prova com aluno e tema de saúde
   são escritos, mas a tese já fica com aprovacao "aguarda_aprovacao" e o Luan confirma no painel.
5. Grave a pauta para o painel, que lê estes arquivos (aba "Pautas e rascunhos"):
   - `painel/teses/<doc_id>.json`: {"id", "titulo" (escolha.titulo), "subtitulo", "data" (AAAA-MM-DD de hoje), "aprovacao": "aguarda aprovação", "tese" (texto da tese com ## e -), "saidas": {"blogpost" | "video_aula" | "ementa" | "reels_direcao" | "teleprompter" | "broll_narracao": {"status": "pronto" | "erro", "texto", "erro"}}}.
   - `painel/teses/index.json`: lista com {id, titulo, data, aprovacao}, a mais nova primeiro (sem duplicar o id).
   - Também `saidas/<doc_id>/<chave>.md` e a tese-mãe do passo 2.
   `git pull --rebase`, commit e push. O painel é publicado sozinho quando a pasta `painel/` muda.
6. `ArtifactData update`: {status:"rascunhos", vez:"luan", atualizado_em}. Não troque o status para "gerando" nem "pronto" aqui.

## ESTUDIO reels <id>
O Luan enviou um vídeo pelo painel (card `<id>` em "Em criação"). O doc do Estúdio tem o mesmo id (`criacoes/<id>`, origem "reels").
Leia `diretrizes/reels.md`.
1. `ArtifactData get` do doc. Se status não for "gerando", pare.
2. Dispare o robô "Preparar reels": `gh api -X POST repos/tavarescoach/ttc-publicador/actions/workflows/preparar-reels.yml/dispatches -f ref=main -f "inputs[id]=<id>"`.
   Espere terminar (pode levar até ~8 min por causa da transcrição) e faça `git pull`. Se falhar, registre o erro (ex.: vídeo acima de 50 MB, card sem vídeo).
3. Leia `render/reels/<id>/info.json` e abra os quadros com Read. Escolha o quadro, escreva título da capa e legenda.
4. Escreva `render/pedidos/<id>-reels.json`:
   `{"formato":"reels","id":"<id>","data":info.data,"quando":info.quando,"funil":info.funil,"pauta":info.pauta,
     "video":info.video_bucket,"legenda":"...","slides":[{"tipo":"capa_reels","rotulo":"...","titulo":"...","subtitulo":"...","foto":"render/reels/<id>/quadro-N.jpg"}]}`
   O `id` é o mesmo do card, então o card sai de "Em criação" e vai para "Pronto para aprovar" com vídeo, capa e legenda.
5. Push, espere o "Renderizar artes", confira `render/previas/<id>.jpg` (no máximo 1 correção).
6. `ArtifactData update`: {status:"pronto", vez:"luan", resultado:{reels:"<id>"}, atualizado_em}.

## Se algo falhar
`ArtifactData update` com {status:"erro", vez:"luan", erro:"<o que aconteceu, em 1 frase>"}. Não deixe o documento em "gerando"/"pesquisando".

## Commits
Mensagens curtas em português. Sempre `git pull --rebase` antes do push (outros robôs commitam na mesma branch).

## Fluxo de criação ponta a ponta (versão 1, 23/10/2026)

Fluxo que o Luan usa a cada tema. Cada etapa tem um estado em `criacoes` e um efeito visível no painel. Aprovação só pelo painel.

1. **Painel:** vê o que executar e o que está agendado.
2. **Radar:** lê notícias, tendências e vídeos. Clica no tema e em **"Criar a partir desta"** (cria a criação com `foco = radar:<id>`, status `pesquisando`).
3. **Studio, "gerar 5 pautas":** `ESTUDIO pesquisa <doc_id>` gera 5 teses-mãe em `opcoes` (seção "ESTUDIO pesquisa" acima). O Luan escolhe uma.
4. **Tese central:** ao escolher, a sessão grava `tese-mae/<id>.json` com o contrato de `diretrizes/tese-mae.md` (inclui `emocao`, `lacuna`, `passo_final`; a skill `acao-emocional-ttc` decide esses campos) e status `aguarda_aprovacao`.
5. **Saídas em rascunho:** logo após a escolha, a sessão gera **em rascunho** (status `rascunho` no documento, `aprovacao` ainda pendente) as saídas, para o Luan comparar:
   - `blogpost`: título, subtítulo e corpo; tamanho pelo tipo (abaixo);
   - `video_aula`: pauta para YouTube (capítulos, promessa, prova, método, CTA);
   - `ementa`: pontos de live ou podcast, tempo por bloco, perguntas-gatilho;
   - `reels_direcao` e `teleprompter` (teleprompter derivado da direção);
   - `broll_narracao` (formato de `narracao-broll.md`).
   O carrossel **não** é gerado aqui: só a headline entra, na etapa 6.
6. **Carrossel:** quando o Luan escolhe o carrossel, a sessão gera as **opções de headline** (4, cada uma com `notas`, `publico_alvo`, `historico` quando houver `contexto/instagram`). O Luan escolhe a headline e então o carrossel é escrito a partir da tese (`render/pedidos/e-<id>-carrossel.json`) e passa pela revisão automática.
7. **Aprovação:** o Luan aprova a tese central pelo painel (`aprovacao.status = aprovada`). Sem aprovação, nenhuma saída sai do rascunho. Saídas escolhidas viram `pronto`.
8. **Publicação:** carrossel e stories seguem o robô (aprovado → agendado, veto na lixeira). Blogpost, YouTube, ementa e roteiros não passam pelo robô: ficam no painel como materiais, com botão de copiar ou baixar.

### Tamanho do blogpost (por tipo de pauta)
- Notícia ou caso com um dado central: 800 a 1.200 palavras.
- Tese com evidências (dois ou mais estudos): 1.500 a 2.000 palavras.
- Guia, passo a passo ou método: 2.000 a 2.500 palavras.
O tipo vem do campo `tipo_pauta` da tese (`noticia` | `tese` | `guia`). Sem tipo definido, usar 1.200 como padrão.

### Regras que valem em toda etapa
- Diretrizes v2 (`diretrizes/conteudo.md`, 02/11/2026) valem para pautas, teses, textos e artes: pilares conexão,
  autoridade e desejo; famoso brasileiro primeiro; voz informal no gancho e na legenda; capa sempre com rosto; slide
  "o que eu faço" com foto do Luan nos carrosséis.
- Número sem fonte confirmada bloqueia a aprovação da tese (campo `fontes` em cada evidência).
- Prova com aluno e temas de saúde (hormônio, suplemento, remédio, lesão, gravidez, menopausa) exigem aprovação explícita do Luan, em qualquer saída.
- Público da notícia diferente de 30–50 anos deve virar ponte para o público da marca (`pontos_de_cuidado` da tese); no Formato Protagonista, é o tipo **Ponte**.
- Formato Protagonista em toda pauta de notícia: uma persona, um desejo, um vilão; o leitor entra no slide 2 e não sai; sucesso como identidade, nunca número com prazo.
- Nada é publicado fora do robô ou do Luan; nada já publicado é alterado.

## Tema editorial

Cada pauta, carrossel, reels e story leva um campo `tema` com um valor exato da lista em `diretrizes/temas.md`. O painel usa esse campo para o calendário (sigla, equilíbrio e alerta de fora da linha). Sem `tema`, a publicação aparece como fora da lista.

## CICLO pacote (tarefa agendada "Pacote do ciclo", todo dia 15h07)

Escreve o conteúdo dos 3 dias do ciclo temático (diretrizes/ciclo.md). Ninguém está olhando: não pergunte nada.
0. **O robô "Ciclo temático" pode atrasar horas** (o agendador do GitHub rodou o das 14h50 às 16h58 e às 18h53).
   Se `ativo` for true, amanhã for o início do próximo ciclo (`fim` do último ciclo de `ciclos/ciclos.json` + 1 dia;
   sem ciclos, `inicio` do `ciclo/config.json`) e esse ciclo ainda não estiver lá, dispare-o você:
   `gh api -X POST repos/tavarescoach/ttc-publicador/actions/workflows/ciclo.yml/dispatches -f ref=main -f "inputs[simular]=false"`,
   espere terminar (consulte `.../workflows/ciclo.yml/runs?per_page=1` a cada 20 s, até 10 min) e faça `git pull`.
   Se o agendado rodar depois, ele vê que já existe o ciclo e não faz nada.
1. `git pull`. Leia `ciclo/config.json` e `ciclos/ciclos.json`. Pare sem fazer nada ("nada a fazer") se `ativo` for false,
   ou se o último ciclo não estiver com status "escolhido", ou se o `inicio` dele não for amanhã (horário de Brasília).
2. Leia `diretrizes/protagonista.md` e `diretrizes/personas.md` (26/11/2026: valem sobre o arco antigo do carrossel),
   `diretrizes/conteudo.md` (v2, 02/11/2026: vale sobre as demais em fotos, voz e curadoria), `diretrizes/ciclo.md`,
   `marca.md`, `carrossel.md`, `temas.md` e as skills `copy-social-ttc` e `acao-emocional-ttc`. Pilares: 07h conexão,
   12h autoridade, 20h desejo.
   **Formato Protagonista no ciclo:** para cada dia, antes de escrever, escolha a notícia, passe o filtro de protagonista
   e preencha `protagonista` {tipo, persona, desejo, vilao, nivel_consciencia} e a ficha `narrativa` (seção 4). Estático
   e carrossel do mesmo dia usam o mesmo `protagonista` e a mesma `narrativa` (o carrossel aprofunda o estático). Varie o
   tipo (espelho, ponte, alerta) entre os 3 dias quando as notícias permitirem e registre as escolhas em `ciclos/ciclos.json`
   (`protagonistas`: {<dia>: {tipo, persona}}), para a medição por tipo. Notícia que não passa no filtro vira estático de
   topo, sem carrossel de venda: busque outra notícia para o carrossel das 12h. História do guia ainda não confirmada:
   `guia_empatia` vazio e nada de história pessoal do Luan no slide 9 nem na legenda.
   Todo item leva `tema` = o `tema` do ciclo. Saúde: só afirmação defensável, com fonte; sem prescrição nem promessa.
   **Arco do ciclo (como os 3 dias conversam):** um tema, três ângulos que avançam. D1 = o caso (o fato da pessoa
   conhecida e o estudo que explica). D2 = o mecanismo e a aplicação (por que funciona e como entra na semana;
   o carrossel das 20h é o guia prático). D3 = a objeção e o convite (o que trava o leitor e o primeiro passo, com
   MÉTODO mais forte). Funil por horário: 7h topo (atenção), 12h meio (autoridade, salvamento), 20h fundo/humano.
   Cada estático termina chamando o carrossel do meio-dia do mesmo dia; o carrossel retoma o caso da manhã e, do slide 2
   em diante, fala com o leitor ("você"). O D3 (objeção e convite) usa uma objeção real da persona do dia (`personas.md`).
   Headline do estático: gancho do tipo escolhido (seção 8 do Protagonista), nomeia a pessoa, traz um número ou uma frase
   dela, **termina no leitor**, fica abaixo de ~60 caracteres e não promete resultado; 1–3 palavras em **destaque** no
   que muda para o leitor.
3. Peças (D1, D2, D3 = dias do ciclo; ids com o dia, ex. `k-2026-10-26-estatico`):
   - **Estático 07h** de cada dia (`k-<dia>-estatico`): notícia de pessoa conhecida ligada ao tema. Comece por
     `famosos` do ciclo (o `protagonista` de cada um está no item de mesmo `noticia_id` em `radar/curadoria/*.json`: use
     como ponto de partida e confira); sem nada lá, procure com WebSearch notícias das últimas 24 h, depois 72 h, depois 7 dias.
     Abra a matéria (WebFetch) e confirme o fato numa segunda fonte. Três pessoas ou fatos diferentes nos 3 dias.
     **Brasileiro primeiro** (`pessoa_br`; a lista `famosos` já vem nessa ordem). Gancho: nome + fato concreto.
     Foto: escreva `"pessoa": "<nome como aparece no Commons>"` na capa e deixe `foto` vazio. O robô "Renderizar
     artes" busca no Wikimedia Commons, confere a licença pelos metadados (só CC BY, CC BY-SA, CC0 ou domínio
     público) e preenche foto, crédito, licença e página de origem. Preencha SEMPRE a reserva para quando o Commons
     não tiver foto: `"foto_reproducao": "<URL da imagem da matéria ou do post da pessoa>"`, `"credito_reproducao":
     "Foto: Reprodução/<veículo ou @perfil>"` e `"origem_reproducao": "<link da matéria ou do post>"` (a `imagem` do
     item do radar costuma servir; confira que a foto mostra a pessoa e não é de menor). Sem nenhuma foto, a capa
     sai só com texto e vai para "Precisa de você".
     Depois do render, confira na prévia se a foto é mesmo da pessoa; se não for, troque o nome ou ponha `"pessoa": null`.
     Pedido: `{"formato": "estatico", "id", "data", "quando": "<dia>T07:00:00-03:00", "tema", "funil": "topo", "pauta",
     "protagonista", "narrativa", "legenda", "slides": [{"tipo": "capa", "titulo" (nomeia a pessoa, até ~60 caracteres, 1–3 palavras em **destaque**),
     "subtitulo" (chama para o carrossel das 12h), "fonte": "Veículo, DD/MM/AAAA", "link_noticia", "foto", "credito":
     "Foto: autor / Wikimedia Commons (CC BY-SA 4.0)", "licenca": "cc-by | cc-by-sa | dominio-publico | cc0",
     "pagina_origem", "foco"}]}`. Só o que a notícia afirma sobre a pessoa; nunca sugerir que ela usa ou recomenda o
     método; notícia negativa em tom informativo; menor de idade nunca. Sem MÉTODO na arte (vai na legenda).
   - **Carrossel 12h** de cada dia (`k-<dia>-carrossel`): aprofunda o gancho do estático daquele dia, com a estética
     Decodificado de `diretrizes/carrossel.md` e o **arco de 10 slides do Formato Protagonista** (`protagonista.md`,
     seção 6): 1 capa (personagem + pergunta ao leitor) · 2 espelho · 3 vilão · 4 problema interno · 5 causa com fonte ·
     6 o erro · 7 o que está em jogo · 8 o que o caso revela (insight, fundo claro, frase-assinatura) · 9 o guia
     (`texto_foto` com `rotulo` "O QUE EU FAÇO COM MEUS ALUNOS", foto do Luan e o plano em 3 passos com verbo) · 10 `cta`
     (MÉTODO + passo menor da `cta_transicao`). Personagem em no máximo 3 slides. Pedido leva `protagonista` e `narrativa`.
     Legenda na ordem da seção 7. A capa
     NUNCA usa a mesma foto do estático (05/11/2026): use outra foto da pessoa (outra matéria, outro evento) ou uma
     foto do Luan do `acervo`, com `"layout": "recorte"` na capa (foto em bloco no alto, título em fundo sólido) para o
     visual não repetir o do estático; ajuste `foco` para o rosto ficar no bloco. Slide 9 "O QUE EU FAÇO COM MEUS ALUNOS": `texto_foto` com
     uma foto do `acervo` do ciclo (abra as `previa` com Read, escolha a que combina e use
     `https://txiszakrpssubgvzpdcx.supabase.co/storage/v1/object/public/midia/<arquivo>`). Nunca a mesma foto do
     acervo em dois posts do ciclo.
   - **Carrossel 20h** do D2 (`k-<D2>-carrossel-noite`, quando 20:00): outro ângulo do tema (guia, aplicação, objeção),
     falando com a mesma persona do D2 em "você", Cena → Causa → Movimento e slide do guia com foto do Luan. Se partir de
     outra notícia, segue o Formato Protagonista completo.
   - **Meme 20h** do D3 (`k-<D3>-meme`, no lugar da foto pessoal do D3): frase de situação de treino com até 8 palavras,
     de preferência ecoando a notícia do ciclo; foto do `acervo` com a expressão certa (URL do bucket como acima).
     Pedido: `{"formato": "meme", "id", "data", "quando": "<D3>T20:00:00-03:00", "tema", "pauta", "frase", "foto",
     "foco" (opcional), "legenda"}`. Legenda: 1 linha de humor + 1–2 de ensinamento + "Me manda MÉTODO no direct." +
     3 hashtags. Sem foto adequada no acervo, faça a foto pessoal do D3 no lugar.
   - **Foto pessoal 20h** do D1 (e do D3 se não houver meme) (`k-<dia>-foto`): use `fotos` do ciclo. Sem camisa: só em
     contexto de vida (praia, viagem, natureza) e no máximo uma vez por ciclo; se vier outra, troque por uma do `acervo`. Abra a `previa` com Read e escreva a
     legenda: 2 a 4 linhas curtas, só o que a foto mostra (não invente lugar, aluno nem história), a ligação com o
     tema do ciclo, "Me manda MÉTODO no direct." e 3 hashtags. Pedido: `{"formato": "foto", "id", "data", "quando",
     "arquivo", "tema", "pauta", "legenda"}`.
   - Escreva `render/fontes/<id>.json` para estáticos e carrosséis (diretrizes/carrossel.md, seção Fontes).
   - Stories (v3, desde 26/11/2026): escreva o plano de cada dia do ciclo em `ciclos/stories/<dia>.json` (formato e
     regras no bloco v3 de `diretrizes/stories.md`): série, assunto (para a foto do fundo), palavra do tema, abertura (só o título, até 12 palavras,
     sem "Hoje:"), virada com artigo verificado (DOI ou PubMed), resultado com critério mensurável. O robô "Preparar
     stories" monta as 5 telas sozinho às 18h da véspera. Sem plano, só sai o Post novo.
4. Rode `python render/revisar.py render/pedidos/<id>.json` em cada pedido e corrija todo "problema".
   Depois confira à mão, em cada estático e carrossel de notícia, a revisão do Protagonista (seção 10 de
   `diretrizes/protagonista.md`, ainda fora do revisar.py): `narrativa` com desejo, vilão e sucesso; personagem em até
   3 slides; "você" entre os slides 2 e 4; slide 9 com foto do Luan; nenhuma promessa com número e prazo nos slides 8 a 10;
   primeira pessoa de aluno só com `aluno_autorizado: true`. Corrija antes do push.
   A revisão barra foto já usada em outro post do feed nos últimos 21 dias (mesmo link; no render, também a mesma
   imagem vinda de outro link). Cada foto aparece em um post só: estático, carrossel, foto pessoal e meme do ciclo
   com fotos diferentes entre si e das peças já publicadas. Foto pessoal de ciclo anterior não volta em slide.
4a. Etiquete em `acervo/tags.json` (chave = `drive_id`) cada foto de `fotos` e `acervo` que você abriu: expressao,
    contexto, sem_camisa, aluno, evitar (true para foto fora de contexto ou pose de exibição; o robô não escolhe mais),
    nota. Não marque `autorizado`: só o Luan registra autorização de aluno.
5. Marque o ciclo em `ciclos/ciclos.json`: `status` "pacote_pronto", `pecas` (lista de ids). `git pull --rebase`,
   commit ("ciclo: pacote <id>") e push. Até 3 tentativas; confira em origin/main. Se não der, deixe `status` "erro" com
   `erro` (1 frase) e termine a resposta com "CICLO NÃO ENTREGUE: <motivo>".
6. Espere o robô "Renderizar artes", `git pull` e abra as prévias (`render/previas/<id>.jpg`). Texto cortado, foto
   ruim ou destaque errado: corrija e faça push de novo (no máximo 1 correção por peça).
