from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import auth, affiliate, admin, webhook
from app.config import settings

app = FastAPI(title="WinWin Law MLM API", version="1.0.0")

_cors_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]
_frontend_url = settings.FRONTEND_URL.rstrip("/")
if _frontend_url and _frontend_url not in _cors_origins:
    _cors_origins.append(_frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(affiliate.router)
app.include_router(admin.router)
app.include_router(webhook.router)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok", "service": "winwinlaw-mlm"}
