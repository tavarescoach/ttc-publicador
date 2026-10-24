-- 001 · Tema editorial e view do calendário
-- Rodar no SQL Editor do Supabase (projeto ttc-midia). Idempotente.

-- 1. Coluna de tema (1 a 2 palavras da lista aprovada em temas-editoriais)
alter table public.conteudos add column if not exists tema text;

-- 2. View usada pelo painel: uma linha por publicação, com sigla e dia pronto
create or replace view public.calendario as
select
  c.id,
  c.data,
  c.quando,
  c.tipo,
  c.pauta,
  c.funil,
  c.etapa,
  c.tema,
  case c.tema
    when 'Treino de força'   then 'FOR'
    when 'Emagrecimento'     then 'EMA'
    when 'Estilo de vida'    then 'EST'
    when 'Esportes'          then 'ESP'
    when 'Famosos'           then 'FAM'
    when 'GLP-1'             then 'GLP'
    when 'Longevidade'       then 'LON'
    when 'Saúde mental'      then 'MEN'
    when 'Tecnologia e dados' then 'WEA'
    else null
  end as sigla,
  (c.tema is null or c.tema not in (
     'Treino de força','Emagrecimento','Estilo de vida','Esportes',
     'Famosos','GLP-1','Longevidade','Saúde mental','Tecnologia e dados')) as fora_da_lista,
  c.media_id,
  c.capa,
  c.link
from public.conteudos c
where c.etapa <> 'cancelado';

comment on view public.calendario is
  'Calendário do painel. fora_da_lista = tema ausente ou fora dos temas aprovados.';
