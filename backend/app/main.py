"""RiskLens AI — FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.config import settings
from app.database import init_db
from app.routers import transactions, dashboard, investigations, simulator, model

logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create DB tables, ensure model is trained."""
    logger.info("Starting RiskLens AI backend")
    init_db()
    # Ensure model exists at startup
    try:
        from app.ml.predictor import get_best_model
        get_best_model()
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.warning("Model not ready at startup: %s — will train on first request", e)
    yield
    logger.info("Shutting down RiskLens AI backend")


app = FastAPI(
    title="RiskLens AI",
    description=(
        "Explainable Payment Fraud Risk Management System — "
        "Razorpay AI Buildathon, AI Risk Manager track. "
        "DEMO ONLY: Do not use for real financial decisions."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Security middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(transactions.router)
app.include_router(dashboard.router)
app.include_router(investigations.router)
app.include_router(simulator.router)
app.include_router(model.router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "RiskLens AI",
        "version": "1.0.0",
        "disclaimer": "DEMO system — not for real financial decisions",
    }


@app.get("/")
def root():
    return {
        "message": "RiskLens AI API is running",
        "docs": "/docs",
        "health": "/health",
    }
