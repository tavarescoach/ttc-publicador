---
name: arte-treino-ttc
description: Use quando o Luan mandar uma foto dele e o report de um treino (sticker/print do Strava, Garmin, Apple Fitness, Hevy, planilha ou texto) e quiser a arte pronta para story ou feed do @tavarescoach, no estilo "pop-out" do story do Strava (ele recortado na frente da palavra gigante, da rota e do cartão de música, números no alto), na identidade LT.
---

# Arte de treino: foto + report

O Luan manda a **foto** e o **report** e recebe a arte pronta, sem perguntas no meio. Se ele disser a música que ouviu, ela entra no cartão de "tocando agora"; se mandar o print da música, a capa também.

Entrega: story 1080x1920 e feed 1080x1350 (os dois, salvo pedido).

## O estilo (referência: reel de @maluizamelo, "Strava pop-out")

Camadas, de trás para a frente (todas em `render/treino.html`):
1. **Fundo**: a própria foto desfocada e escurecida no azul da marca (`"fundo": "desfoque"`, padrão). Some com a bagunça do ambiente e funciona com selfie. Só use `"fundo": "foto"` (foto nítida em tela cheia) quando o fundo já é limpo, como céu.
2. **Palavra gigante** de ponta a ponta na base (CORRIDA, PERNAS, COSTAS, TREINO, TTC).
3. **Rota** em vermelho grosso, ampliada para a largura da arte.
4. **Cartão de música** em vidro fosco: capa, música, artista, barra de progresso, controles.
5. **O Luan recortado** (rembg, modelo birefnet-portrait), nítido e com sombra, cobrindo parte da rota e a ponta do cartão: é o efeito "sai da arte".
6. **Contorno da palavra** por cima dele: onde o corpo cobre a palavra, ela continua legível em traço.
7. **Números** em linha com divisórias (DISTÂNCIA | RITMO | TEMPO), logo LT à esquerda e @tavarescoach à direita, no alto.

## Passo a passo

1. **Salvar** a foto em `render/treinos/fotos/<data>.jpg` e o report em `render/treinos/rotas/<data>.png` (se for o sticker do Strava). Essas pastas ficam fora do git (`.gitignore`): são fotos pessoais.

2. **Ler o report.** O **sticker do Strava** é um PNG transparente cujos números e logo vêm em **branco**: numa prévia em fundo branco só aparece a rota laranja. Componha sobre fundo escuro antes de ler (PIL: `Image.new("RGBA", im.size, (20, 30, 50, 255))` + `alpha_composite`). Transcreva os números exatamente; não invente, não arredonde para melhor. Tempo vai como `49:08` (ou `1:02:15`).

3. **Escolher 3 métricas** (no máximo 4): corrida/bike, Distância · Ritmo · Tempo; musculação, Duração · Volume · a carga do exercício principal; condicionamento, Duração · FC média · Calorias. `"destaque": true` (vermelho) só para PR ou recorde de verdade.

4. **Rota.** Sticker do Strava: `"rota_img"` com o PNG; o script pega só o traçado laranja (descarta números e logo do Strava), pinta no vermelho da marca e põe na `rota_caixa` `[centro x, centro y, largura]`. Posicione para passar **atrás das cabeças ou do tronco**, com as pontas à mostra dos dois lados. Outro print com mapa: escreva 8 a 20 pontos em `"rota"`. Sem mapa, sem rota.

5. **Música** (só se ele disser qual): `"musica": {"titulo", "artista", "capa", "tempo", "resta", "progresso", "topo"}`. Sem `capa`, entra uma capa vermelha da marca com uma nota. Não invente a música.

6. **Palavra**: uma palavra curta do treino (CORRIDA, PERNAS, PEITO, COSTAS, TREINO) ou TTC, nada de "BORA", "MONSTRO", "SHAPE" (`.claude/skills/copy-social-ttc/SKILL.md`).

7. **Montar o JSON** em `render/treinos/<data>.json` (lista com story e feed). Exemplo que funcionou com uma selfie em close (rosto até a borda de cima):
   ```json
   [{"arquivo": "render/treinos/saida/2026-10-27-story.png", "formato": "story",
     "foto": "treinos/fotos/2026-10-27.jpg", "palavra": "CORRIDA", "pessoa": {"base": 1.08}, "dados_topo": 318,
     "metricas": [{"rotulo": "Distância", "valor": "7,32", "unidade": "km"},
                  {"rotulo": "Ritmo", "valor": "6:42", "unidade": "/km"}, {"rotulo": "Tempo", "valor": "49:08"}],
     "musica": {"titulo": "Pump It", "artista": "Black Eyed Peas", "tempo": "2:42", "resta": "-0:51", "progresso": 0.76, "topo": 440},
     "rota_img": "treinos/rotas/2026-10-27.png", "rota_caixa": [0.5, 0.47, 1.0]},
    {"arquivo": "render/treinos/saida/2026-10-27-feed.png", "formato": "feed",
     "foto": "treinos/fotos/2026-10-27.jpg", "palavra": "CORRIDA", "palavra_base": 0.985, "pessoa": {"base": 1.33}, "dados_topo": 128,
     "metricas": ["...mesmas..."],
     "musica": {"titulo": "Pump It", "artista": "Black Eyed Peas", "tempo": "2:42", "resta": "-0:51", "progresso": 0.76,
                "topo": 228, "largura": 0.78, "controles": false},
     "rota_img": "treinos/rotas/2026-10-27.png", "rota_caixa": [0.5, 0.5, 1.0]}]
   ```
   Composição:
   - `pessoa.base` é onde fica a borda de baixo da foto (1 = rente à base; acima de 1 desce e corta o corpo embaixo). Mantenha `largura` 1 para as bordas laterais da foto ficarem fora da tela. Selfie em close: story ~1.08, feed ~1.3. Foto de corpo inteiro: perto de 1.
   - Os rostos ficam entre o cartão de música e a palavra. A cabeça pode cobrir **só a ponta** do cartão (cabelo sobre o canto), nunca o título nem os tempos.
   - No feed, use `"controles": false` no cartão para caber.
   - A palavra **nunca cruza rosto** (boca, queixo, olhos). Ajuste `palavra_base` (story ~0.9, feed ~0.97–0.99).
   - Outros campos: `dados_coluna` (números empilhados), `tamanho_numeros`, `contorno: false`, `foco` (só no modo `"foto"`), `data` (entra antes do @).

8. **Renderizar:** `python render/treino.py render/treinos/<data>.json`. Precisa de `pip install playwright "rembg[cpu]"`; o modelo birefnet-portrait (~1 GB) baixa na primeira vez. Ele recorta melhor que o u2net, que grudava objetos do fundo (capacetes) na cabeça. Fora do Actions: `CHROMIUM_PATH=/opt/pw-browsers/chromium-1243/chrome-linux64/chrome` (confira com `ls /opt/pw-browsers`).

9. **Conferir** cada PNG com Read, como diretor de arte, e refazer até passar:
   - recorte limpo (sem halo nem pedaço do fundo grudado);
   - nenhuma borda reta da foto à mostra;
   - rota visível dos dois lados do corpo;
   - palavra fora dos rostos;
   - cartão legível;
   - números iguais ao report;
   - nada encostando em nada.

10. **Entregar** com SendUserFile (`display: "render"`). Se for feed, sugira uma legenda no formato da marca (1 linha gancho, 2–3 linhas, "Me manda MÉTODO no direct.", 3 hashtags). Se a música não foi informada, diga que o cartão entra quando ele disser qual foi.

11. **Publicar só se ele pedir**: `python render/treino.py <json> --subir` (precisa `SUPABASE_URL` e `SUPABASE_SERVICE_KEY`, `arquivo` em `midia/<data>/...`) e item em `fila.json`.

## Regras

- A foto é do Luan: só o recorte e o desfoque do fundo; nada gerado ou alterado com IA.
- Logo só a oficial (`render/assets/logo-lt.png`). Nunca o logo do Strava ou de outro app.
- Números só do report. Música só se ele disser.
- Vermelho (#E5383B) só na rota, na capa padrão da música e no destaque. Mudanças de estilo vão em `render/treino.html`.
