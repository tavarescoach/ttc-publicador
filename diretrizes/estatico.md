# Estático v2: publicação de valor individual (26/11/2026)

Decisão do Luan em 26/11/2026. Substitui o "estático das 7h com foto do famoso como gancho do carrossel".
Doc completo (com o banco de frases) no Project: `claude/estatico-v2.md`.

## A ideia

O estático entrega uma ideia completa num só olhar, tirada da ficha da persona (`personas.md`). Ele não anuncia o
carrossel, não usa famoso e não tem MÉTODO. A pessoa da notícia vai para a capa do carrossel das 12h.

## Dois testes (obrigatórios)

1. **Vale sozinho:** se a pessoa só vir esta imagem, ela leva alguma coisa?
2. **Reconhecimento ou envio:** ela se vê na frase ou mandaria para alguém?

## Função (uma por estático) e escada do ciclo

| Função | Campo da ficha | Dia do ciclo |
|---|---|---|
| `dor` | Dores / problema interno | D1 |
| `erro` | Erros | D2 |
| `crenca` | Vilão (crença ou hábito) | D2 |
| `objecao` | Objeções | D3 |
| `valor` | Manifesto ("Corpo forte, evolução sem acaso.") | D3 |

A persona alterna por ciclo (Rafael, Thiago; variação feminina em ~30% dos ciclos).

## Texto

- Frase de até 12 palavras: até 3 linhas brancas (`frase_branca`, quebras com `\n`) + 1 linha vermelha com o desfecho (`frase_vermelha`).
- Uma ideia só. O vilão é crença ou hábito, nunca pessoa, marca ou colega.
- Nada de número com prazo, aluno inventado, alarme de saúde ou escassez falsa. Sem travessão.
- Voz informal liberada (é o gancho do post).

## Arte (padrão aprovado: post "ERRO")
- Fade da foto para o marinho #07112A (27/11/2026), igual às capas do carrossel; nunca para preto puro.

Modelo `render/estatico-v2.html`, 1080×1350: foto de fundo inteira (escura, azul-marinho, ligada ao assunto; do
acervo ou de banco), logo LT no alto à esquerda, bloco no terço inferior com traço vermelho, etiqueta da função,
linhas brancas em Roboto Condensed e a última linha em vermelho; @tavarescoach no rodapé. A fonte se ajusta sozinha
para caber. Referência no Canva: "Estáticos v2 — 6 exemplos (padrão ERRO)" (DAHcD3ZeCV0).

## Legenda

1ª linha: opinião do Luan. Depois Cena, Causa (com fonte se for afirmação científica), Movimento. Fecha com CTA de
transição ("salva…", "manda para…") + "me manda <PALAVRA> no direct" (palavra ligada ao tema, nunca MÉTODO) + 3 a 5 hashtags.

## Horário

Janela 06h–11h. Fase de teste: alternar 07:00, 09:00 e 11:00 por 3 ciclos (9 estáticos). O horário com mais
salvamentos + compartilhamentos por mil de alcance vira o padrão; reavaliar todo mês. Estático às 11:00 empurra o
carrossel do dia para 12:30.

## Pedido

```json
{"formato": "estatico_v2", "id": "v2-<dia>-estatico", "data", "quando", "tema", "funil": "topo",
 "pauta": "<a frase inteira>", "funcao": "dor|erro|crenca|objecao|valor", "persona": "rafael|thiago|feminina",
 "campo_ficha": "<item da ficha>", "angulo_complementar": "<o que ele diz que o carrossel do dia não diz>",
 "frase_branca": "linha 1\nlinha 2\nlinha 3", "frase_vermelha": "desfecho.", "foto": "<URL do bucket>",
 "foco": "center 30%", "legenda": "..."}
```

## Revisão (`render/revisar.py`, `revisar_estatico_v2`)

Barra: campo obrigatório vazio, função fora da lista, sem foto, frase com mais de 12 palavras, referência a outro post
("veja", "às 12h", "no próximo post", "arrasta", "no carrossel"), MÉTODO na arte ou na legenda, número com prazo na
frase, famoso no pedido. Avisa: frase com duas ideias.

## Medição

Salvamentos + compartilhamentos por mil de alcance, comparados com os últimos 10 estáticos de prévia. Reavaliar
depois de 10 estáticos v2, por função e por persona.
