---
name: arte-treino-ttc
description: Use quando o Luan mandar uma foto dele e o report de um treino (print do Strava, Garmin, Apple Fitness, Hevy, planilha ou texto) e quiser a arte pronta para story ou feed do @tavarescoach, no estilo "pop-out" do story do Strava (palavra gigante e rota atrás dele, números pequenos no alto), na identidade LT.
---

# Arte de treino: foto + report

O Luan manda duas coisas e recebe a arte pronta, sem perguntas no meio:

1. **A foto dele** (treinando, pós-treino, no TTC). Funciona melhor com corpo inteiro ou da cintura para cima, com céu ou parede limpa acima da cabeça.
2. **O report do treino**: print de app (Strava, Garmin, Apple Fitness, Hevy, Whoop), foto da ficha, ou texto.

Entrega: PNG 1080x1920 (story) por padrão. Se ele pedir feed/post, 1080x1350. Se não disser nada, gere os dois.

## O estilo (referência: reel de @maluizamelo, "Strava pop-out")

Camadas, de trás para a frente:
1. A foto em tela cheia.
2. Uma **palavra gigante** em branco, de ponta a ponta, perto da base (no reel é "STRAVA"; aqui é o tipo do treino: CORRIDA, PERNAS, COSTAS, TREINO, TTC).
3. A **rota** em linha vermelha grossa (só corrida/bike/caminhada com mapa no report).
4. **O Luan recortado**, por cima da palavra e da rota: ele parece sair da arte. O recorte é automático (rembg).
5. Os **números pequenos e centralizados**, rótulo em cima do valor (Distância / Pace / Tempo), no espaço livre acima da cabeça. A logo LT, a data e o rodapé @tavarescoach.

O layout está em `render/treino.html`; o render e o recorte em `render/treino.py`.

## Passo a passo

1. **Salvar a foto** em `render/treinos/fotos/<AAAA-MM-DD>.jpg` (se já existir, acrescente `-2`, `-3`). Abra a foto com Read e anote onde estão a cabeça e os pés: isso define `foco` (`object-position`, ex. `"50% 40%"`), `dados_topo` e `palavra_base`.

2. **Ler o report.** O caso mais comum é o **sticker do Strava** (PNG transparente de 1080x1920 que o app exporta para o story): os números e a logo vêm em **branco**, invisíveis numa prévia em fundo branco, e só a rota laranja aparece. Antes de concluir que não há números, componha o PNG sobre um fundo escuro (PIL: `Image.new("RGBA", im.size, (20, 30, 50, 255))` + `alpha_composite`) e leia de novo. Para os outros reports, abra o print com Read e transcreva todos os números que aparecem. Não invente, não arredonde para melhor, não converta unidade sem dizer. Número ilegível fica de fora.

3. **Escolher 3 métricas** (no máximo 4). Prioridade:
   - Corrida/bike: Distância, Pace (ou Velocidade), Tempo. Depois FC média, Desnível.
   - Musculação: Duração, Volume (kg), o exercício principal com a carga (ex. "Agachamento" 140 kg). Depois Séries, PR.
   - Condicionamento: Duração, FC média, Calorias ou Strain.
   `"destaque": true` (vermelho) em no máximo uma, e só se houver um PR ou um recorde de verdade.

4. **Rota** (opcional): se o report é o sticker do Strava, salve-o em `render/treinos/rotas/<data>.png` e use `"rota_img"`: o script pega só o traçado laranja (descarta números e logo), pinta no vermelho da marca e põe na `rota_caixa` `[centro x, centro y, largura]` (frações da arte). Posicione a rota para passar **atrás das cabeças ou do corpo**, com as pontas à mostra: é isso que dá o efeito do reel. Se o report é outro print com mapa, olhe o traçado e escreva de 8 a 20 pontos `[x, y]` de 0 a 1 que reproduzam a forma, espalhada pela metade de baixo da arte (y entre 0,45 e 0,85), larga o bastante para passar atrás do corpo dele. Sem mapa, sem rota.

5. **Palavra**: uma palavra só, curta, do treino (CORRIDA, PERNAS, PEITO, COSTAS, TREINO) ou TTC. Ela vira texto de tela, então segue `.claude/skills/copy-social-ttc/SKILL.md` e `diretrizes/marca.md`: nada de "BORA", "MONSTRO", "SHAPE".

6. **Montar o JSON** em `render/treinos/<AAAA-MM-DD>.json`:
   ```json
   [
     {"arquivo": "midia/2026-10-27/treino-story.png", "formato": "story",
      "foto": "treinos/fotos/2026-10-27.jpg", "foco": "50% 40%", "data": "27 out 2026",
      "palavra": "CORRIDA", "palavra_base": 0.85, "dados_topo": 340,
      "metricas": [
        {"rotulo": "Distância", "valor": "6,51", "unidade": "km"},
        {"rotulo": "Pace", "valor": "6:01", "unidade": "/km"},
        {"rotulo": "Tempo", "valor": "39m 13s"}
      ],
      "rota": [[0.1, 0.6], [0.3, 0.55], [0.5, 0.6], [0.7, 0.52], [0.9, 0.58], [0.85, 0.7]]},
     {"arquivo": "midia/2026-10-27/treino-feed.png", "formato": "feed", "...": "mesmos campos"}
   ]
   ```
   Campos: `foto` é relativo a `render/`. `palavra_base` é onde a base da palavra assenta (fração da altura; padrão 0,85 no story, 0,93 no feed); `"palavra": ""` tira a palavra. `dados_topo` é o topo dos números em px (padrão 340 no story, 150 no feed). `"lado_a_lado": true` põe os números em linha, bom quando há pouco espaço acima da cabeça. `"dados_lado": "esquerda"` alinha os números à esquerda, para fotos em close com o rosto no centro ou à direita (aí o vão livre costuma ser o canto de cima à esquerda, abaixo da logo). `recorte` só se quiser usar outro PNG; senão é gerado e guardado como `<foto>-recorte.png`.

7. **Renderizar:** `python render/treino.py render/treinos/<data>.json`
   Precisa de `pip install playwright "rembg[cpu]"` (o modelo de recorte do rembg, birefnet-portrait, ~1 GB, baixa na primeira vez). Fora do GitHub Actions, se o Playwright do Python não achar o navegador, aponte para o Chromium já instalado: `CHROMIUM_PATH=/opt/pw-browsers/chromium-1243/chrome-linux64/chrome` (confira a pasta com `ls /opt/pw-browsers`).

8. **Conferir** cada PNG com Read antes de entregar:
   - **Números fora do rosto.** Se caíram na cabeça, mude `dados_topo` (para cima do cabelo, ou para um vão ao lado do corpo) ou use `lado_a_lado`.
   - **Palavra legível.** O corpo deve cobrir no máximo um terço dela (no reel, só os pés cobrem). Se sumiu atrás do tronco, baixe `palavra_base` ou ajuste `foco`.
   - **Recorte limpo**: sem halo e sem pedaço do fundo grudado. Se o recorte falhou (fundo muito parecido com a roupa), use `"palavra": ""` e sem rota, e avise o Luan.
   - **Rota à mostra.** Se ela sumiu atrás do corpo, mova a `rota_caixa` para um vão do fundo ou aumente a largura. Em selfie ou close, o story (9:16) corta a foto dos lados e as cabeças tomam a largura: o feed costuma ficar melhor. Diga isso ao Luan na entrega.
   - Números iguais ao report, nada cortado, rodapé livre.
   Ajuste e renderize de novo.

9. **Entregar** com SendUserFile (`display: "render"`), com uma linha dizendo quais métricas entraram. Se for feed, sugira uma legenda no formato da marca: 1 linha gancho, 2–3 linhas, CTA "Me manda MÉTODO no direct.", 3 hashtags. Música e stickers ele põe no app.

10. **Publicar só se ele pedir.** Aí: commit da foto, do recorte, do JSON e do PNG, `python render/treino.py <json> --subir` (precisa `SUPABASE_URL` e `SUPABASE_SERVICE_KEY`) e item novo em `fila.json` (`tipo` `STORY` ou `IMAGEM`).

## Regras

- A foto é do Luan: só o recorte automático, sem filtro, sem gerar nem alterar a imagem com IA.
- Logo só a oficial (`render/assets/logo-lt.png`), que o template já coloca. Nunca o logo do Strava ou de outro app.
- Números vêm do report e de mais lugar nenhum.
- Vermelho (#E5383B) só na rota e no destaque. Mudanças de estilo vão em `render/treino.html`, não em arte avulsa.
