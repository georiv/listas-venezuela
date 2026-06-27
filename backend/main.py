import os

from dotenv import load_dotenv

# Load .env for local dev. No-op in production (Railway/Vercel set real env vars).
# Must run before importing routers, since services read keys at import time.
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import ocr, records

app = FastAPI(title="Listas Venezuela API", version="0.1.0")

# Comma-separated list of allowed origins, e.g.
#   FRONTEND_ORIGIN="https://listas-venezuela.vercel.app,http://localhost:3000"
# Defaults to "*" for local dev. In production set this to your Vercel URL.
_origins = os.environ.get("FRONTEND_ORIGIN", "*")
allow_origins = [o.strip() for o in _origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    # No cookies are used (token-less open MVP), so credentials stay off.
    # This is what allows "*" to be valid.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ocr.router)
app.include_router(records.router)


@app.get("/healthz")
def health():
    return {"status": "ok"}
