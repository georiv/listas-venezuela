-- Fuzzy search function using pg_trgm similarity
create or replace function buscar_personas(query text)
returns setof personas
language sql
stable
as $$
  select *
  from personas
  where
    similarity(nombre || ' ' || apellido, query) > 0.2
    or cedula = query
  order by similarity(nombre || ' ' || apellido, query) desc
  limit 50;
$$;
