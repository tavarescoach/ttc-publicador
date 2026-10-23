# Tese-mãe: contrato da pauta

Versão 1 · 23/10/2026 · Primeiro passo da pipeline de criação ampliada (radar → pauta → tese-mãe → saídas).

## Fluxo
1. Luan escolhe a notícia (Radar ou pesquisa).
2. Sessão monta 5 opções de pauta a partir dela, mais a 6ª escrita pelo próprio Luan (opção "ideia").
3. Luan escolhe uma opção. A sessão grava a **tese-mãe** em `tese-mae/<id>.json` e a envia para avaliação (status `aguarda_aprovacao`).
4. Só depois da aprovação do Luan a sessão gera as saídas. Ajustes na tese acontecem antes das saídas.
5. Todas as saídas ficam como textos brutos disponíveis no painel; o Luan escolhe o que usar. Nada vai ao ar fora do fluxo já aprovado.

## Regras
- O **carrossel nasce da tese-mãe**. Não é gerado em paralelo.
- Todo texto segue `.claude/skills/copy-social-ttc/SKILL.md`. A revisão automática e `revisar_roteiro.py` valem para as saídas que se aplicam.
- Número ou estatística só entra com fonte em `fontes`. Sem fonte confiável, não entra.
- Prova com aluno e temas de saúde (hormônio, suplemento, remédio, lesão, gravidez, menopausa) exigem aprovação do Luan em qualquer saída.
- YouTube não é obrigatório: o roteiro de vídeo-aula é uma saída de texto. Gravar e publicar é decisão posterior.
- Foco: autoridade pessoal do personal trainer. TTC é contexto secundário, exceto no blogpost (site do TTC), onde é protagonista.

## Campos da tese-mãe (`tese-mae/<id>.json`)

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | texto | `tm-AAAA-MM-DD-<slug>` |
| `criada_em` | ISO com -03:00 | quando a tese foi gravada |
| `origem` | `radar` \| `ideia` \| `pesquisa` | de onde veio a pauta |
| `reportagem` | objeto ou null | `{titulo, veiculo, data, link}` da notícia de partida |
| `opcao_escolhida` | texto | título da opção de pauta escolhida |
| `tese` | texto (1 frase) | a afirmação central, dita como fato |
| `cena` | texto | a cena que o leitor vive (vira enquete e abertura) |
| `causa` | texto (1 frase) | frase-assinatura, a causa real, afirmada |
| `evidencias` | lista de `{afirmacao, fonte}` | 2 a 4 itens, cada um com link |
| `emocao` | `admiracao` \| `indignacao` \| `reconhecimento` \| `urgencia_perda` \| `pertencimento` | a emoção única que o conteúdo desperta (skill `acao-emocional-ttc`, seção 1) |
| `lacuna` | texto | o que a manchete promete e o conteúdo entrega; precisa estar fechada no fim |
| `passo_final` | texto | o único próximo passo do leitor, com a razão |
| `funil` | `topo` \| `meio` \| `fundo` | objetivo de venda da pauta |
| `publico` | `executivo` \| `mulher` \| `ambos` | para quem é a pauta |
| `cta` | texto | CTA do funil (padrão: "Me manda MÉTODO no direct") |
| `pontos_de_cuidado` | lista | saúde, prova com aluno, claims a não fazer |
| `aprovacao` | `{status, em}` | `aguarda_aprovacao` \| `aprovada` \| `ajustar` \| `descartada` |
| `saidas` | objeto | status por saída (ver abaixo) |

## Saídas (cada uma com `status`: `aguarda_tese` | `gerando` | `pronto` | `erro`)
- `carrossel`: slides + legenda, segue `diretrizes/carrossel.md`
- `blogpost`: título, subtítulo, corpo com seções, fontes (site do TTC)
- `video_aula`: roteiro de fundo de funil com capítulos, promessa, prova, método e CTA
- `ementa`: pontos de conversa para live ou podcast, tempo por bloco e perguntas-gatilho
- `reels_direcao`: direção de gravação (5 partes, duração por funil)
- `teleprompter`: texto para a boca, derivado de `reels_direcao`
- `broll_narracao`: narração em VOZ/PONTOS com planos de imagem (formato de `narracao-broll.md`)

Cada saída guarda o texto bruto em `saidas/<id-da-tese>/<saida>.md` e aparece no painel, na pauta da tese, depois da publicação do carrossel.

## Ordem de construção (próximos passos)
1. Este contrato (feito).
2. Gravação da tese-mãe com status `aguarda_aprovacao`, sem gerar saídas.
3. Módulo `reels_direcao` + `teleprompter` (saídas mais curtas, testáveis com a pauta de 23/10).
4. Módulo `blogpost`.
5. Demais saídas (vídeo-aula, ementa, narração de b-roll) e carrossel derivado da tese.
