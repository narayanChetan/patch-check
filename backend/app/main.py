from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import CORS_ORIGINS
from app.db.database import Base, SessionLocal, engine
from app.routers import auth, ledger, scan
from app.routers.auth import ensure_default_users

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        ensure_default_users(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="PackCheck API",
    description="Legal Metrology (Packaged Commodities) Rules, 2011 compliance scanner — SIH26034 prototype.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(scan.router)
app.include_router(ledger.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
