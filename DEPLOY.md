# Despliegue a producción — Listas Venezuela

MVP abierto (sin login). Backend en Railway, frontend en Vercel, datos en Supabase.

---

## Parte 1 · Credenciales (tú las obtienes)

### 1.1 Supabase
1. Crea un proyecto en https://supabase.com → New project.
2. En el **SQL Editor**, pega y ejecuta, en orden:
   - `supabase/migrations/001_init.sql`
   - `supabase/migrations/002_fuzzy_search.sql`
3. Confirma que se creó el bucket de Storage `imagenes-listas`
   (Storage → debería aparecer; lo crea la migración 001).
4. Copia desde **Project Settings → API**:
   - `SUPABASE_URL`  → "Project URL"
   - `SUPABASE_SERVICE_KEY` → "service_role" secret (⚠️ secreto, solo backend)

### 1.2 Gemini (Google AI Studio)
Gemini hace OCR + estructuración en una sola llamada multimodal
(Flash por defecto, escala a Pro si la calidad es baja).
1. https://aistudio.google.com/apikey → **Create API key**.
2. (Opcional) Tiene **tier gratuito** con límites de uso; sirve para empezar.
   Para volumen alto, activa facturación en el proyecto de Google Cloud asociado.
3. Copia `GEMINI_API_KEY`.

---

## Parte 2 · Subir el código a GitHub (tú)

Aún no es un repo git. Desde `/Users/georgina/Venezuela`:

```bash
git init
git add .
git commit -m "Listas Venezuela: MVP"
# crea el repo en GitHub y luego:
git remote add origin https://github.com/<tu-usuario>/listas-venezuela.git
git branch -M main
git push -u origin main
```

> `.gitignore` ya excluye `.env`, `node_modules/` y `.venv/`. **Nunca subas `.env`.**

---

## Parte 3 · Backend en Railway

1. https://railway.app → New Project → **Deploy from GitHub repo** → elige el repo.
2. **Root Directory:** déjalo en la raíz (`/`). Ya hay `requirements.txt` y `Procfile`
   en la raíz que Railway/Nixpacks detecta automáticamente.
3. En **Variables**, añade:
   ```
   GEMINI_API_KEY       = ...
   SUPABASE_URL         = https://xxxx.supabase.co
   SUPABASE_SERVICE_KEY = ...
   FRONTEND_ORIGIN      = *        (lo ajustamos en la Parte 5)
   ```
   Opcionales para cambiar de modelo:
   `GEMINI_FLASH_MODEL` (def. `gemini-2.5-flash`),
   `GEMINI_PRO_MODEL` (def. `gemini-2.5-pro`).
4. Railway arranca con: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` (Procfile).
5. En **Settings → Networking → Generate Domain** para obtener una URL pública.
6. Verifica: abre `https://<tu-backend>.up.railway.app/healthz` → debe responder
   `{"status":"ok"}`.

Guarda esa URL del backend; la necesitas en la Parte 4.

---

## Parte 4 · Frontend en Vercel

1. https://vercel.com → Add New → Project → importa el mismo repo de GitHub.
2. **Root Directory:** `frontend`  (importante).
3. Framework: Vercel detecta **Nuxt** automáticamente (build `nuxt build`).
4. En **Environment Variables** añade:
   ```
   NUXT_PUBLIC_API_URL = https://<tu-backend>.up.railway.app
   ```
   (Nuxt mapea esta variable a `runtimeConfig.public.apiUrl` automáticamente.)
5. Deploy. Obtendrás una URL tipo `https://listas-venezuela.vercel.app`.

---

## Parte 5 · Conectar CORS y redeploy

1. Vuelve a Railway → Variables → cambia:
   ```
   FRONTEND_ORIGIN = https://listas-venezuela.vercel.app
   ```
   (sin barra final; puedes poner varias separadas por coma).
2. Railway redepliega solo. Sin esto, el navegador bloqueará las llamadas del
   frontend al backend por CORS.

---

## Parte 6 · Prueba de humo en producción

1. Abre la URL de Vercel.
2. Sube una foto real de una lista hospitalaria.
3. Verifica: aparece la tabla editable con los datos extraídos.
4. Corrige algo, exporta el CSV → debe descargar con cabecera exacta
   `nombre,apellido,cedula,centro,edad_sector`.
5. En Supabase → Table Editor → `personas` deberías ver las filas en estado
   `pendiente`.

Si algo falla, revisa los **logs de Railway** (errores de OCR/Claude/Supabase)
y la **consola del navegador** (errores de CORS o de red).

---

## Notas / pendientes conocidos

- **Sin login:** `voluntario_id` se guarda como `null`. Cuando quieras auth,
  hay que cablear Supabase Auth (login.vue, middleware, verificación JWT en
  FastAPI) y volver a enviar `voluntario_id`.
- **imagen_url** apunta al bucket privado; la URL guardada no es accesible
  públicamente todavía. No bloquea el MVP (la tabla no muestra la imagen
  almacenada). Para mostrarla luego: usar signed URLs o bucket público.
- **Costos:** Gemini tiene tier gratuito; pasado el límite cobra por uso
  (~$1 por cada 1.000 fotos con Flash). El fallback a Pro solo se activa en
  páginas difíciles. Vigila el billing si el volumen es alto.
- **Seguridad:** al ser MVP abierto, cualquiera con el link puede subir y
  exportar. Considera un rate limit o auth antes de difundir ampliamente.
```
