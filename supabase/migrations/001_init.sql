-- Enable fuzzy search extension
create extension if not exists pg_trgm;

-- ─── centros ────────────────────────────────────────────────────────────────
create table centros (
  id          uuid primary key default gen_random_uuid(),
  nombre      text not null,
  ciudad      text not null,
  estado_vzla text not null,
  created_at  timestamptz default now()
);

-- ─── personas ───────────────────────────────────────────────────────────────
create table personas (
  id            uuid primary key default gen_random_uuid(),
  nombre        text not null,
  apellido      text not null,
  cedula        text,
  centro        text not null,
  edad_sector   text,
  imagen_url    text,
  estado        text not null default 'pendiente'
                  check (estado in ('pendiente', 'aprobado', 'exportado')),
  voluntario_id uuid references auth.users(id) on delete set null,
  created_at    timestamptz default now()
);

-- Trigram indexes for fuzzy name search
create index personas_nombre_trgm  on personas using gin (nombre  gin_trgm_ops);
create index personas_apellido_trgm on personas using gin (apellido gin_trgm_ops);
create index personas_cedula_idx   on personas (cedula);
create index personas_estado_idx   on personas (estado);

-- ─── Storage bucket ─────────────────────────────────────────────────────────
insert into storage.buckets (id, name, public)
values ('imagenes-listas', 'imagenes-listas', false);

-- ─── Row-level security ─────────────────────────────────────────────────────
alter table personas enable row level security;
alter table centros  enable row level security;

-- Volunteers can read all records
create policy "voluntarios_read_personas"
  on personas for select
  to authenticated
  using (true);

-- Volunteers can insert and update their own submissions
create policy "voluntarios_insert_personas"
  on personas for insert
  to authenticated
  with check (voluntario_id = auth.uid());

create policy "voluntarios_update_personas"
  on personas for update
  to authenticated
  using (voluntario_id = auth.uid());

-- Centros are readable by all authenticated users
create policy "voluntarios_read_centros"
  on centros for select
  to authenticated
  using (true);

-- Service role can do everything (used by FastAPI backend)
create policy "service_all_personas"
  on personas for all
  to service_role
  using (true)
  with check (true);

create policy "service_all_centros"
  on centros for all
  to service_role
  using (true)
  with check (true);

-- Storage: volunteers can upload; service role has full access
create policy "voluntarios_upload_imagenes"
  on storage.objects for insert
  to authenticated
  with check (bucket_id = 'imagenes-listas');

create policy "voluntarios_read_imagenes"
  on storage.objects for select
  to authenticated
  using (bucket_id = 'imagenes-listas');

create policy "service_all_imagenes"
  on storage.objects for all
  to service_role
  using (bucket_id = 'imagenes-listas');
