# Narração e b-roll — reels do @tavarescoach

Referência da skill copy-social-ttc para todo vídeo em que a voz do Luan e as imagens trabalham juntas: reels de topo (voz por cima de b-roll), reels de meio (fala para a câmera com cortes de b-roll), reels de fundo (olho no olho, com b-roll pontual) e vídeos de bastidor nos stories.

Versão 2 · 18/10/2026 · curadoria avançada. Base: commentary-writer, voice-over-script-writer, teleprompter-script-writer, cold-open-writer, transition-narration-writer, narrator-voice-adapter e scene-breakdown-writer (autopunk-media-skills, MIT); voiceover-direction (clawfu-skills, MIT); hook-system, short-form-video-specs, edit-anatomy e short-form-video (marketingskills, Corey Haines). Calibrada com dados do próprio @tavarescoach: duas transcrições da fala do Luan e o tempo médio assistido dos reels publicados (metricas/painel.json). As regras de texto da skill (Cena → Causa → Movimento, vícios de IA) continuam valendo dentro da narração.

Para conferir um roteiro automaticamente: `python render/revisar_roteiro.py tarefas.json` (seção 17).

---

## 1. O princípio: cada camada faz um trabalho

Um reels tem três camadas ao mesmo tempo. Nenhuma repete a outra.

| Camada | Trabalho | Erro comum |
|---|---|---|
| **Imagem** (b-roll ou o Luan na câmera) | Mostra. Prova que é real, que é no TTC, que alguém faz | Imagem genérica que poderia ser de qualquer academia |
| **Voz** | Diz o que a imagem não mostra: o número, o porquê, o contexto, a consequência | Narrar o que já está na tela ("aqui eu coloco a anilha na barra") |
| **Texto na tela** | Ancora a ideia para quem assiste sem som e resume o bloco | Escrever na tela, palavra por palavra, o que a voz está dizendo |

Teste rápido de cada bloco: tape o áudio e veja se o texto na tela ainda conta a história; feche os olhos e veja se a voz ainda faz sentido. Se a voz descreve a imagem, reescreva com o que só a voz pode trazer.

> Imagem: anilha encaixando na barra.
> Errado (voz descreve): "Coloco carga na barra."
> Certo (voz acrescenta): "Quarenta minutos por semana."
> Tela (resume, não repete): "A dose que 16 estudos encontraram"

## 2. O que os números do perfil dizem (calibração em 18/10/2026)

- **Tempo médio assistido dos reels publicados: 7 a 12,6 segundos.** O reels do fim de semana (19,4 s) teve 7,2 s de média, perto de 37% do vídeo. A maior parte do público decide nos primeiros 3 a 8 segundos: gancho e rampa valem mais que o resto do roteiro.
- **Consequência para o topo:** reels de topo ficam entre 12 e 20 segundos. A frase-assinatura tem de chegar antes dos 15 s, e a informação principal (o número) já aparece no gancho.
- **Consequência para meio e fundo:** o que importa para quem sai cedo vai até os 8 s; o resto é para quem ficou e é ali que entram o porquê e o CTA.
- Atualize esta seção quando houver 10 reels com dados (métricas em metricas/painel.json: `tempo_medio_s`; duração em render/reels/<id>/info.json).

## 3. A voz do Luan, como ela é

Medido em duas gravações dele (uma lida, uma falada de improviso):

- **Ritmo: 2,85 a 2,9 palavras por segundo.** Mais rápido do que um locutor de documentário. Use **2,8 palavras/s** para planejar.
- **Quando lê, fica duro.** A gravação lida tem "fim de semana bem-vivido", "mantém-se em movimento", "assim como": construções de texto escrito.
- **Quando fala de improviso, fica vivo.** "Tu vai, faz o treino, sua, e até fica cansado, mas o corpo no final das contas não muda." Cena concreta, verbos em sequência, ritmo de conversa.
- **Marcas reais da fala dele (manter):** "tá", "pra", "tu" misturado com "você", "a gente", "no final das contas", "pelo contrário", "seu ponto de partida", "pra gente seguir daí".
- **Vícios que aparecem na fala dele (cortar no roteiro e na edição):** "Fica aqui comigo até o final que eu vou te dizer o porquê" (promessa de retenção que o público já reconhece), "Siga em frente" como fecho genérico, "Resultado não é perfeição, é consistência" (contraste encenado).

**Regra que sai disso: roteiro fixo só onde precisa.**

| Parte | Como o roteiro entrega |
|---|---|
| Gancho (0–3 s) | Texto exato. Gravar 3 versões |
| Frase-assinatura | Texto exato. Gravar 3 vezes |
| CTA | Texto exato |
| Tensão e explicação | **Pontos de fala**, não frases: 2 ou 3 tópicos curtos com o número e a ordem. O Luan fala com as palavras dele |

No topo (voz por cima de b-roll, 12–20 s) o roteiro inteiro pode ser fixo, porque é curto e é narração. No meio e no fundo, o miolo é sempre em pontos de fala.

## 4. Escreva a partir dos planos que existem

O roteiro de narração nasce da lista de planos, não o contrário. Antes de escrever a voz:

1. Liste os planos que o Luan consegue gravar no TTC em poucos minutos (banco abaixo).
2. Escolha um plano por ideia. A ideia que não tem plano vira texto na tela sobre fundo escuro ou sai do roteiro.
3. Ordene: primeiro mostrar, depois explicar. O plano entra meio segundo antes da frase que ele sustenta.

**Banco de planos do TTC** (reaproveitáveis na semana toda e nos stories):
- Carga: anilha encaixando, presilha fechando, barra sendo carregada vista de cima, anilha tocando o chão.
- Mãos: giz, pegada fechando na barra, mão anotando carga, dedo seguindo a planilha.
- Movimento: levantamento terra de lado, agachamento de frente, remada em câmera lenta, descida controlada.
- Medida: fita métrica na cintura, bioimpedância, cronômetro, planilha com cargas subindo semana a semana.
- Rotina: relógio às 7h, porta do TTC abrindo, garrafa e caderno no banco, celular virado para baixo.
- Noite e sono: quarto escuro, celular deixado de lado, despertador.
- O Luan: corrigindo a pegada de alguém, anotando na planilha, olhando o cronômetro, explicando com a mão. Pelo menos 5 planos dele por bloco de gravação: ele é o fio do perfil.
- Aluno: só com autorização escrita; mostre a execução e o número, nunca o corpo sem roupa.

## 5. Como captar no bloco semanal

- **Três enquadramentos de cada momento:** perto (mãos, anilha), médio (corpo inteiro no aparelho), aberto (0,5x, o TTC em volta). Um momento gravado assim rende três planos.
- **Clipes curtos:** 3 a 5 segundos cada, muitos clipes, nunca um take longo andando.
- **Regra do movimento:** se a pessoa se move, o celular fica parado. Se nada se move, o celular faz um avanço lento ou desliza de lado.
- **Ordem:** grave por lugar do TTC, não pela ordem do vídeo. Ao final, 5 minutos passando de novo por 10 a 12 coisas, nos três enquadramentos.
- **Plano-gancho:** marque como favorito no celular o melhor plano de abertura de cada reels. A edição começa por ele.
- **Banco reaproveitável:** um álbum "b-roll TTC" no celular. Planos de carga, mãos e medida servem para várias pautas e para os stories da semana.

## 6. Escrever para o ouvido

A voz é ouvida uma vez, sem voltar. Regras:

- **Uma frase por respiração.** De 6 a 14 palavras. Acima de 18, quebre.
- **Verbo cedo.** Sujeito e verbo na primeira metade da frase. "Dezesseis estudos mediram isso" e não "Em uma análise que reuniu dezesseis estudos publicada em 2022, pesquisadores mediram…".
- **Números falados.** Escreva como se fala: "quarenta minutos", "dezoito por cento", "dois mil e vinte e dois". Na tela, o algarismo ("40 min").
- **Nada que só funcione escrito.** Sem parênteses, sem "et al.", sem sigla que o leitor não conhece (diga "uma revista de medicina do esporte", não "BJSM"). A fonte completa vai na legenda.
- **Português falado do Luan** (seção 3). Pode "a gente", "olha", "tá", "pra". Não pode "outrossim", "ademais", "vale ressaltar", "nesse sentido", "assim como", "mantém-se".
- **Uma ideia por bloco**, e o bloco seguinte continua a premissa do anterior (a rampa, seção 7).
- **Os vícios de IA valem em voz alta também**, e soam pior falados: "não é X, é Y", "o resultado? …", "sem X, sem Y, sem Z", "e sabe o que aconteceu?", "fica comigo até o final".

**Tempo.** Planeje com **2,8 palavras por segundo** (o ritmo medido do Luan) e some 1 segundo para cada silêncio marcado.

| Duração | Palavras faladas |
|---|---|
| 12 s | 30–34 |
| 15 s | 38–42 |
| 20 s | 50–56 |
| 40 s | 100–112 |
| 60 s | 150–168 |

O número final sai do cronômetro, lendo em voz alta, não da conta.

**Marcas no roteiro:**
- `//` pausa de respiração (não se fala).
- `[silêncio 1 s]` a imagem trabalha sozinha.
- **negrito** na palavra de ênfase (no máximo uma por frase).

## 7. Gancho e rampa

**Três componentes, um trabalho cada.** Nos primeiros 3 segundos, imagem, voz e tela entram juntas e se completam:

| Componente | Função | Exemplo (seg, 19/10) |
|---|---|---|
| Imagem | Para o dedo | Anilha batendo na barra, close, com o som do metal |
| Voz | Abre o loop | "Quarenta minutos por semana." |
| Tela | Ancora para quem está sem som | "A dose que 16 estudos encontraram" |

O primeiro quadro já tem movimento. Nada de logo, nada de "oi, pessoal", nada de abertura em preto.

**Abertura em três tempos** (para reels de meio e fundo): (1) jogar a pessoa no meio da cena ou do número, (2) levantar a pergunta sem responder, (3) uma frase curta que dá vontade de ficar. Sem contexto, sem apresentação: isso vem depois ou não vem.

**A rampa (segundos 3 a 15).** O bloco depois do gancho continua a premissa do gancho. Se o gancho prometeu um número, o segundo bloco começa a explicar o número. Com 7 a 12 s de tempo médio assistido (seção 2), é na rampa que o perfil perde gente: se a retenção cair, mexa na rampa antes de trocar o gancho.

## 8. Formatos de reels para o nosso nicho

Escolha o formato antes de escrever. Cada um tem um motivo diferente para a pessoa ficar.

| Formato | Forma | Funil | Duração | O que gravar |
|---|---|---|---|---|
| **Número medido** | Um dado de estudo, explicado e aplicado | Topo | 12–20 s | Voz sobre b-roll de carga e medida |
| **Matemática do tempo** | A conta da semana: "40 minutos", "3 treinos de 35", "o que cabe na agenda de quem trabalha 10 horas" | Topo/meio | 15–30 s | Relógio, cronômetro, planilha, agenda |
| **Olhar de treinador** | "O que eu corrijo primeiro em quem chega aqui", filmado no TTC, com a mão do Luan corrigindo | Meio | 30–45 s | Luan corrigindo pegada, postura, ritmo (aluno com autorização) |
| **Bastidor de medida** | Uma avaliação, a bioimpedância, a planilha: o objeto que o público não vê | Meio/fundo | 30–45 s | O equipamento e o processo, sem expor o aluno |
| **Pergunta real** | Uma pergunta da caixinha ou do direct, lida na tela, respondida olhando para a câmera | Meio | 30–60 s | Print da pergunta (sem nome) + fala |
| **Duas opções** | Duas escolhas reais que o público pesa ("três treinos curtos ou um longo no sábado"), e o Luan escolhe uma | Meio | 30–45 s | Fala + b-roll das duas opções |
| **Lista nomeada** | "3 sinais", "2 ajustes": cada item com nome, cada item com um plano | Meio/fundo | 40–60 s | Um plano por item |
| **Prova** | Contexto → trava → ajuste → resultado medido, com autorização | Fundo | 45–90 s | Planilha e execução do aluno, depoimento se ele quiser |
| **Convite** | Olho no olho: a quem serve a Avaliação Estratégica, o que acontece nos 40 minutos, MÉTODO | Fundo | 30–60 s | Luan, plano fechado; b-roll da avaliação |

Evite: trend dançada, sketch, POV encenado, rua com entrevista falsa. Não combinam com Especialista + Mentor.

## 9. Matriz de ganchos

Antes de escrever os ganchos da semana, monte a matriz. Dez ganchos para dez combinações diferentes valem mais que trinta versões de um só.

| # | Público | Dor, nas palavras dele | Formato | Imagem | Voz | Tela |
|---|---|---|---|---|---|---|

- **Dor nas palavras do público:** tirada do banco de pautas do Guia, de respostas da caixinha e do direct. "Meu corpo não responde mais" vence "estagnação do progresso".
- **Cobertura:** na semana, pelo menos um gancho para o público feminino, um de cada funil e nenhum formato repetido no mesmo dia.
- **Sem repetir** gancho, abertura ou plano-gancho dos últimos 7 dias.

## 10. Transições entre blocos

O bloco seguinte nasce do anterior por uma de três ligações:

- **Continuação:** o número pede o porquê ("Dezesseis estudos mediram isso." → "O menor risco apareceu perto de quarenta minutos.").
- **Contraste real:** duas coisas que o público de fato compara (treino curto × treino longo), nunca uma negação que ninguém afirmou.
- **Causa e efeito:** o que acontece → o que isso faz com o corpo.

Proibido como ponte: "Mas", "Enquanto isso", "E tem mais", "Agora vem a parte importante", "Presta atenção nisso". A troca de plano já faz a passagem; a voz entra direto na ideia nova.

## 11. Silêncio e ritmo de corte

- **Nem toda imagem precisa de voz.** Antes da frase-assinatura, segure de 0,5 a 1 segundo de imagem sem fala (a barra descendo, a anilha tocando o chão). O silêncio dá peso à frase seguinte.
- **O corte cai no começo da frase**, não no meio da palavra.
- **Duração do plano:** topo, 1 a 3 s por plano; meio e fundo, cortes de b-roll de 2 a 4 s por cima da fala.
- **No reels de meio e fundo**, o b-roll entra quando a fala cita um objeto ou um número ("a carga da semana passada" → close da planilha) e sai de volta para o rosto na frase-assinatura e no CTA. A conclusão é sempre olho no olho.

## 12. Formato do roteiro (o que o pacote e a lista do dia entregam)

Toda peça com narração sai em blocos, um por plano. No plano em PDF, como tabela:

| Tempo | Imagem | Voz | Tela |
|---|---|---|---|
| 0–3 s | Anilha batendo na barra (close) | "Quarenta minutos por semana." | A dose que 16 estudos encontraram |

Na lista do dia (tarefas.json, lida no celular e no guia Como gravar), em texto corrido, um bloco por linha:

```
0–3 s · IMAGEM: anilha batendo na barra (close)
   VOZ: "Quarenta minutos por semana."
   TELA: A dose que 16 estudos encontraram
```

Para o miolo de reels de meio e fundo (seção 3), a linha VOZ vira PONTOS:

```
9–23 s · IMAGEM: b-roll do despertador, depois aquecimento no TTC
   PONTOS: 13 adultos, uma noite em claro, em laboratório · no dia seguinte, 18% menos construção de músculo · cortisol subiu 21%
   TELA: 13 adultos · −18% proteína muscular · +21% cortisol
```

Abaixo dos blocos, sempre:
- **Planos para gravar:** a lista de b-roll, na ordem de gravação (agrupada por lugar do TTC, não pela ordem do vídeo).
- **Palavras faladas e duração estimada** (2,8 palavras/s + silêncios).
- **Intenção da voz** (seção 14).

## 13. Fala para a câmera (teleprompter)

Quando o Luan quiser ler na câmera (app de teleprompter no celular):

- Uma frase por linha. `//` no fim de cada frase e onde ele deve segurar.
- Nada de rubrica no meio do texto; a intenção vai numa linha no topo.
- Só gancho, frase-assinatura e CTA vão completos. O miolo vai em pontos (seção 3), para ele olhar e falar.

## 14. Direção da própria voz: pela intenção

O Luan grava a própria voz. A direção é a intenção, não a entonação ("fale isso como…", nunca "suba o tom no fim").

- Intenção padrão: **explicar para um aluno na pausa entre séries.** Perto, calmo, sem vender.
- Topo (voz sobre b-roll): "você está contando um dado que te surpreendeu, para um amigo."
- Meio: "você está corrigindo um aluno que entendeu errado, sem dar bronca."
- Fundo: "você está convidando alguém que confia em você para um próximo passo."

Ajustes comuns, para o próprio Luan ouvir o take e corrigir:
- **Soou locutor:** fale mais baixo e mais perto do celular, como numa conversa.
- **Soou lido:** grave um segundo take sem olhar o roteiro, com as suas palavras. Pela calibração da seção 3, este costuma ser o melhor.
- **Corrido:** respire em cada `//`. Você fala rápido (2,9 palavras/s); no gancho e na frase-assinatura, desacelere.
- **Monótono:** pense no aluno real que precisaria ouvir isso, antes de começar.
- **Vendendo demais no CTA:** fale como um convite, não como um anúncio.

**Como gravar a voz:** celular a um palmo da boca, num lugar sem eco (carro parado, quarto com cortina), modo avião. Grave bloco a bloco, com 1 segundo de silêncio antes e depois. Grave o gancho e a frase-assinatura três vezes.

## 15. Edição e tela

- **Áudio:** os clipes de b-roll sem som, a não ser o som que conta história (o metal da anilha no gancho). Música baixa por baixo da voz, entrando em fade e saindo em fade no último segundo. Em conteúdo com fala, prefira o áudio original ao som em alta.
- **Texto na tela:** branco, sem caixa colorida, fonte sans em negrito, frases curtas. Fica parado enquanto o bloco dura (sem animação de entrada). Uma palavra em vermelho #C1121F no máximo.
- **Área segura (1080×1920):** texto e o que importa ficam entre 220 px do topo e 500 px da base, com 180 px de margem nas laterais. Embaixo ficam a legenda e os botões do Instagram.
- **Legenda queimada** (a fala transcrita) ajuda quem assiste sem som. Quando houver, o texto do bloco sobe para o terço de cima.

**Copiar a edição de um reels de referência.** Quando o Luan mandar um reels que gostou, faça a ficha de edição antes de gravar: tempo de cada corte, onde o texto entra na tela, estilo da legenda, movimentos (avanço, corte seco), som. Depois liste as 3 a 5 marcas que fazem o estilo ("corte seco a cada frase com avanço de 5%", "texto parado no terço de cima"). Copia-se a técnica, nunca o texto, as imagens ou a ideia do outro.

## 16. Diagnóstico depois de publicar

Cada métrica aponta para uma parte do reels. Mude uma parte por vez.

| Sinal | Onde está o problema | O que mudar no próximo |
|---|---|---|
| Poucas visualizações para o alcance da conta | Primeiro quadro e capa | Plano-gancho com movimento; capa com o número |
| Tempo médio abaixo de 30% da duração | Gancho ou rampa (seção 7) | Rampa continuando a premissa; cortar contexto |
| Tempo médio bom, poucos salvos | A explicação não deixou nada para levar | Um número ou um passo que dá para aplicar amanhã |
| Poucos compartilhamentos | Falta uma frase que a pessoa queira mandar | Frase-assinatura mais curta e mais específica |
| Visualizações e salvos bons, zero MÉTODO | Ponte para a oferta | CTA mais concreto: o que acontece nos 40 minutos |

Referência atual: reels do fim de semana, 19,4 s, 7,2 s de média (≈37%).

## 17. Conferência antes de entregar o roteiro

Rode `python render/revisar_roteiro.py tarefas.json` (ou com o caminho de um arquivo de roteiro). Ele aponta: frase da voz com mais de 18 palavras, algarismo na voz, vício de IA, voz e tela repetindo as mesmas palavras, duração declarada diferente da estimada e falta de silêncio antes da frase-assinatura.

Depois, à mão:
- [ ] A voz não descreve nenhuma imagem; cada bloco acrescenta um número, um porquê ou uma consequência.
- [ ] Toda ideia tem um plano que dá para gravar no TTC hoje; o que não tem, saiu ou virou tela.
- [ ] O número principal aparece até os 8 segundos; a frase-assinatura, antes dos 15 s no topo.
- [ ] Meio e fundo: miolo em pontos de fala, gancho/frase-assinatura/CTA em texto exato.
- [ ] No meio e no fundo, a frase-assinatura e o CTA são olho no olho.
- [ ] Nenhum "fica comigo até o final", "siga em frente", "presta atenção".
- [ ] Nada inventado: aluno, caso e número só se forem reais e com fonte.

## 18. Exemplo completo — segunda, 19/10 (topo, voz sobre b-roll)

Intenção: contar um dado que surpreendeu, para um amigo.

| Tempo | Imagem | Voz | Tela |
|---|---|---|---|
| 0–2 s | Anilha batendo na barra, close, com o som do metal | "Quarenta minutos por semana." | A dose que 16 estudos encontraram |
| 2–6 s | Mãos no giz, a pegada fechando na barra | "Depois dos trinta, a força cai. // E quase todo mundo culpa a idade." | Depois dos 30 |
| 6–12 s | Levantamento terra de lado, subida lenta | "Dezesseis estudos mediram isso. // O menor risco de morte apareceu perto de **quarenta** minutos de força por semana." | 16 estudos · menor risco com 40 min/semana |
| 12–13 s | A barra desce e a anilha toca o chão | [silêncio 1 s] | |
| 13–17 s | Close da planilha, dedo seguindo a carga que sobe semana a semana | "O músculo responde em qualquer década // quando a carga **sobe**." | Salva para quem diz que não tem tempo |

Palavras faladas: 45 · duração estimada: 16 a 18 s (45 ÷ 2,8 + 1 s de silêncio). Frase-assinatura antes dos 15 s.
Planos para gravar (na ordem do TTC): planilha na mesa → giz e pegada → anilha na barra (close, com som) → terra de lado, subida lenta, até a anilha tocar o chão.
