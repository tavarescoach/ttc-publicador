# TTC Publicador

Robô que publica no Instagram do **Luan Tavares Treinador** nos horários da fila. Roda no GitHub Actions a cada 30 minutos, das 6h às 22h30 (horário de Brasília).

## Como funciona

1. Os arquivos finais (PNG do Canva, MP4 do CapCut) vão para o bucket público `midia` no Supabase, numa pasta por dia: `2026-10-20/`.
2. A fila de publicação fica em `fila.json`: o que publicar, quando, com qual legenda.
3. A cada 30 min o robô publica o que já passou do horário e marca o `status` na fila.
4. Se algo der errado, o GitHub manda e-mail com o motivo, e o item fica com `"status": "erro"` e o campo `erro` explicando.

## Formato de um item da fila

```json
{
  "id": "2026-10-20-carrossel",
  "quando": "2026-10-20T12:00:00-03:00",
  "tipo": "CARROSSEL",
  "arquivos": ["2026-10-20/carrossel-1.png", "2026-10-20/carrossel-2.png"],
  "legenda": "Texto da legenda...",
  "colaboradores": ["usuario_do_studio"]
}
```

| Campo | Obrigatório | Valores |
| --- | --- | --- |
| `id` | sim | qualquer nome único |
| `quando` | sim | data e hora com fuso, ex. `2026-10-20T07:00:00-03:00` |
| `tipo` | sim | `IMAGEM`, `CARROSSEL` (2 a 10 arquivos), `REELS`, `STORY` |
| `arquivos` | sim | caminhos dentro do bucket `midia` |
| `legenda` | não | texto do post (ignorado em story) |
| `capa` | não | só reels: imagem de capa |
| `no_feed` | não | só reels: `false` para não aparecer no grid (padrão `true`) |
| `colaboradores` | não | até 3 @ sem o arroba, para post em collab |
| `status` | automático | `pendente` → `publicado`, `erro` ou `atrasado` |

Itens com mais de 12h de atraso não são publicados (status `atrasado`). Para republicar, ajuste `quando` e apague o `status`.

## Segredos (Settings → Secrets and variables → Actions)

| Segredo | O que é |
| --- | --- |
| `IG_TOKEN` | token gerado no app da Meta (Instagram → Configuração da API com login do Instagram) |
| `IG_USER_ID` | ID da conta do Instagram |
| `MIDIA_BASE` | `https://SEU-PROJETO.supabase.co/storage/v1/object/public/midia` |
| `GH_PAT` | token pessoal do GitHub com permissão de escrever segredos neste repositório (usado para renovar o token do Instagram) |

## Limites

- Stickers de enquete, caixinha, quiz e link não podem ser publicados pela API: esses stories são postados à mão.
- Publicar story pela API exige conta **Comercial**.
- O horário pode atrasar alguns minutos (fila do GitHub).
- O token do Instagram é renovado sozinho nos dias 1 e 15 (workflow "Renovar token").

## Testar sem publicar

```
SIMULAR=1 python publicar.py
```
