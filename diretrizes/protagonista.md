# Formato Protagonista: linha editorial dos posts que partem de notícia

Versão 1 · aprovado pelo Luan em 26/11/2026 · cópia de trabalho do doc `claude/formato-protagonista.md` do Project.
Vale para todo post que parte de notícia (Estúdio e Pacote do ciclo). Não substitui `diretrizes/conteudo.md` (v2):
curadoria do Radar, fotos, ciclo de 3 dias e voz continuam valendo. O que muda é **quem é o protagonista** e **como o
arco do post leva até o MÉTODO**. Personas em `diretrizes/personas.md`.

Base: StoryBrand (Donald Miller), níveis de consciência de Eugene Schwartz e a fórmula da marca Cena → Causa → Movimento.

## 1. A ideia em uma frase
A notícia traz o personagem, o leitor é o herói, e o Luan e o método são o guia que mostra o caminho.

## 2. Os papéis
| Papel | Quem é | O que faz na história | O que nunca faz |
|---|---|---|---|
| **Personagem** | Pessoa da notícia (famoso, atleta) | Abre a conversa e serve de espelho ou de prova | Ser o herói depois do slide 2; parecer cliente, parceiro ou usuário do método |
| **Herói** | O leitor (Rafael, Thiago ou a variação feminina) | Tem um desejo, enfrenta um vilão, muda de identidade | Ser julgado ou culpado |
| **Vilão** | Uma crença, um hábito ou um obstáculo | Explica por que o herói não chega lá | Ser uma pessoa, uma marca ou um colega de profissão |
| **Guia** | O Luan | Mostra empatia ("já estive aí") e autoridade (dado, aluno, experiência) | Ser o centro da história ou se gabar |
| **Plano** | O método (Avaliação Estratégica → plano → acompanhamento) | Tira a confusão e o medo do próximo passo | Prometer número com prazo |

Regra de ouro: se, ao terminar o post, a pessoa lembra mais do famoso do que de si mesma, o post virou fofoca.

## 3. Curadoria: o filtro de protagonista
Depois dos filtros da v2 (famoso brasileiro com história pessoal; "a pessoa comentaria isso no almoço do trabalho?"):

**Dá para escrever, em uma linha cada, o desejo e o vilão da persona dentro dessa notícia?**
- Sim: a notícia entra no Formato Protagonista.
- Não: pode virar post de topo (alcance), marcado `funil: topo`, sem pretensão de venda.

| Tipo | Quando usar | Pergunta que o post faz | Exemplo de pauta |
|---|---|---|---|
| **Espelho** | O personagem tem o mesmo problema ou desejo do leitor | "Ele passou pelo que você passa. E você?" | Atriz de 60 anos começa a levantar peso na menopausa |
| **Ponte** | O feito está longe da realidade do leitor (recorde, atleta jovem, marca de elite) | "O que eu faria para chegar perto disso depois dos 30?" | Atleta de 25 anos bate recorde |
| **Alerta** | O personagem cometeu um erro comum ao leitor | "Ele fez o que você provavelmente já fez." | Famoso conta que fez dieta radical e perdeu massa |

No tipo **Ponte**, o objetivo nunca é a marca do atleta. É o **processo** do atleta na escala da vida do leitor.

Campos no item do Radar e no pedido:
```json
"protagonista": {
  "tipo": "espelho | ponte | alerta",
  "persona": "rafael | thiago | feminina",
  "desejo": "uma linha",
  "vilao": "uma linha",
  "nivel_consciencia": 1
}
```
Notícia de famoso costuma pegar o leitor no nível 1 ou 2: a capa abre a conversa e não vende; a venda fica no fim do arco.

## 4. Ficha narrativa (antes de escrever)
Nenhum texto é escrito antes da ficha. Ela vai no pedido JSON, no campo `narrativa`.

| Campo | Pergunta | Regra |
|---|---|---|
| `personagem` | Quem é e qual é o fato? | Só o que a notícia afirma, com fonte |
| `persona` | Para quem é este post? | Uma persona por post |
| `desejo` | O que o leitor quer? | Um só: saúde, energia, presença, controle ou longevidade |
| `vilao` | O que impede? | Um só, e é uma crença ou um hábito |
| `problema_externo` | O que acontece no corpo ou na rotina? | Concreto e mensurável |
| `problema_interno` | Como isso faz ele se sentir? | Nas palavras do leitor (frases reais do direct, avaliações, stories) |
| `problema_filosofico` | Por que isso é injusto? | Uma frase, opcional na legenda |
| `causa` | O que a ciência mostra? | Dado com fonte; é a Causa da fórmula |
| `erro` | O que o leitor faz de errado hoje? | Da lista de Erros da persona |
| `em_jogo` | O que ele perde se não mudar? | Sutil, sem medo nem prazo |
| `guia_empatia` | Onde o Luan já esteve no lugar dele? | Só da história do guia confirmada (seção 12); sem ela, vazio |
| `guia_autoridade` | Por que confiar? | Dado, aluno autorizado, anos de prática |
| `plano` | Quais são os 3 passos? | Avaliação → plano que cabe na agenda → evolução acompanhada |
| `sucesso` | De quem → para quem? | Identidade, nunca número com prazo |
| `cta_direto` | O que pedir? | MÉTODO no direct (o material do online ainda não existe) |
| `cta_transicao` | Qual é o passo menor? | Salvar, responder, mandar para alguém |
| `personagem_nome` | Nome do personagem como aparece nos slides | Usado pela revisão para contar em quantos slides ele aparece |
| `ficha_persona` | De onde vem o contexto do leitor? | Obrigatório. Ver abaixo |

### Ficha da persona (obrigatória desde 26/11/2026)
Todo post de notícia leva `narrativa.ficha_persona` com o nível de consciência e **um item copiado, palavra por
palavra, de cada bloco** da persona escolhida em `diretrizes/personas.json`:

```json
"ficha_persona": {
  "consciencia": 2,
  "objetivo": "<item de objetivos>",
  "desejo": "<item de desejos>",
  "dor": "<item de dores>",
  "erro": "<item de erros>",
  "objecao": "<item de objecoes>"
}
```
- O texto do post usa pelo menos o desejo, a dor e o erro (com as suas palavras, não precisa copiar a frase).
- A objeção entra na legenda ou no slide 9 (o guia), respondida pelo plano.
- O objetivo orienta o `sucesso` e o plano em 3 passos.
- O nível de consciência decide o quanto o post vende: 1–2 abre conversa, 3 traz autoridade e prova, 4–5 quebra objeção e convida.
- `desejo` e `problema_interno` da narrativa são a versão do post, nas palavras do leitor; os da `ficha_persona` são o item original da ficha.
- Variação feminina: onde o bloco dela estiver vazio, vale um item da ficha do Rafael ou do Thiago.

## 5. Quem narra
| Narrador | Quando | Regra |
|---|---|---|
| **"Você"** (o leitor) | Padrão do corpo do post | Do slide 2 em diante, o texto fala com o leitor |
| **Luan em primeira pessoa** | Gancho do tipo Ponte e slide do guia | Só fatos reais da vida dele |
| **Aluno em primeira pessoa** | Prova de transformação | Só aluno real, com autorização registrada no acervo e fala dele. Sempre vai para "Precisa de você" |

Proibido: depoimento inventado ou persona fictícia contada como pessoa real; frase atribuída ao personagem que não está
na notícia; afirmar sobre o corpo ou a rotina do personagem mais do que a notícia afirma (se a fonte diz que ela começou
a levantar peso, não escrever que ela "trocou o cardio pelo peso").

## 6. Arco do carrossel das 12h (10 slides)
| Slide | Tipo no render | Função na história | Fórmula |
|---|---|---|---|
| 1 | `capa` | Personagem + pergunta que vira para o leitor | Nome + fato + pergunta |
| 2 | `texto_foto` | **Espelho**: o desejo do leitor dentro do caso | "Você também…" |
| 3 | `texto_foto` | **Vilão**: a crença ou o obstáculo | Cena |
| 4 | `insight` | **Problema interno**: o que ele sente | Frase do leitor |
| 5 | `numero` | **Causa** com dado e fonte | Causa |
| 6 | `numero` ou `texto_foto` | **O erro** do leitor e por que ele não funciona | Causa |
| 7 | `insight` | **O que está em jogo**, dito de leve | Uma frase |
| 8 | `insight` (fundo claro) | **O que o caso revela**: identidade de → para | Frase-assinatura |
| 9 | `texto_foto` com `rotulo` e foto do Luan do acervo | **O guia**: empatia + autoridade + plano em 3 passos | Movimento |
| 10 | `cta` | Convite direto + passo menor | MÉTODO |

- Slide 9 é `texto_foto` (e não `licao`) porque o render só desenha foto em `texto_foto`. É o slide "o que eu faço com
  meus alunos" da v2, sempre com foto do Luan do acervo.
- O personagem aparece no máximo na capa e em mais dois slides, como prova.
- Continuam valendo: um fato por slide, títulos de até ~60 caracteres, alternância de fundos e a lista de vícios de IA.

## 7. Estático das 7h e legenda
**Estático das 7h (pilar Conexão):** foto do personagem e um título que termina no leitor. Sem MÉTODO e sem oferta na arte.

**Legenda (carrossel):**
1. Primeira linha: opinião do Luan, já virada para o leitor.
2. Um parágrafo com o fato e a Causa.
3. Um parágrafo com a cena do leitor e o erro.
4. Um parágrafo com o guia: o que o Luan faz com os alunos.
5. CTA de transição + "Me manda MÉTODO no direct." + 3 a 5 hashtags.

**Stories:** regras v3 de `diretrizes/stories.md` (palavra do convite ligada ao conteúdo do dia, nunca MÉTODO).

## 8. Ganchos por tipo
| Tipo | Estrutura | Forma (não é post final) |
|---|---|---|
| Espelho | [Nome], [idade], [fato]. [Pergunta ao leitor] | "[Nome], 60, começou a levantar peso. Tarde pra você?" |
| Ponte | [Personagem] fez [marca]. O que eu faria para chegar perto disso depois dos 30? | "[Atleta], 25, bateu o recorde de [X]. O que eu faria depois dos 30?" |
| Alerta | [Nome] contou que [erro]. [Ligação com o leitor] | "[Nome] cortou tudo e perdeu força. Você já fez a mesma dieta." |

Valem as regras de gancho da v2: nome conhecido + fato concreto + vontade de saber o resto.

## 9. Regras de texto
1. Um desejo e um vilão por post.
2. O leitor entra no slide 2 e não sai mais.
3. Problema interno nas palavras do leitor.
4. O que está em jogo é dito de leve. Proibidos: medo, prazo e escassez falsa.
5. Sucesso como identidade ("de quem lembra do auge para quem treina pelos próximos 30 anos"). Nunca número com prazo; no tipo Ponte, nunca prometer a marca do atleta.
6. O guia aparece com empatia e autoridade juntas.
7. Plano com 3 passos que começam com verbo.
8. Fidelidade ao fato (seção 5).
9. Vale tudo da `copy-social-ttc`: Cena → Causa → Movimento, vícios de IA proibidos, sem travessão.
10. Saúde (menopausa, hormônio, GLP-1, lesão): nível geral, "sinal de alerta, não diagnóstico", conduta com o médico.

## 10. Revisão automática (`render/protagonista.py`, chamado pelo `render/revisar.py`)
Vale para estático e carrossel com `protagonista` ou `narrativa` e para todo estático e carrossel do ciclo a partir de
28/11/2026. Rodar antes do push: `python render/revisar.py render/pedidos/<id>.json`.

Barra:
- Pedido do formato sem `protagonista` (tipo espelho, ponte ou alerta, e persona conhecida).
- Pedido do formato sem `narrativa`, ou sem `desejo`, `vilao` ou `sucesso`.
- Sem `ficha_persona`, com `consciencia` fora de 1 a 5, ou com objetivo, desejo, dor, erro ou objeção que não esteja na ficha da persona.
- Nome do personagem em mais de 3 slides.
- Nenhum "você" entre os slides 2 e 4.
- Slide 9 sem foto do Luan.
- Primeira pessoa de aluno sem `aluno_autorizado: true`.
- Promessa com número e prazo no slide 8, 9 ou 10.

Avisa:
- `desejo` ou `vilao` com mais de uma ideia (presença de "e" ou vírgula).
- `cta_transicao` vazio.
- Desejo, dor ou erro da ficha que não aparecem no texto do post (nem por palavra-chave); objeção que não aparece no carrossel.
- Nível de consciência diferente em `protagonista` e em `ficha_persona`.

## 11. Como medir
Por tipo (Espelho, Ponte, Alerta): seguidores ganhos, salvamentos, respostas nos stories e MÉTODO no direct.
Reavaliar depois de 10 posts e manter o tipo que mais gera MÉTODO por mil visualizações. Por isso todo pedido leva
`protagonista.tipo` e `protagonista.persona`.

## 12. História do guia (a confirmar pelo Luan)
Enquanto `diretrizes/historia-do-guia.md` não existir, o slide 9 e a legenda usam só `guia_autoridade` e não contam
história pessoal do Luan. `guia_empatia` fica vazio.
