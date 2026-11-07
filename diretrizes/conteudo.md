# Diretrizes de conteúdo v2 (decididas pelo Luan em 02/11/2026)

Valem para toda sessão que escolhe notícia, escreve ou monta arte do @tavarescoach (Radar, Estúdio, Pacote do ciclo).
Onde conflitarem com `marca.md`, `carrossel.md`, `ciclo.md` ou a skill `copy-social-ttc`, valem estas.
Cópia no Project: `claude/diretrizes-conteudo-v2.md`.

## Objetivo
Entender o público atual e entregar, com base em ciência:
- **Conexão:** famosos com os mesmos problemas do público.
- **Autoridade:** o Luan mostra resultado e aplicação prática do método.
- **Desejo:** saúde, resultado, corpo bonito.
Isso leva à venda (MÉTODO no direct).

## Por que mudou (insights de 30 dias, 02/11/2026)
- Famoso brasileiro com história pessoal: 2 mil a 12 mil visualizações. Famoso de fora: 340 a 926. Estudo sem personagem, capa azul só com texto: 124 a 261.
- Notícia de famoso dá alcance mas não seguidor quando o Luan não aparece (Simone Mendes: 12 mil visualizações, 1 seguidor).
- O que trouxe seguidor foi o Luan na foto (carrossel da Bahia: 242 seguidores, 74 toques no link).

## Os três pilares no ciclo de 3 dias
| Pilar | Formato | Entrega |
|---|---|---|
| Conexão | Estático 07h com famoso brasileiro | a pessoa conhecida tem o mesmo problema do leitor |
| Autoridade | Carrossel 12h | ciência + "o que eu faço com meus alunos", com foto do Luan |
| Desejo | Foto pessoal ou meme 20h | o corpo, a saúde e a vida que o método dá |

Arco do carrossel: famoso (conexão) → o que a ciência diz → o que eu faço no TTC, com foto do Luan (autoridade) → o resultado possível (desejo) → MÉTODO.

## 1. Notícias
- Prioridade: famoso **brasileiro** com história pessoal (o que fez, sentiu, mediu ou confessou) ligada a corpo, saúde, treino ou rotina.
- Famoso de fora só se for muito conhecido no Brasil e o tema for muito próximo do leitor.
- Estudo entra como prova dentro da história, nunca como pauta sozinho.
- Pergunta de corte: o leitor comentaria isso no almoço do trabalho? Se não, fica fora.
- O tema do ciclo segue a melhor história disponível; não se força uma história para caber no tema.

## 2. Texto
- Voz informal no gancho e na legenda, como o Luan fala ("Eita ferro", "Confia, pae", "meti o shape"): gíria e humor liberados. O miolo continua informativo, com fonte.
- 1ª linha da legenda é uma opinião do Luan, em primeira pessoa, não um resumo da notícia.
- Continuam proibidos: os vícios de IA da skill copy-social-ttc (seção 4), promessa com prazo, culpa, escassez falsa.

## 3. Gancho
- **Desde 06/11/2026: o gancho provoca emoção.** Régua, 9 tipos e exemplos em `diretrizes/ganchos.md`. Pergunta, provocação, contraste, autoironia, gíria e até 2 palavras em caixa alta liberados no gancho. Freio: número com fonte, nada inventado, nada de alarme de saúde.
- Fórmula com famoso: nome conhecido + fato concreto + cutucada no leitor ("O Bruninho tem 40 anos. Qual é a sua desculpa mesmo?").
- "A faixa de força semanal ligada a menos mortes" vira "30 minutos de musculação por semana mudam quanto tempo você vive".
- Proibido: gancho abstrato, de estudo, ou que qualquer perfil poderia postar.

## 4. Fotos (adaptado do Manual Master do TTC, com a identidade LT)
1. **70/30:** 70% das peças com pessoas reais (Luan, TTC, alunos autorizados, famosos da notícia); 30% composição limpa (fundo escuro + tipografia), só quando o conteúdo pedir.
2. **Capa sempre com rosto:** do Luan, de aluno autorizado ou do famoso. Capa de carrossel ou estático sem foto não agenda sozinha (vai para "Precisa de você").
3. **Calor na foto, respiro no layout:** pessoas em ação, luz natural, expressão real; um único destaque por peça.
4. **Tratamento único:** fotos do acervo saem sem filtro, só enquadradas (decisão de 24/10); o modelo aplica o mesmo tratamento em todas as capas.
5. **Nunca fingir que a foto é real:** banco de imagem não aparece como TTC ou aluno do Luan.
6. **Aluno** (imagem, nome, número) só com autorização registrada (`acervo/tags.json`, `"autorizado": true`).
7. **Evolução** com dados e contexto, nunca antes e depois sensacionalista.
8. **Áreas seguras:** margem de 96 px no feed; nada nos 250 px do topo e da base em stories e capas de reels.
9. **Kit de modelos:** capa com foto, texto, número, "o que eu faço", CTA e meme (`render/carrossel.html`, `render/meme.html`). Mudança de modelo passa pelo Luan.
10. **Foto de famoso:** primeiro Wikimedia Commons (licença livre); senão a foto da própria notícia como **reprodução**, com crédito na arte ("Foto: Reprodução/veículo ou @perfil") e `pagina_origem`. Decisão do Luan em 02/11, substitui a exigência de licença comercial de 24/10. Menor de idade nunca.
11. **Sem camisa:** liberado em contexto de vida (praia, viagem, natureza), no pilar Desejo, no máximo uma vez por ciclo. Fora: pose de exibição em academia ou espelho e enquadramento sensual.
12. **Uma foto, um post (05/11/2026):** a mesma foto não aparece em dois posts do feed em 21 dias, nem por outro link. Estático e carrossel do mesmo dia têm fotos diferentes; a capa do carrossel usa o layout `recorte` para não repetir o visual do estático. A revisão barra.
13. **Etiquetas do acervo** em `acervo/tags.json` (quem gera o pacote etiqueta cada foto que abre), para escolher a foto certa.

## 5. Meme (formato `meme`)
- Tarja branca no topo com frase de situação de treino; foto do Luan do acervo embaixo; logo LT e @tavarescoach no rodapé.
- **Até 8 palavras** na frase (leitura em 2 segundos). O contexto, o porquê e a ciência ficam na legenda.
- Exemplos: "Aluno na segunda: 'comi pouco no churrasco'" · "Eu lendo o LDL do marido da Simone" · "Eu vendo aluno pular o dia de perna".
- Uma vez por ciclo, no lugar de uma das fotos pessoais das 20h. Pode ecoar a notícia do ciclo.
- Legenda: 1 linha de humor + 1 a 2 linhas de ensinamento + "Me manda MÉTODO no direct." + 3 hashtags.

## Público e anúncios
- Correção prática atrai o homem-alvo (92% homens, 73% entre 25 e 44). A mulher 30–50 quase não aparece: toda semana, pelo menos uma pauta pensada para ela.
- Impulsionamento: raio de 3–5 km de Copacabana/Botafogo, 30–50 anos, objetivo mensagens; só post que já foi bem sem anúncio.
