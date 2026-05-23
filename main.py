from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging, os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s %(levelname)-5s [%(name)s] %(message)s",
)
logger = logging.getLogger("aqua_qe")

from persistence.base import build_engine, build_session_factory, create_all_tables, get_session
from api.requirements.router import router as req_router
from functools import partial

_engine = build_engine()
_session_factory = build_session_factory(_engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AQuA-QE iniciando...")
    create_all_tables(_engine)
    logger.info("Banco inicializado.")
    yield
    _engine.dispose()
    logger.info("AQuA-QE encerrado.")


app = FastAPI(
    title="AQuA-QE System",
    description="AI-Native Requirements Engineering & Quality Platform",
    version="0.1.0-mvp",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.dependency_overrides[get_session] = partial(get_session, _session_factory)
app.include_router(req_router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok", "version": app.version}
