import os

from dotenv import load_dotenv

# Load .env for local dev. No-op in production (Railway/Vercel set real env vars).
# Must run before importing routers, since services read keys at import time.
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.ratelimit import limiter
from backend.routers import ocr

app = FastAPI(title="Listas Venezuela API", version="0.1.0")

# Rate limiting (protects the paid /upload endpoint from abuse).
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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


@app.get("/healthz")
def health():
    return {"status": "ok"}
