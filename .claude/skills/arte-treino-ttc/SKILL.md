---
name: arte-treino-ttc
description: Use quando o Luan mandar uma foto dele e o report de um treino (de preferência o sticker do Strava, PNG transparente; ou print do Garmin, Apple Fitness, Hevy, planilha, texto) e quiser a arte pronta para story ou feed, igual ao story "pop-out" do Strava que ele monta à mão no Instagram: foto nítida, números pequenos no alto, rota laranja gigante e logo STRAVA gigante atrás dele, widget de música do iPhone.
---

# Arte de treino: foto + report

O Luan manda a **foto** e o **report** e recebe a arte pronta, sem perguntas no meio. Se ele disser a música (e onde ouviu: "Ouvindo em Tavares Echo Dot"), entra o widget de "tocando agora".

Entrega: story 1080x1920 e feed 1080x1350 (os dois, salvo pedido).

## A referência (o story que o próprio Luan montou)

- **Foto nítida em tela cheia**, com o céu e o ambiente reais. Nada de desfoque nem filtro.
- **Números do Strava pequenos e empilhados** (Distância / Elevação ou Ritmo / Tempo), no céu, longe do rosto. São os do próprio sticker, na tipografia do Strava.
- **Rota laranja Strava (#FD5300) gigante e grossa**, bem maior que a tela, passando **atrás** da cabeça, do braço ou do tronco.
- **Logo STRAVA gigante na base**, sangrando pelas bordas, **atrás** do corpo (braço, toalha ou perna cobrindo parte).
- **Widget "tocando agora" do iPhone**: pequeno, cinza translúcido, música em caixa alta, "Ouvindo em …", onda sonora, controles. Pode ter a mão, o punho ou o cabelo cobrindo **só a borda**.
- **Sem marca LT por cima.** A logo LT e o @ só entram com `"marca": true`.

Camadas (`render/treino.html`): foto > logo STRAVA > rota > widget > o Luan recortado > números.

## Passo a passo

1. **Salvar** a foto em `render/treinos/fotos/<data>.jpg` e o sticker em `render/treinos/rotas/<data>.png`. Essas pastas e as artes ficam fora do git (`.gitignore`): são fotos pessoais.

2. **Ler o report.** No sticker do Strava os números e a logo são **brancos** em fundo transparente: numa prévia em fundo branco só aparece a rota laranja. Componha sobre fundo escuro para ler (PIL: `Image.new("RGBA", im.size, (20, 30, 50, 255))` + `alpha_composite`). Confira se os números da arte batem com o sticker.

3. **Olhar a foto com Read** e mapear o espaço livre: onde está o céu, onde estão a cabeça, os braços e o tronco. Isso decide tudo:
   - **números**: num canto de céu, sem tocar rosto nem braço;
   - **widget**: em outro trecho de céu, de preferência encostando numa borda do corpo (o punho, o cabelo);
   - **rota**: passando atrás do corpo, com as duas pontas ou um lado bem à mostra;
   - **logo**: na base, atrás do corpo.
   Sem céu (selfie em close, ambiente fechado), o efeito fica escondido. Faça mesmo assim e diga ao Luan que, para esse estilo, a foto precisa ter céu ou parede limpa em volta dele.

4. **Montar o JSON** em `render/treinos/<data>.json`. Exemplo real (foto na praia, braços para cima, céu no alto):
   ```json
   [{"arquivo": "render/treinos/saida/<data>-story.png", "formato": "story",
     "foto": "treinos/fotos/<data>.jpg", "foco": "30% 0%", "sticker": "treinos/rotas/<data>.png",
     "dados_caixa": [0.78, 0.095, 0.17], "rota_caixa": [0.5, 0.45, 1.35], "palavra_caixa": [0.5, 0.985, 1.14],
     "musica": {"titulo": "MEGA FUNK XHAKINHA BROTA", "subtitulo": "Ouvindo em Tavares Echo Dot",
                "tempo": "0:03", "resta": "-2:16", "x": 0.3, "y": 0.128, "largura": 0.4}},
    {"arquivo": "render/treinos/saida/<data>-feed.png", "formato": "feed",
     "foto": "treinos/fotos/<data>.jpg", "sticker": "treinos/rotas/<data>.png",
     "dados_caixa": [0.79, 0.045, 0.15], "rota_caixa": [0.5, 0.45, 1.35], "palavra_caixa": [0.5, 0.99, 1.14],
     "musica": {"...": "...", "x": 0.28, "y": 0.115, "largura": 0.38}}]
   ```
   Campos:
   - `sticker` é separado sozinho em números, rota e logo (branco acima e abaixo do traçado laranja). Rota e logo são ampliadas com a borda nítida. Atividade sem mapa (esteira, bike indoor) também funciona: sem rota, números e logo são separados pelo vão entre eles.
   - As caixas são frações da arte:
     - `dados_caixa` = [centro x, topo, largura];
     - `rota_caixa` = [centro x, centro y, largura];
     - `palavra_caixa` = [centro x, base, largura].
   - A largura pode passar de 1 para sangrar.
   - `foco` é o `object-position` da foto: no story, que corta os lados, use-o para centralizar o Luan.
   - `musica.largura` é a largura do widget (~0.4). `x` e `y` são o centro dele.
   - Sem sticker:
     - os números vão em `metricas` [{"rotulo", "valor", "unidade"}];
     - a palavra vai em `palavra` (texto);
     - a rota vai em `rota` (pontos 0-1, no laranja do Strava, ou na cor de `cor_rota`) ou em `rota_img` (PNG já pronto, usado como está).
   - `dados_sticker: false` e `logo_sticker: false` descartam essas peças do sticker.
   - `fundo: "desfoque"` (foto desfocada, com o Luan reduzido via `pessoa`) existe para fotos sem nenhum respiro. Não é o padrão.

5. **Renderizar:** `python render/treino.py render/treinos/<data>.json`.
   - Precisa de `pip install playwright "rembg[cpu]"`. O modelo de recorte birefnet-portrait (~1 GB) baixa na primeira vez; ele não gruda objetos do fundo na cabeça, como o u2net fazia.
   - Fora do Actions: `CHROMIUM_PATH=/opt/pw-browsers/chromium-1243/chrome-linux64/chrome` (confira com `ls /opt/pw-browsers`).

6. **Conferir** cada PNG com Read, como diretor de arte. Refaça até passar:
   - números no céu, sem encostar no corpo nem no widget;
   - widget inteiro legível (título, onda, botões), com no máximo uma borda coberta;
   - rota visível atrás do corpo;
   - logo gigante na base, parte atrás do corpo, sem cobrir rosto;
   - recorte sem halo;
   - números iguais ao sticker.
   Para conferir detalhes, recorte um trecho da arte e olhe ampliado.

7. **Entregar** com SendUserFile (`display: "render"`). Para o feed, sugira uma legenda (1 linha gancho, 2–3 linhas, "Me manda MÉTODO no direct.", 3 hashtags).

8. **Publicar só se ele pedir**: `python render/treino.py <json> --subir` (precisa `SUPABASE_URL` e `SUPABASE_SERVICE_KEY`, `arquivo` em `midia/<data>/...`) e item em `fila.json`.

## Regras

- A foto é do Luan: só o recorte para as camadas; nada gerado ou alterado com IA.
- Números só do report. Música só se ele disser qual.
- As peças do Strava (números, rota, logo) vêm do sticker que ele exportou. Não redesenhe a logo do Strava.
