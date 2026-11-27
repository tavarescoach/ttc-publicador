# Dor → Movimento: carrossel de tela dividida (v1.1, 26/11/2026)

Aprovado pelo Luan em 26/11/2026. Versão completa, com o banco de pares e o histórico do protótipo, no doc do Project
`claude/formato-dor-movimento.md`. Render: `render/dor_movimento.py` + `render/dor-movimento.html`.
Revisão: `revisar_dor_movimento` em `render/revisar.py` e `render/foto_qualidade.py`.

## Onde entra
- Publicação **extra**, fora do ciclo de 3 dias. Não substitui o estático nem o carrossel das 12h.
- Dias úteis alternados: semana A segunda, quarta e sexta; semana B terça e quinta.
- Manhã, a pelo menos 90 min do estático e do carrossel das 12h. Durante o teste de horário do estático:
  estático 7h → extra 9h; estático 9h → extra 7h; estático 11h → extra 7h30.
- Teste de 3 semanas: salvamentos + compartilhamentos por mil de alcance, seguidores e palavra no direct.

## Conteúdo
1. Uma persona (`rafael`, `thiago`, `feminina`) e um tema do calendário (`diretrizes/temas.md`) por carrossel. Hipertrofia fora.
2. **6 a 8 pares** de dor e movimento (com guia e CTA, até 10 slides, o limite da API do Instagram).
3. Pares vindos das Personas (problemas, dores, erros), de preferência com frases reais do direct e das avaliações.
4. A dor belisca: cena concreta que o leitor reconhece (a foto da praia, a camisa que marca, o fôlego na escada). Descreve, não humilha.
5. O movimento é uma ação de semana, começa com verbo no imperativo e dá para começar amanhã.

## Texto
- Dor: pergunta, até 7 palavras. Movimento: imperativo, até 6 palavras.
- Informal liberado. **Exceção à copy-social-ttc:** os vícios de IA não valem nesta linha (pergunta → resposta é o formato).
- Continuam valendo: nada de número com prazo, saúde em nível geral com fonte na legenda, sem travessão.

## Estrutura
Slides 1 a 8: um par por slide (o 1º é o par mais forte) → "O que eu faço com meus alunos" (foto cheia do Luan) →
CTA "Salva pra usar essa semana" + "Me manda MÉTODO no direct" (ou a palavra do tema).

## Arte
- 1080×1440, dividida ao meio (720 + 720). Em cima: foto do Luan + a dor. Embaixo: foto do Luan fazendo o movimento + o movimento.
- Tipografia única: Roboto Condensed 800, caixa alta, nas duas metades e nos slides cheios. Só a cor muda: última palavra do movimento em vermelho #C1121F.
- Logo LT em **todos** os slides (canto superior esquerdo, ~330 px) e @tavarescoach no rodapé.
- Marinho só no degradê atrás do texto; **nunca filtro de cor sobre a foto**.

## Regras de foto (a revisão barra)
1. **Rosto visível em todas as fotos** (de cima e de baixo), de frente ou de perfil; óculos escuros pode. Bloqueadas: de costas, só pernas ou mãos, rosto de cabeça para baixo, escondido pelo celular ou cortado.
2. **Enquadramento:** rosto inteiro dentro da metade, com o centro entre 8% e 55% da altura, sem texto nem logo por cima. Sem `foco` no pedido, o robô calcula o recorte pelo rosto (centro a 32% da metade). Se não couber, troca a foto.
3. **Nitidez:** pelo menos 1080 px úteis depois do recorte (o render nunca amplia). Bloqueia quadro de reels de 720 px, print e foto de WhatsApp. Rosto tremido ou fora de foco também barra (variância do Laplaciano abaixo de 40, limite a calibrar nos 3 primeiros carrosséis).
4. **Original do Drive:** use `drive:<id>` (original do TTC Acervo), nunca a cópia de 1080×1350 do bucket.
5. **Luz:** nada de foto escura de banco. Fotos de banco proibidas nesta linha.
6. **Sem repetição** no carrossel (mesma imagem barra) e nos 21 dias do feed (regra geral).
7. Aluno só com `autorizado: true`. Sem camisa onde é natural (`diretrizes/conteudo.md`, fotos, item 11).
8. **IA:** permitida com qualidade excepcional, nunca de aluno, famoso, TTC ou do Luan, e com `ia: true` + `rotulo_ia: true` (rótulo "Conteúdo de IA" do Instagram).

## Etiquetas do acervo
`acervo/qualidade.py` (robô "Listar acervo", até 60 fotos por dia) grava em `acervo/tags.json`: `rosto`, `largura_px`,
`nitidez` e `dor_movimento` (`ok` | `bloqueada`). **Só fotos `dor_movimento: "ok"` entram nesta linha.** `rosto` pode ser
corrigido à mão para `perfil` ou `costas` (costas bloqueia).

## Pedido
```json
{
  "id": "d-2026-12-01-abd", "data": "2026-12-01", "quando": "2026-12-01T09:00:00-03:00",
  "formato": "dor_movimento", "persona": "rafael", "tema": "ABD", "funil": "topo",
  "pauta": "Barriga: 7 dores e 7 movimentos",
  "pares": [{"dor": "Encolhe a barriga na foto da praia?", "movimento": "Treine força 3x por semana",
             "foto_dor": "drive:<id>", "foto_movimento": "drive:<id>"}],
  "guia": {"titulo": "Barriga não sai", "titulo_vermelho": "no improviso.", "texto": "No TTC, …", "foto": "drive:<id>"},
  "cta": {"titulo": "Quer isso com", "titulo_vermelho": "plano e direção?", "texto": "…", "palavra": "MÉTODO", "foto": "drive:<id>"},
  "legenda": "opinião do Luan\n\npar + causa (com fonte)…\n\no que eu faço com os alunos\n\nSalva pra usar essa semana. Me manda MÉTODO no direct.\n#…"
}
```
Teste local: `python render/render.py <pedido>.json --local` (gera os PNGs em `render/_saida/` e a revisão, sem subir nada).
