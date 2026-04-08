"""Forecasting API — exposes time-series predictions and incident alerts."""

from fastapi import APIRouter, Query
import sys
import os

router = APIRouter()

# Add project root to path so ml module is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))


@router.get("/forecast")
async def get_volume_forecast(days: int = Query(14, ge=3, le=90)):
    """
    Predict ticket volume for the next N days.
    Uses Prophet if installed, otherwise EMA with linear trend.
    """
    try:
        from ml.forecasting import forecast_ticket_volume
        return forecast_ticket_volume(periods_days=days)
    except Exception as e:
        return {"error": str(e), "method": "unavailable"}


@router.get("/incidents")
async def get_predicted_incidents(lookback_days: int = Query(7, ge=1, le=30)):
    """
    Detect anomalous ticket volume spikes from the past N days.
    Returns suggested auto-created incident tickets.
    """
    try:
        from ml.forecasting import predict_incidents
        return {"incidents": predict_incidents(lookback_days=lookback_days)}
    except Exception as e:
        return {"error": str(e), "incidents": []}
