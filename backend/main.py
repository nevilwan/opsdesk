"""
OpsDesk AI — FastAPI Backend
Production-grade IT helpdesk automation platform.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import logging
import time

from app.core.config import settings
from app.api.routes import tickets, analytics, agents, chatbot, knowledge, health, auth, webhooks, forecasting

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OpsDesk AI",
    description="AI-Powered IT Operations Platform — Production Grade",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ── Middleware ─────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def add_request_id_and_timing(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000, 2)
    response.headers["X-Response-Time"] = f"{duration}ms"
    return response


# ── Routes ─────────────────────────────────────────────────────────────────────

app.include_router(health.router,     prefix="/api",          tags=["Health"])
app.include_router(auth.router,       prefix="/api/auth",     tags=["Auth"])
app.include_router(tickets.router,    prefix="/api/tickets",  tags=["Tickets"])
app.include_router(analytics.router,  prefix="/api/analytics",tags=["Analytics"])
app.include_router(agents.router,     prefix="/api/agents",   tags=["Agents"])
app.include_router(chatbot.router,    prefix="/api/chatbot",  tags=["Chatbot"])
app.include_router(knowledge.router,  prefix="/api/knowledge",tags=["Knowledge Base"])
app.include_router(webhooks.router,   prefix="/api/webhooks",  tags=["Webhooks"])
app.include_router(forecasting.router,prefix="/api/forecasting",tags=["Forecasting"])


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.on_event("startup")
async def startup():
    logger.info("OpsDesk AI starting up...")
    from app.services.ml_service import ml_service
    ml_service.load_models()
    logger.info("ML models loaded.")


@app.on_event("shutdown")
async def shutdown():
    logger.info("OpsDesk AI shutting down.")
