---
name: auditoria-instagram-ttc
description: Use para analisar, auditar ou reanalisar o desempenho do Instagram @tavarescoach (alcance, arte, copy, horários, formatos, público) e transformar o diagnóstico em estratégia, ou quando o Luan disser que os posts estão indo mal.
---

# Auditoria do Instagram @tavarescoach

Ciclo em quatro passos: **analisar → avaliar → estratégia → reanalisar.** Cada auditoria compara com a anterior; a estratégia só muda o que os números sustentam.

Montada em 06/11/2026 a partir de quatro skills abertas, adaptadas aos dados que o robô já coleta:
- instagram-insights-report (Two Minute Reports): os módulos crescimento, engajamento, conteúdo, reels, público e o plano em três níveis; salvos e compartilhamentos como sinais principais.
- social-media-audit (pm-claude-skills): os 3 melhores e os 3 piores com o porquê, padrão de horário e consistência, comparação com concorrentes.
- social-media-analyzer (claude-skills): validar os dados antes de concluir e marcar cada conclusão como verificada, provável ou suposta.
- social-analytics (clawfu): "o Claude acha o padrão, o Luan decide a prioridade"; comparação com perfis de referência.

## Regras
1. Nunca inventar número. Toda conclusão leva o dado que a sustenta e uma marca: **[verificado]** (sai direto dos dados), **[provável]** (padrão em 5 ou mais posts) ou **[suposto]** (hipótese a testar).
2. Comparar o perfil com ele mesmo antes de comparar com o mercado. As médias de engajamento do mercado (1–3% por alcance) só servem de referência secundária.
3. Separar o que o robô publicou (AUTO) do que o Luan postou no app (MAN). As decisões de automação dependem disso.
4. Separar efeito de post fora da curva do efeito de sistema. Se os 3 melhores posts trouxeram mais de 70% dos seguidores, a média engana; usar a mediana.
5. Posts com menos de 24 h ficam de fora. Insights de stories só existem por 24 h: não entram em auditoria de período.
6. Dado de saúde, aluno ou direct: só números agregados. Nada de texto de mensagem.
7. Não fabricar problema: se um formato vai bem, dizer que vai bem.

## Passo 1 — Analisar (coletar e calcular)
1. Disparar o robô **"Auditoria do Instagram"** (`.github/workflows/auditoria.yml`, `gh api -X POST repos/tavarescoach/ttc-publicador/actions/workflows/auditoria.yml/dispatches -f ref=main`) e esperar terminar. Ele grava `auditoria/dados/ultimo.json`: posts de 60 dias com legenda e insights (alcance, salvos, compartilhamentos, seguidores ganhos, visitas ao perfil, tempo médio de reels), série diária da conta e público (cidade, idade, gênero dos seguidores e do público engajado).
2. Rodar `python auditoria/analisar.py [início] [fim]` → `auditoria/relatorios/AAAA-MM-DD.json`.
3. Olhar as artes: `render/previas/<id>.jpg` dos melhores e dos piores. Ler as legendas inteiras desses posts.
4. Contexto obrigatório: `diretrizes/conteudo.md` (regras em vigor e data da última mudança), relatório anterior em `auditoria/relatorios/`, anúncios no período (perguntar ao Luan se não houver registro).

## Passo 2 — Avaliar (seis dimensões, nota de 0 a 10 cada)
| Dimensão | O que olhar | Sinal de problema |
|---|---|---|
| Crescimento | alcance diário por semana, saldo de seguidores, visitas ao perfil | saldo negativo; 3 posts trazendo mais de 70% dos seguidores |
| Formato | mediana de alcance e salvos+compart. por formato × origem | um formato com 10+ posts e quase zero seguidores |
| Arte | capa com rosto (de quem?), Luan aparece?, densidade de texto, repetição visual | capa sem o Luan nos posts que deveriam converter; mesmo famoso em dois posts do dia |
| Copy | padrão da 1ª linha (abertura), gancho, CTA | um padrão de abertura com mediana abaixo da do perfil |
| Horário e volume | mediana por hora; posts de feed por dia; horários repetidos | mais de 2 posts de feed no mesmo dia competindo; dois posts no mesmo minuto |
| Público e conversão | % Rio (seguidores e engajados), % homens 25–44, MÉTODO, cliques no link | engajados do Rio abaixo de 30%; MÉTODO zerado |

Para cada dimensão: nota, os números, e os 1–2 problemas com a marca de confiança.

## Passo 3 — Estratégia
- **Esta semana:** no máximo 3 ações, cada uma com o número que deve mexer e quanto.
- **Este mês:** testes A/B com uma variável por vez (formato, capa, horário), 4–6 posts por braço.
- **Parar:** o que sai do sistema (formatos ou padrões sem resultado em 10+ posts).
- Escrever as mudanças operacionais em `diretrizes/conteudo.md` só depois que o Luan aprovar.
- Metas sempre contra a mediana da auditoria anterior, não contra o pico.

## Passo 4 — Reanalisar
- A tarefa agendada "Auditoria do Instagram — reanálise" roda a cada 14 dias e repete os passos 1–3.
- A reanálise abre com a tabela **meta × resultado** da auditoria anterior e diz o que manter, o que ajustar e o que abandonar.
- Mínimo de 10 dias de dados depois de uma mudança antes de julgá-la.

## Entrega
- Doc no Claude Docs: Resumo (3 causas com números) → Números da conta → Análise por dimensão → Problemas em ordem → Estratégia → Reanálise.
- Commit de `auditoria/relatorios/AAAA-MM-DD.json` no repositório.
- Mensagem curta ao Luan com o problema nº 1 e a ação nº 1.
