# Formato Protagonista (aprovado na linha editorial v3, 26/11/2026)

Regras de narrativa de todo post do @tavarescoach, com ou sem notícia. Cópia de origem no Project: `claude/formato-protagonista.md`.
Parte de `diretrizes/linha-editorial-v3.md` (pilares, séries, grade, CTA). Base: StoryBrand (Donald Miller), níveis de consciência de Eugene Schwartz (doc Personas) e a fórmula da marca, Cena → Causa → Movimento.

## 1. A ideia em uma frase
O personagem abre a conversa, o leitor é o herói, e o Luan e o método são o guia que mostra o caminho.

## 2. Os papéis
| Papel | Quem é | O que faz | O que nunca faz |
|---|---|---|---|
| Personagem | Pessoa da notícia (famoso, atleta) ou situação típica ("quem chega dizendo…") | Abre a conversa e serve de espelho ou prova | Ser o herói depois do slide 2; parecer cliente ou usuário do método; ser um aluno inventado |
| Herói | O leitor: Rafael, Thiago ou a variação feminina, dentro de um perfil de meta | Tem um desejo, enfrenta um vilão, muda de identidade | Ser julgado ou culpado |
| Vilão | A antítese da série do dia (crença, hábito, obstáculo) | Explica por que o herói não chega lá | Ser uma pessoa, uma marca ou um colega |
| Guia | O Luan | Empatia ("já estive aí", `historia-do-guia.md`) + autoridade (dado, aluno autorizado, prática) | Ser o centro da história ou se gabar |
| Plano | O método: avaliação → plano que cabe na agenda → evolução acompanhada | Tira a confusão e o medo do próximo passo | Prometer número com prazo |
| Sucesso | Identidade de → para | "De quem volta com medo para quem volta testado" | Número com prazo |

Regra de ouro: se, ao terminar o post, a pessoa lembra mais do famoso do que de si mesma, o post virou fofoca.

## 3. Filtro de protagonista (notícias)
Depois dos filtros do Radar (`radar/CURADORIA.md`): **dá para escrever, em uma linha cada, o desejo e o vilão da persona dentro dessa notícia?**
- Sim: entra no formato, com um dos tipos abaixo.
- Não: só pode virar post de topo (`funil: topo`), sem pretensão de venda.

| Tipo | Quando usar | Pergunta do post | Séries que casam |
|---|---|---|---|
| Espelho | O personagem tem o mesmo problema ou desejo do leitor | "Ele passou pelo que você passa. E você?" | qualquer |
| Ponte | O feito está longe da realidade do leitor | "O que eu faria para chegar perto disso depois dos 30?" | `treino-do-luan`, endurance |
| Alerta | O personagem cometeu um erro comum ao leitor | "Ele fez o que você provavelmente já fez." | `sem-atalho`, `apaga-incendio` |

No tipo Ponte, o objetivo nunca é a marca do atleta: é o processo dele na escala da vida do leitor.

Campos no item do Radar:
```json
"protagonista": {"tipo": "espelho | ponte | alerta", "persona": "rafael | thiago | feminina",
                 "desejo": "uma linha", "vilao": "uma linha", "nivel_consciencia": 1}
```

## 4. Ficha narrativa (campo `narrativa` do pedido, antes de qualquer texto)
| Campo | Pergunta | Regra |
|---|---|---|
| `personagem` | Quem é e qual é o fato? | Só o que a fonte afirma |
| `persona` | Para quem é? | Uma por post |
| `desejo` | O que o leitor quer? | Um só (saúde, energia, presença, controle, longevidade, a meta da prova ou do tatame) |
| `vilao` | O que impede? | A antítese da série |
| `problema_externo` | O que acontece no corpo ou na rotina? | Concreto e mensurável |
| `problema_interno` | Como ele se sente? | Nas palavras do leitor, de preferência frases reais das respostas ao story e do direct |
| `problema_filosofico` | Por que é injusto? | Opcional |
| `causa` | O que a ciência mostra? | Dado com fonte verificada |
| `erro` | O que ele faz de errado hoje? | Da lista de Erros da persona |
| `em_jogo` | O que perde se não mudar? | Sutil, sem medo nem prazo |
| `guia_empatia` | Onde o Luan já esteve no lugar dele? | Só fatos de `historia-do-guia.md` |
| `guia_autoridade` | Por que confiar? | Dado, aluno autorizado, prática |
| `plano` | Quais são os 3 passos? | Começam com verbo |
| `sucesso` | De quem → para quem? | Identidade |
| `cta_direto` | O que pedir? | A palavra-chave da origem (linha-editorial-v3.md, seção 7) |
| `cta_transicao` | Qual é o passo menor? | Salvar, responder, mandar para alguém |

## 5. Quem narra
- "Você" (o leitor): padrão do slide 2 em diante.
- Luan em primeira pessoa: gancho do tipo Ponte e slide do guia, só com fatos de `historia-do-guia.md`.
- Aluno em primeira pessoa: só aluno real com `autorizado` no acervo e fala dele; sempre vai para "Precisa de você".
Proibido: depoimento inventado; persona fictícia contada como pessoa real; frase atribuída ao personagem que não está na fonte; afirmar sobre o corpo ou a rotina do personagem mais do que a fonte afirma.

## 6. Carrossel das 12h (10 slides)
| Slide | Tipo no render | Função | Fórmula |
|---|---|---|---|
| 1 | `capa` | Personagem + pergunta que vira para o leitor | Nome + fato + pergunta |
| 2 | `texto_foto` | Espelho: o desejo do leitor dentro do caso | "Você também…" |
| 3 | `texto_foto` | Vilão: a antítese da série | Cena |
| 4 | `insight` | Problema interno | Frase do leitor |
| 5 | `numero` | Causa com dado e fonte | Causa |
| 6 | `numero` ou `texto_foto` | O erro do leitor e por que não funciona | Causa |
| 7 | `insight` | O que está em jogo, dito de leve | Uma frase |
| 8 | `insight` (fundo claro) | O que o caso revela: identidade de → para | Frase-assinatura |
| 9 | `licao` ou `texto_foto` com foto do Luan | O guia: empatia + autoridade + plano em 3 passos ("o que eu faço com meus alunos") | Movimento |
| 10 | `cta` | Palavra MÉTODO + passo menor | CTA |

O personagem aparece no máximo na capa e em mais dois slides. Um dos slides 5, 6 ou 9 precisa ser salvável (checklist, teste, tabela). Continuam valendo as regras de `carrossel.md` (um fato por slide, títulos até ~60 caracteres, alternância de fundos, vícios de IA barrados).

## 7. Outras peças
- Estático das 7h: personagem + título que termina no leitor. Sem palavra-chave e sem oferta.
- Legenda: 1) opinião do Luan virada para o leitor; 2) fato e Causa; 3) cena do leitor e erro; 4) o guia; 5) CTA de transição + palavra-chave da origem + 3 a 5 hashtags.
- Stories: as 3 telas do arco (stories.md) seguem os papéis: tela 1 personagem e vilão; tela 2 guia com a causa e o artigo; tela 3 sucesso com critério de avaliação. Sem enquete (o robô não publica sticker): as frases reais do `problema_interno` vêm das respostas ao story.
- Reels: gancho do tipo da entrada nos 2 primeiros segundos; guia e plano no meio; TESTE no fim.

## 8. Regras de texto
1. Um desejo e um vilão por post.
2. O leitor entra no slide 2 e não sai mais.
3. Problema interno nas palavras do leitor.
4. O que está em jogo é dito de leve. Proibidos medo, prazo e escassez falsa.
5. Sucesso como identidade; nunca número com prazo; no tipo Ponte, nunca a marca do atleta.
6. Guia com empatia e autoridade juntas.
7. Plano com 3 passos que começam com verbo.
8. Fidelidade ao fato (seção 5).
9. Tudo da skill copy-social-ttc: Cena → Causa → Movimento, vícios de IA proibidos, sem travessão no texto publicado.
10. Saúde (menopausa, hormônio, GLP-1, lesão): nível geral, "sinal de alerta, não diagnóstico", conduta com o médico.

## 9. Revisão automática (a implementar em `render/revisar.py`)
Barra: pedido sem `narrativa` ou sem `desejo`, `vilao` ou `sucesso`; nome do personagem em mais de 3 slides; nenhum "você" nos slides 2 a 4; slide 9 sem foto do Luan; primeira pessoa de aluno sem `autorizado`; promessa com número e prazo nos slides 8, 9 ou 10.
Avisa: `desejo` ou `vilao` com mais de uma ideia; `cta_transicao` vazio.

## 10. Como medir
Por tipo (Espelho, Ponte, Alerta) e por série: seguidores ganhos, salvamentos, respostas nos stories e palavras-chave no direct. Reavaliar depois de 10 posts por tipo e manter o que mais gera conversa por mil visualizações.
