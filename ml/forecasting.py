"""
OpsDesk AI — Time-Series Forecasting
=====================================
Predicts future ticket volume to enable proactive staffing and incident prevention.

Uses:
  - Prophet (if installed) for production forecasting
  - Simple exponential smoothing as a lightweight fallback
  - Outputs: hourly/daily forecasts + anomaly flags

Usage:
    python ml/forecasting.py
    # Or import and call forecast_ticket_volume()
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

PROCESSED_DIR = Path("data/processed")
MODELS_DIR = Path("ml/models")


# ── Simple Exponential Smoothing (no-dependency fallback) ─────────────────────

def exponential_smoothing(series: list[float], alpha: float = 0.3) -> list[float]:
    """Single exponential smoothing — O(n), no external deps."""
    if not series:
        return []
    result = [series[0]]
    for x in series[1:]:
        result.append(alpha * x + (1 - alpha) * result[-1])
    return result


def detect_anomalies(series: list[float], window: int = 7, threshold: float = 2.5) -> list[bool]:
    """Flag points more than `threshold` std-devs (or 3x mean) from rolling window."""
    flags = [False] * len(series)
    for i in range(window, len(series)):
        window_vals = series[i - window:i]
        mean = sum(window_vals) / len(window_vals)
        std = (sum((x - mean) ** 2 for x in window_vals) / len(window_vals)) ** 0.5
        val = series[i]
        if std > 0:
            if abs(val - mean) > threshold * std:
                flags[i] = True
        else:
            # Zero variance window — flag if value is significantly different (3× mean or +10)
            if mean > 0 and val > mean * 3:
                flags[i] = True
            elif mean == 0 and val > 10:
                flags[i] = True
    return flags


# ── Prophet wrapper ──────────────────────────────────────────────────────────

def try_prophet_forecast(df_ts: pd.DataFrame, periods: int = 30) -> pd.DataFrame | None:
    """
    Attempt Prophet forecast. Returns None if Prophet not installed.
    df_ts must have columns 'ds' (datetime) and 'y' (ticket count).
    """
    try:
        from prophet import Prophet  # type: ignore
        model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=False,
            changepoint_prior_scale=0.05,
        )
        model.fit(df_ts)
        future = model.make_future_dataframe(periods=periods, freq="D")
        forecast = model.predict(future)
        logger.info(f"  ✓ Prophet forecast complete ({len(forecast)} rows)")
        return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]]
    except ImportError:
        logger.info("  Prophet not installed — using EMA fallback")
        return None
    except Exception as e:
        logger.warning(f"  Prophet error: {e}")
        return None


# ── Main forecasting pipeline ─────────────────────────────────────────────────

def forecast_ticket_volume(periods_days: int = 14) -> dict:
    """
    Load the hourly time-series, aggregate to daily, then forecast.
    Returns a dict with:
      - historical: last 30 days of actuals
      - forecast: next `periods_days` days (with confidence intervals)
      - anomalies: indices of historical anomaly days
      - peak_day: forecasted busiest day
      - recommendation: staffing note
    """
    ts_path = PROCESSED_DIR / "timeseries_hourly.csv"
    if not ts_path.exists():
        logger.warning("  Time-series data not found. Run data_pipeline.py first.")
        return _synthetic_forecast(periods_days)

    df = pd.read_csv(ts_path, parse_dates=["ds"])
    df = df.sort_values("ds")

    # Aggregate to daily
    df["date"] = df["ds"].dt.date
    daily = df.groupby("date")["y"].sum().reset_index()
    daily.columns = ["ds", "y"]
    daily["ds"] = pd.to_datetime(daily["ds"])
    daily = daily.sort_values("ds").tail(90)  # last 90 days

    if len(daily) < 7:
        return _synthetic_forecast(periods_days)

    # Try Prophet first
    forecast_df = try_prophet_forecast(daily, periods=periods_days)

    if forecast_df is not None:
        # Prophet succeeded
        hist = daily.tail(30).copy()
        hist["ds"] = hist["ds"].astype(str)
        future_mask = forecast_df["ds"] > daily["ds"].max()
        fcast = forecast_df[future_mask].copy()
        fcast["ds"] = fcast["ds"].astype(str)

        return {
            "method": "prophet",
            "historical": hist.to_dict("records"),
            "forecast": fcast.rename(columns={
                "yhat": "predicted", "yhat_lower": "lower", "yhat_upper": "upper"
            }).to_dict("records"),
            "anomalies": [],
            "peak_day": str(fcast.loc[fcast["yhat"].idxmax(), "ds"]),
            "recommendation": _staffing_recommendation(fcast["yhat"].max()),
        }

    # EMA fallback
    values = daily["y"].tolist()
    dates = daily["ds"].tolist()

    smoothed = exponential_smoothing(values, alpha=0.3)
    anomaly_flags = detect_anomalies(values, window=7)
    anomaly_dates = [str(dates[i])[:10] for i, f in enumerate(anomaly_flags) if f]

    # Simple linear trend extrapolation
    last_val = smoothed[-1]
    recent_slope = (smoothed[-1] - smoothed[-7]) / 7 if len(smoothed) >= 7 else 0
    last_date = dates[-1] if dates else datetime.utcnow()

    forecast_records = []
    for i in range(1, periods_days + 1):
        pred_day = last_date + timedelta(days=i)
        predicted = max(0, last_val + recent_slope * i)
        # Weekend dip
        if pred_day.weekday() >= 5:
            predicted *= 0.6
        forecast_records.append({
            "ds": str(pred_day)[:10],
            "predicted": round(predicted, 1),
            "lower": round(predicted * 0.75, 1),
            "upper": round(predicted * 1.25, 1),
        })

    hist_30 = [
        {"ds": str(d)[:10], "y": v}
        for d, v in zip(dates[-30:], values[-30:])
    ]

    peak = max(forecast_records, key=lambda r: r["predicted"])

    return {
        "method": "ema_linear",
        "historical": hist_30,
        "forecast": forecast_records,
        "anomalies": anomaly_dates,
        "peak_day": peak["ds"],
        "recommendation": _staffing_recommendation(peak["predicted"]),
    }


def _staffing_recommendation(peak_volume: float) -> str:
    if peak_volume > 100:
        return "🔴 High volume predicted — recommend adding 2 extra agents on peak days"
    elif peak_volume > 50:
        return "🟡 Moderate volume — ensure all agents are available on peak days"
    else:
        return "🟢 Normal volume — standard staffing is sufficient"


def _synthetic_forecast(periods_days: int) -> dict:
    """Return a synthetic forecast when no real data is available."""
    base = datetime.utcnow()
    hist = [
        {"ds": str((base - timedelta(days=30 - i)).date()), "y": int(20 + 10 * np.sin(i / 7))}
        for i in range(30)
    ]
    fcast = [
        {"ds": str((base + timedelta(days=i + 1)).date()),
         "predicted": round(25 + 8 * np.sin((30 + i) / 7), 1),
         "lower": round(18 + 5 * np.sin((30 + i) / 7), 1),
         "upper": round(32 + 11 * np.sin((30 + i) / 7), 1)}
        for i in range(periods_days)
    ]
    return {
        "method": "synthetic",
        "historical": hist,
        "forecast": fcast,
        "anomalies": [],
        "peak_day": fcast[-1]["ds"],
        "recommendation": "🟢 Normal volume — standard staffing is sufficient",
    }


# ── Incident prediction ───────────────────────────────────────────────────────

def predict_incidents(lookback_days: int = 7) -> list[dict]:
    """
    Scan recent ticket patterns for anomalies and auto-generate incident alerts.
    In production, this runs as a scheduled cron job.
    """
    ts_path = PROCESSED_DIR / "timeseries_hourly.csv"
    if not ts_path.exists():
        return []

    df = pd.read_csv(ts_path, parse_dates=["ds"])
    df = df.sort_values("ds").tail(24 * lookback_days)

    hourly = df.set_index("ds")["y"]
    values = hourly.tolist()
    anomalies = detect_anomalies(values, window=6, threshold=2.0)

    incidents = []
    for i, (flag, idx) in enumerate(zip(anomalies, hourly.index)):
        if flag:
            incidents.append({
                "timestamp": str(idx),
                "volume": values[i],
                "severity": "high" if values[i] > 50 else "medium",
                "suggested_action": "Auto-escalate tickets created in this window",
                "auto_ticket": {
                    "subject": f"Automated Incident Alert — Volume spike at {str(idx)[:13]}",
                    "category": "Cloud",
                    "priority": "high",
                    "source": "predictive_ml",
                },
            })

    logger.info(f"  ✓ Detected {len(incidents)} potential incidents from last {lookback_days} days")
    return incidents[:10]  # top 10


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    logger.info("Running time-series forecast...")
    result = forecast_ticket_volume(periods_days=14)
    print(json.dumps({
        "method": result["method"],
        "historical_days": len(result["historical"]),
        "forecast_days": len(result["forecast"]),
        "peak_day": result["peak_day"],
        "recommendation": result["recommendation"],
        "anomalies": result["anomalies"][:3],
    }, indent=2))

    incidents = predict_incidents()
    print(f"\nPredicted incidents: {len(incidents)}")
    for inc in incidents[:3]:
        print(f"  [{inc['severity'].upper()}] {inc['timestamp']} — volume: {inc['volume']}")
