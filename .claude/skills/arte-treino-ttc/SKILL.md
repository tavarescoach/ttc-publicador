---
name: arte-treino-ttc
description: Use quando o Luan mandar uma foto dele e o report de um treino (print do Garmin, Strava, Apple Fitness, Hevy, planilha ou texto) e quiser a arte pronta para story ou feed do @tavarescoach, com a foto e os números do treino na identidade LT.
---

# Arte de treino — foto + report

O Luan manda duas coisas e recebe a arte pronta, sem perguntas no meio:

1. **A foto dele** (treinando, pós-treino, no TTC).
2. **O report do treino**: print de app (Garmin, Strava, Apple Fitness, Hevy, Whoop), foto da ficha, ou texto.

Entrega: PNG 1080x1920 (story) por padrão. Se ele pedir feed/post, 1080x1350. Se não disser nada, gere os dois.

## Passo a passo

1. **Salvar a foto** em `render/treinos/fotos/<AAAA-MM-DD>.jpg` (se já existir, acrescente `-2`, `-3`). Abra a foto com Read e anote onde está o rosto/corpo: vira o campo `foco` (`object-position`, ex. `"50% 25%"` com o rosto no alto). A parte de baixo da arte (~45%) fica coberta pelos números; o rosto não pode ficar ali.

2. **Ler o report.** Abra o print com Read e transcreva todos os números que aparecem. Não invente, não arredonde para melhor, não converta unidade sem dizer. Se um número estiver ilegível, deixe-o de fora.

3. **Escolher 3 a 6 métricas** (o ideal é 4 ou 6, que fecham a grade). Prioridade:
   - Corrida/bike: distância, pace ou velocidade, tempo, FC média, desnível, calorias.
   - Musculação: duração, volume total (kg), séries, exercício principal com a carga (ex. "Agachamento 140 kg"), PR.
   - Condicionamento: duração, FC média/máx, tempo em zona, calorias, esforço/strain.
   Marque `"destaque": true` em no máximo uma métrica: a que conta a história do dia (um PR, a maior carga, o pace mais rápido).
   Rótulos curtos em português: Duração, Distância, Pace, FC média, Volume, Séries, Calorias, Carga.

4. **Escrever o texto** seguindo `.claude/skills/copy-social-ttc/SKILL.md` e `diretrizes/marca.md`:
   - `rotulo`: o tipo do treino em 2 a 4 palavras ("Treino de inferiores", "Corrida longa").
   - `titulo`: até 6 palavras, um fato do treino, com `**negrito**` (vermelho) em 1 a 3 palavras. Ex.: "Agachamento com **carga nova**", "10 km em **ritmo controlado**".
   - `frase` (opcional): uma linha de Causa no tom da marca, ligando o número a método. Deixe de fora se não houver nada de verdade para dizer.
   - Nada de "bora", "monstro", "shape", "foco força e fé", emoji, CAPS ou travessão.

5. **Montar o JSON** em `render/treinos/<AAAA-MM-DD>.json`:
   ```json
   [
     {"arquivo": "midia/2026-10-27/treino-story.png", "formato": "story",
      "foto": "treinos/fotos/2026-10-27.jpg", "foco": "50% 25%", "data": "27 out 2026",
      "rotulo": "Treino de inferiores", "titulo": "Agachamento com **carga nova**",
      "metricas": [
        {"rotulo": "Duração", "valor": "64", "unidade": "min"},
        {"rotulo": "Volume", "valor": "12.480", "unidade": "kg"},
        {"rotulo": "Séries", "valor": "22"},
        {"rotulo": "Agachamento", "valor": "140", "unidade": "kg", "destaque": true}
      ],
      "frase": "Carga sobe quando a técnica para de oscilar."},
     {"arquivo": "midia/2026-10-27/treino-feed.png", "formato": "feed", "...": "mesmos campos"}
   ]
   ```
   `foto` é relativo a `render/`. `colunas` é opcional (padrão: 2 para 4 métricas, senão 3).

6. **Renderizar:** `python render/treino.py render/treinos/<data>.json`
   Fora do GitHub Actions, se o Playwright do Python não achar o navegador, aponte para o Chromium já instalado: `CHROMIUM_PATH=/opt/pw-browsers/chromium-1243/chrome-linux64/chrome` (confira a pasta com `ls /opt/pw-browsers`). Se faltar o pacote: `pip install playwright`.

7. **Conferir** cada PNG com Read antes de entregar: rosto visível e fora da área dos números, texto sem quebra estranha, números iguais ao report, nada cortado. Se o rosto ficou coberto, ajuste `foco`; se o título quebrou em 3+ linhas, encurte. Renderize de novo.

8. **Entregar** com SendUserFile (`display: "render"`), com uma linha dizendo quais métricas entraram e qual foi o destaque. Junto, sugira uma legenda curta (só se for para feed) no formato da marca: 1 linha gancho, 2–3 linhas, CTA "Me manda MÉTODO no direct.", 3 hashtags.

9. **Publicar só se ele pedir.** Aí: commit da foto, do JSON e do PNG, `python render/treino.py <json> --subir` (precisa `SUPABASE_URL` e `SUPABASE_SERVICE_KEY`) e item novo em `fila.json` (`tipo` `STORY` ou `IMAGEM`).

## Regras

- A foto é do Luan: não recorte o rosto, não aplique filtro, não gere nem altere a imagem com IA.
- Logo só a oficial (`render/assets/logo-lt.png`), que o template já coloca.
- Números vêm do report e de mais lugar nenhum.
- Visual: fundo #050A16, texto #F8FAFC, vermelho #C1121F/#E5383B só no destaque. O layout está em `render/treino.html`; mudanças de estilo vão lá, não em arte avulsa.
