# Radar — curadoria (sessão em segundo plano)

Roda 2x por dia (~6h17 e ~14h17, Brasília), 30 min depois da coleta. Ninguém está olhando: não pergunte nada.

## Entrada
- `radar/coleta.json` — notícias pré-selecionadas (id, canal, titulo, link, imagem, publicado_em, resumo).
  O `resumo` é só para você entender o assunto: nunca copie esse texto para o pitch.
- `radar/preferencias.json` — o que o Luan salvou, descartou ou transformou em pauta. Temas parecidos com os descartados
  perdem pontos; parecidos com salvos/virou_pauta ganham.
- `diretrizes/marca.md` — marca, tom, público, oferta.
- `radar/perfil-interesse.json` — o que o radar aprendeu sobre o gosto do Luan (assuntos, termos, ângulos, o que evitar).
  Notícias que batem com ele ganham pontos (até +15), as que batem com `evitar` perdem.
- Itens com `"referencia": true` (canal "Sua referência") são links que o Luan colou no botão "Ensinar o radar",
  às vezes com `nota_luan` (o que chamou a atenção dele). O campo `tipo` diz o que é: `noticia`, `instagram_reels` ou
  `instagram_perfil`. Veja "Referências do Luan" e "Instagram" abaixo.
- `radar/palavras-chave.json` — palavras que o Luan digitou no topo do Radar. Elas já trouxeram notícias na coleta (itens com
  `palavra`) e são o motor principal da busca de reels.
- Curadorias anteriores (`radar/curadoria/*.json`): notícia com o mesmo id já avaliada nas últimas 24 h mantém nota, motivo,
  pitch e cluster (recalcule só `em_alta`). Avalie de verdade só o que é novo.

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

## Referências do Luan (botão "Ensinar o radar")
Para cada item com `"referencia": true` cujo id ainda não está em `referencias_analisadas` do perfil:
1. Leia a matéria (WebFetch no `link`; se não abrir, use título, resumo e a `nota_luan`). Essas leituras não contam no limite de ~5.
2. Entenda por que ela interessa ao Luan: assunto, termos, o ângulo, o tipo de dado, o tom e o jeito de pensar que conversam
   com o nicho e a marca. A `nota_luan` vale mais que a sua leitura.
3. Atualize `radar/perfil-interesse.json`, refinando (não só acrescentando; junte o que for parecido, tire o que ficou velho):
   `resumo` (2–3 frases, em "você"), `assuntos` (até 15), `termos.pt` e `termos.en` (até 30 cada: palavras e expressões
   curtas que aparecem em títulos de notícia e ajudam a busca a achar matérias parecidas, nada genérico como "saúde"),
   `angulos` (até 8), `evitar` (assuntos), `evitar_termos` (termos de busca que trazem lixo), `aprendido[id]` (1 frase:
   o que esta referência ensinou), acrescente o id em `referencias_analisadas` e atualize `atualizado_em` (horário de Brasília).
4. Dê nota, motivo e pitch à própria referência como a qualquer notícia; no `motivo`, diga o que o radar aprendeu com ela.
Se houver fontes que publicam muito sobre os assuntos das referências e ainda não estão no radar, cite-as no fim da sua
resposta final (não adicione sozinho).

Referência do Instagram (`tipo` instagram_reels ou instagram_perfil): o título e o resumo podem vir pobres (o Instagram
fecha a página). Tente WebFetch no link; se não abrir, busque o perfil ou o reels com WebSearch e use a `nota_luan`. Aprenda
o FORMATO (como o vídeo é montado), a ESTRUTURA DO GANCHO, o ritmo, o uso de texto na tela, o tom e o tipo de perfil, e
atualize a seção `instagram` de `radar/perfil-interesse.json`: `resumo` (2–3 frases, em "você"), `formatos` (até 10, nomes
do catálogo abaixo ou novos quando fizer sentido), `ganchos` (até 8 estruturas de abertura, sem copiar frase de ninguém),
`perfis` (até 15 @, os de referência e os parecidos que você achar), e `aprendido[id]` como nas notícias.

## Instagram (reels)
Objetivo: achar reels que estão funcionando no nicho e dizer como o @tavarescoach faz a versão dele, de preferência
amarrada a uma notícia em alta da coleta.

0. Primeiro `radar/instagram.json` (robô, dados reais da API do Instagram): reels dos últimos 30 dias dos perfis de
   referência com engajamento >= 2x a mediana do próprio perfil (`razao`), com legenda, curtidas e comentários. Eles têm
   prioridade: analise cada um pela legenda (e WebFetch no link, se abrir) e cite a `razao` no `motivo`
   ("4,3x a média do perfil"). Perfis com `erro` são pessoais ou não existem: tire de `instagram.perfis`.
1. Busca (até ~10 WebSearch por rodada): para cada palavra de `radar/palavras-chave.json` (as mais recentes primeiro),
   procure `site:instagram.com/reel <palavra>` e variações em português e inglês; depois os perfis de `instagram.perfis`
   (`site:instagram.com/<perfil> reel`). Sem palavras nem perfis, use os `assuntos` do perfil de interesse.
   Não use raspadores nem serviços que entram no Instagram: só a busca e o WebFetch do próprio link.
2. Escolha até 8 reels por rodada: do nicho (treino, saúde, nutrição, sono, longevidade, medicina, revistas), recentes
   (de preferência últimos 30 dias), com formato que o Luan consegue gravar sozinho (câmera, academia, tela verde, sem
   produção pesada). Sinal de desempenho (curtidas, visualizações ou comentários visíveis no resultado) pesa a favor;
   nunca invente número. Não repita reels sugeridos nos últimos 7 dias.
3. Item na curadoria, junto das notícias:
   `id` "ig-" + 14 primeiros caracteres do sha1 do link sem parâmetros, `canal` "Instagram", `titulo` (o que o reels
   diz, em português, até ~90 caracteres), `link`, `imagem` (null se não tiver), `publicado_em` (data do reels; se não
   souber, o `gerado_em`), `tema`, `nota`, `motivo` (por que serve e qual sinal de desempenho você viu), `publico`,
   `cluster` (se o assunto bate com uma notícia da coleta, use O MESMO cluster: o Instagram conta como mais um canal
   no "em alta"), `em_alta`, e `pitch` (sempre, mesmo abaixo de 50):
   {"perfil": "@quem publicou",
    "formato": "mito x método | erro comum | notícia com tela verde | talking head com dado | lista (3 sinais/3 erros) |
                pergunta do aluno | POV | bastidor de aula | tutorial de exercício | antes e depois de rotina",
    "estrutura": "o reels tempo a tempo (0–2 s gancho · … · CTA), como o Luan deve gravar a versão dele",
    "por_que": "1 frase: o mecanismo que fez funcionar (tensão, número, identificação, contradição)",
    "gancho": "a versão do @tavarescoach, palavras SUAS, até ~12 palavras, no tom da marca",
    "angulo": "ângulo da marca", "noticia": "título da notícia da coleta que combina, ou null",
    "ponte": "como liga ao personal / Avaliação Estratégica"}
   `nota` 0–100: encaixe com o público e a marca, formato reproduzível, sinal de desempenho e combinação com notícia em alta.

## Saída
1. Escreva `radar/curadoria/AAAA-MM-DD-HH.json` (horário de Brasília): {"gerado_em": "...", "itens": [ {id, canal, titulo, link,
   imagem, publicado_em, tema, nota, motivo, publico, pitch, cluster, em_alta}, ... ]} com TODAS as notícias da coleta.
2. Apague arquivos de curadoria com mais de 3 dias.
3. `git pull --rebase`, commit ("radar: curadoria AAAA-MM-DD HH h", incluindo `radar/perfil-interesse.json` se mudou) e push. O robô "Radar de notícias" aplica no painel.
4. Atualize o contexto do Estúdio (as notas de histórico, atualidade e o aprendizado A/B das headlines dependem disso).
   Carregue ArtifactData (ToolSearch "select:ArtifactData"); url https://claude.ai/artifact/4qy326S1jHcMxz8Ycw4QbH.
   a. `list` da collection `criacoes` com `out_dir` numa pasta temporária (ex.: o scratchpad) e `query.limit` 200.
   b. `python3 metricas/estudio_contexto.py --criacoes <pasta>/criacoes` (gera instagram, radar e aprendizado).
   c. `list` da collection `contexto` para pegar as versões; depois um `batch` com três `set` (com `if_version` de cada um):
      `instagram` <- metricas/estudio-contexto.json, `radar` <- metricas/estudio-radar.json,
      `aprendizado` <- metricas/estudio-aprendizado.json (doc que ainda não existe vai sem `if_version`).
   Se algo falhar, siga em frente: é opcional. Não commite a pasta temporária.
