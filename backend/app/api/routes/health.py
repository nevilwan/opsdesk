"""Health check endpoints."""

from fastapi import APIRouter
from datetime import datetime
from app.services.ml_service import ml_service

router = APIRouter()


@router.get("/health")
async def health():
    models = {
        "classifier": ml_service.classifier is not None,
        "routing_model": ml_service.routing_model is not None,
        "resolution_predictor": ml_service.resolution_predictor is not None,
        "sla_classifier": ml_service.sla_classifier is not None,
        "knowledge_base": ml_service.knowledge_base is not None,
    }
    all_ok = all(models.values())
    return {
        "status": "healthy" if all_ok else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "models": models,
        "ml_loaded": ml_service._loaded,
    }


@router.get("/health/ready")
async def readiness():
    return {"ready": True}


@router.get("/health/live")
async def liveness():
    return {"live": True}
