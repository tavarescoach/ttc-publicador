# Direção de criação — Carrossel "decodificado" com identidade LT

Padrão aprovado pelo Luan em 17/10/2026: ESTRUTURA e ESTÉTICA do estudo dos carrosséis do @brandsdecoded__
(skill "carrossel-decodificado-ttc", modelo Canva DAHYRWWZ43I) com a IDENTIDADE LT (logo LT, fundo escuro,
vermelho só no detalhe, CTA "MÉTODO"). Nunca copiar logo, nome, frases ou layout de outra marca.
Exemplo aprovado: render/pedidos/c-2610171339-y4f-carrossel.json (prévia em render/previas/).

## v3 (26/11/2026): arco do Formato Protagonista
O carrossel das 12h segue os 10 slides de `diretrizes/protagonista.md` (seção 6): capa com personagem → espelho → vilão (a antítese da série do dia) → problema interno → causa → erro → o que está em jogo → identidade de → para → o guia com foto do Luan ("o que eu faço com meus alunos") → CTA MÉTODO. Antes de escrever, preencher a ficha `narrativa`. Um slide salvável (checklist, teste, tabela) por carrossel. A estrutura v2 abaixo vale onde não conflitar.

## v2 (02/11/2026): arco conexão → autoridade → desejo
Leia `diretrizes/conteudo.md`. O carrossel segue: famoso ou caso (conexão) → o que a ciência diz → o que o Luan faz
com os alunos, com foto dele do acervo (autoridade) → o resultado possível (desejo) → MÉTODO. A capa sempre tem rosto
(do famoso, do Luan ou de aluno autorizado); capa sem foto não agenda sozinha.

## Lógica
- O "caso" é narrado slide a slide: um estudo, um fenômeno de treino, um atleta, uma crença comum que foi medida.
- Cada slide = 1 ideia, com pelo menos 1 dado concreto (número, data, fonte). Sem fonte confiável, sem dado.
- A lição chega só no fim. Não moralizar no meio.
- Tom: jornalístico e factual, sem exclamação, sem emoji. Sujeito + verbo + dado. Tom de voz da marca (diretrizes/marca.md).
- Copy: siga a skill `.claude/skills/copy-social-ttc/SKILL.md` (Cena → Causa → Movimento, três perguntas, vícios de IA). A revisão automática barra "não é X. É Y.", "sem X, sem Y", pergunta respondida pelo próprio texto, revelação com dois-pontos e travessão.
- A frase-assinatura (a Causa) aparece uma vez: na capa ou no slide 8, não nos dois. Legenda abre com gancho próprio, diferente do slide 1.

## Estrutura (9 a 10 slides, v2)
1. capa — nome conhecido + fato concreto, 1 a 3 palavras em **destaque** (vermelho). Foto com rosto em tela cheia (famoso, Luan ou aluno autorizado). Precisa parar a rolagem sozinha.
2. contexto — o caso da pessoa conhecida ou a cena do leitor (texto_foto). Conexão.
3–6. ciência — 1 fato por slide, alternando `numero` (número gigante) e `texto_foto`/`insight`. Cada slide puxa o próximo.
7. "O QUE O CASO REVELA" — a leitura (insight, fundo claro).
8. "O QUE EU FAÇO COM MEUS ALUNOS" — `texto_foto` com `rotulo`, foto do Luan do acervo (`acervo` do ciclo: URL do bucket) e a aplicação prática, em primeira pessoa. Autoridade. Obrigatório.
9. "O QUE MUDA EM VOCÊ" — o resultado possível, sem prazo nem promessa (licao, com `nota`). Desejo.
10. CTA — `cta`: "Me manda **MÉTODO** no direct."

## Fundos
- marinho / preto / claro. Nunca o mesmo fundo em 3 slides seguidos. Claro no máximo 2 vezes.

## Tipos de slide (campos do JSON)
- capa: titulo, foto, layout (opcional: "recorte" = foto em bloco no alto e título em fundo sólido; padrão = foto em tela cheia). Nunca a mesma foto do estático do dia nem de outro post dos últimos 21 dias.
- texto_foto: rotulo (opcional), titulo, texto, foto (opcional; sem foto o texto centraliza), fonte (opcional)
- numero: rotulo, numero, unidade (opcional, ex.: "semanas"), titulo, texto, fonte
- insight: rotulo, titulo, texto (pode abrir com **frase em destaque**)
- licao: rotulo, titulo, texto, nota
- cta: titulo, texto, cta
- `**palavra**` = destaque vermelho. Títulos: até ~60 caracteres (máx. 90). Textos de apoio: 18–45 palavras.

## Fotos (regras completas em diretrizes/conteudo.md, seção 4)
- Ordem de preferência: famoso da notícia (capa) e fotos do Luan do acervo (capa ou slide 8). Banco gratuito com licença comercial (Pexels, Unsplash) só para slides de apoio (2–6), nunca na capa quando houver pessoa ou foto do Luan.
- Foto de banco nunca pode parecer o TTC ou aluno do Luan.
- URL direta da imagem: Pexels `https://images.pexels.com/photos/<ID>/pexels-photo-<ID>.jpeg?auto=compress&cs=tinysrgb&w=1600`.
- Estilo: documental, luz dura, escuro ou P&B, pessoas reais treinando, 30–50 anos, homem e mulher conforme o público da pauta.
- EVITAR (banco): homem sem camisa, fisiculturismo, poses de modelo, sorrisos posados, academia "de catálogo", imagens com marcas/logos visíveis.
- Conferir a página da foto (título/descrição) antes de usar. Na dúvida, sem foto.

## Capa de pauta de notícia com pessoa conhecida
- Pauta que nasce de notícia com pessoa central (atleta, celebridade, executivo, figura pública): a capa mostra essa pessoa, numa foto do contexto do fato. Sem pessoa central, a foto do próprio fato. O título nomeia a pessoa.
- Fonte da foto, em ordem: 1) licença livre (Agência Brasil, Wikimedia Commons CC BY/CC BY-SA/domínio público, Flickr oficial com CC); 2) divulgação oficial; 3) a foto da própria notícia ou do Instagram da pessoa como **reprodução** (`licenca` "reproducao", crédito "Foto: Reprodução/veículo ou @perfil", `pagina_origem` = link da matéria ou do post), aceita pelo Luan em 02/11/2026; 4) sem foto: capa tipográfica, que vai para "Precisa de você".
- Campos na capa: `foto`, `credito` ("Foto: autor / agência"), `licenca` (cc-by | cc-by-sa | dominio-publico | cc0 | divulgacao | reproducao), `pagina_origem`, `link_noticia`, `foco` opcional (posição CSS do recorte, ex.: "30% center"). O crédito substitui o @ do rodapé da capa.
- A capa é editorial: nada de MÉTODO, oferta ou logo em posição de parceria. Nunca sugerir que a pessoa usa ou recomenda o método. Sem montagem nem filtro que altere o corpo. Sobre corpo e saúde da pessoa, só o que a notícia afirmou. Notícia negativa: tom informativo e passa pelo Luan. Menor de idade nunca vai na capa.

## Legenda
1ª linha: opinião do Luan em primeira pessoa (v2), diferente da capa; "Decodificando [tema]." pode abrir quando o caso for uma história. Depois 2 parágrafos curtos com os fatos + 1 parágrafo de lição + CTA do funil + "Me manda MÉTODO no direct." + 3–5 hashtags (nicho e bairro).

## Fontes (aparecem no painel, na janela do conteúdo)
Junto com o pedido, escreva `render/fontes/<id>.json` (mesmo id do pedido) com TODAS as referências usadas, com link clicável:
`[{"tipo": "estudo", "titulo": "Autor et al. (ano) — título. Revista", "url": "https://..."},
  {"tipo": "noticia", "titulo": "Veículo (data) — título da matéria", "url": "https://..."}]`
- tipo: estudo | noticia | artigo. Prefira o link do estudo (revista, PubMed ou PMC) e acrescente a notícia que levou ao tema (ex.: a matéria do Radar).
- Só URLs que você abriu e conferiu. O robô "Renderizar artes" grava as fontes no card sem mexer na aprovação.

## Checklist
- [ ] Todo número tem fonte e data   - [ ] render/fontes/<id>.json com os links   - [ ] 1 ideia por slide   - [ ] Fundos alternam
- [ ] Capa com rosto   - [ ] Slide 8 com foto do Luan   - [ ] Lição liga ao treino e à Avaliação Estratégica   - [ ] Nada copiado de outra página
