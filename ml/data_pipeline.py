"""
OpsDesk AI - Data Pipeline
==========================
Ingests, cleans, and preprocesses all ticket datasets for ML training.
Handles 6 dataset sources with different schemas, normalizes to a unified format.
"""

import os
import re
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from sklearn.preprocessing import LabelEncoder
import pickle
import json

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
MODELS_DIR = Path("ml/models")

for d in [RAW_DIR, PROCESSED_DIR, MODELS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Canonical schema ──────────────────────────────────────────────────────────
CANONICAL_COLS = [
    "ticket_id", "subject", "description", "category", "priority",
    "status", "created_at", "resolved_at", "resolution_hours",
    "assigned_agent", "department", "resolution_notes",
    "satisfaction_score", "first_response_hours", "escalated",
    "sla_breached", "tenant_id", "language", "source_dataset"
]

CATEGORY_MAP = {
    "network": "Network", "networking": "Network", "connectivity": "Network",
    "hardware": "Hardware", "hw": "Hardware", "device": "Hardware",
    "software": "Software", "sw": "Software", "application": "Software", "app": "Software",
    "security": "Security", "infosec": "Security", "cyber": "Security",
    "database": "Database", "db": "Database", "data": "Database",
    "cloud": "Cloud", "aws": "Cloud", "azure": "Cloud", "gcp": "Cloud",
    "email": "Email", "mail": "Email", "outlook": "Email",
    "vpn": "VPN", "remote access": "VPN",
    "printing": "Printing", "printer": "Printing",
    "access management": "Access Management", "iam": "Access Management",
    "access": "Access Management",
}

PRIORITY_MAP = {
    "low": "Low", "1": "Low", "p4": "Low",
    "medium": "Medium", "normal": "Medium", "2": "Medium", "p3": "Medium",
    "high": "High", "urgent": "High", "3": "High", "p2": "High",
    "critical": "Critical", "emergency": "Critical", "4": "Critical", "p1": "Critical",
}


# ── Text cleaning ─────────────────────────────────────────────────────────────
STOPWORDS = {
    "the", "a", "an", "is", "it", "in", "on", "at", "to", "for",
    "of", "and", "or", "but", "not", "with", "this", "that", "be",
    "as", "by", "from", "are", "was", "were", "has", "have", "had",
    "do", "does", "did", "will", "would", "could", "should", "may",
    "might", "can", "i", "we", "you", "he", "she", "they", "my",
    "your", "our", "their", "its", "user", "please", "help",
}


def clean_text(text: str) -> str:
    """Lowercase, remove special chars, remove stopwords."""
    if not isinstance(text, str) or not text.strip():
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    tokens = [t for t in text.split() if t not in STOPWORDS and len(t) > 1]
    return " ".join(tokens)


def normalize_category(val: str) -> str:
    if not isinstance(val, str):
        return "Software"
    key = val.lower().strip()
    return CATEGORY_MAP.get(key, val.title() if val else "Software")


def normalize_priority(val) -> str:
    if not isinstance(val, str):
        val = str(val)
    key = val.lower().strip()
    return PRIORITY_MAP.get(key, "Medium")


def parse_datetime(val) -> pd.Timestamp | None:
    if pd.isna(val) or val == "" or val is None:
        return None
    try:
        return pd.to_datetime(val)
    except Exception:
        return None


# ── Dataset loaders ───────────────────────────────────────────────────────────

def load_main_classifier_dataset() -> pd.DataFrame:
    """Dataset 1: IT Support Ticket Topic Classifier (all_tickets_processed_improved_v3.csv)"""
    fp = RAW_DIR / "all_tickets_processed_improved_v3.csv"
    if not fp.exists():
        logger.warning(f"  Missing: {fp}")
        return pd.DataFrame()
    df = pd.read_csv(fp)
    logger.info(f"  Loaded {len(df)} rows from {fp.name}")
    df["source_dataset"] = "classifier_v3"
    df["language"] = df.get("language", "en")
    return df


def load_ticketing_2024_dataset() -> pd.DataFrame:
    """Dataset 2: Support Ticketing 2024 (Jan-Jul)"""
    fp = RAW_DIR / "Support_Ticketing_Cleaned_Jan-Jul_2024.csv"
    if not fp.exists():
        logger.warning(f"  Missing: {fp}")
        return pd.DataFrame()
    df = pd.read_csv(fp)
    logger.info(f"  Loaded {len(df)} rows from {fp.name}")
    df["source_dataset"] = "ticketing_2024"
    df["language"] = df.get("language", "en")
    return df


def load_multilang_dataset() -> pd.DataFrame:
    """Dataset 3: Multi-language customer support tickets"""
    fp = RAW_DIR / "dataset-tickets-multi-lang-4-20k.csv"
    if not fp.exists():
        logger.warning(f"  Missing: {fp}")
        return pd.DataFrame()
    df = pd.read_csv(fp)
    logger.info(f"  Loaded {len(df)} rows from {fp.name}")
    df["source_dataset"] = "multilang"
    # Merge subject + body into description
    if "body" in df.columns and "subject" in df.columns:
        df["description"] = df["subject"].fillna("") + " " + df["body"].fillna("")
    return df


def load_resolution_dataset() -> pd.DataFrame:
    """Dataset 4: Resolution time dataset"""
    fp = RAW_DIR / "customer_support_tickets_resolution.csv"
    if not fp.exists():
        logger.warning(f"  Missing: {fp}")
        return pd.DataFrame()
    df = pd.read_csv(fp)
    logger.info(f"  Loaded {len(df)} rows from {fp.name}")
    df["source_dataset"] = "resolution"
    df["language"] = df.get("language", "en")
    return df


def load_mendeley_dataset() -> pd.DataFrame:
    """Dataset 5: Mendeley Help Desk Tickets (time-series)"""
    fp = RAW_DIR / "helpdesk_tickets_mendeley.csv"
    if not fp.exists():
        logger.warning(f"  Missing: {fp}")
        return pd.DataFrame()
    df = pd.read_csv(fp)
    logger.info(f"  Loaded {len(df)} rows from {fp.name}")
    df["source_dataset"] = "mendeley"
    df["language"] = "en"
    return df


def load_synthetic_dataset() -> pd.DataFrame:
    """Dataset 6: Synthetic IT Helpdesk tickets (fallback/augmentation)"""
    fp = RAW_DIR / "IT_helpdesk_synthetic_tickets.csv"
    if not fp.exists():
        logger.warning(f"  Missing: {fp}")
        return pd.DataFrame()
    df = pd.read_csv(fp)
    logger.info(f"  Loaded {len(df)} rows from {fp.name}")
    df["source_dataset"] = "synthetic"
    df["language"] = df.get("language", "en")
    return df


# ── Canonicalization ──────────────────────────────────────────────────────────

def canonicalize(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """Map any dataframe to canonical schema."""
    if df.empty:
        return pd.DataFrame(columns=CANONICAL_COLS)

    result = pd.DataFrame()
    cols = df.columns.str.lower().tolist()
    col_map = dict(zip(cols, df.columns))  # lower -> original

    def get_col(*names):
        for n in names:
            if n in col_map:
                return df[col_map[n]]
        return pd.Series([""] * len(df))

    result["ticket_id"] = get_col("ticket_id", "id", "ticketid")
    result["subject"] = get_col("subject", "title", "summary", "issue")
    result["description"] = get_col("description", "body", "details", "text", "message")
    result["category"] = get_col("category", "type", "topic", "issue_type").apply(normalize_category)
    result["priority"] = get_col("priority", "severity", "urgency").apply(normalize_priority)
    result["status"] = get_col("status", "state", "ticket_status").fillna("Open")
    result["created_at"] = get_col("created_at", "created", "open_date", "date").apply(parse_datetime)
    result["resolved_at"] = get_col("resolved_at", "resolved", "close_date", "resolution_date").apply(parse_datetime)
    result["resolution_hours"] = pd.to_numeric(get_col("resolution_hours", "resolution_time", "time_to_resolve"), errors="coerce")
    result["assigned_agent"] = get_col("assigned_agent", "agent", "assignee", "owner")
    result["department"] = get_col("department", "dept", "team", "group")
    result["resolution_notes"] = get_col("resolution_notes", "resolution", "solution", "notes")
    result["satisfaction_score"] = pd.to_numeric(get_col("satisfaction_score", "csat", "rating", "score"), errors="coerce")
    result["first_response_hours"] = pd.to_numeric(get_col("first_response_hours", "first_response", "response_time"), errors="coerce")
    result["escalated"] = get_col("escalated", "is_escalated").map(lambda x: bool(x) if x != "" else False)
    result["sla_breached"] = get_col("sla_breached", "sla_violation", "breach").map(lambda x: bool(x) if x != "" else False)
    result["tenant_id"] = get_col("tenant_id", "org_id", "organization", "company").fillna("default")
    result["language"] = get_col("language", "lang", "locale").fillna("en")
    result["source_dataset"] = source

    return result


# ── Feature engineering ───────────────────────────────────────────────────────

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create ML-ready features from cleaned canonical data."""
    df = df.copy()

    # Text features
    df["text_combined"] = (
        df["subject"].fillna("") + " " +
        df["description"].fillna("") + " " +
        df["resolution_notes"].fillna("")
    )
    df["text_clean"] = df["text_combined"].apply(clean_text)
    df["text_length"] = df["text_combined"].str.len().fillna(0).astype(int)
    df["word_count"] = df["text_clean"].str.split().str.len().fillna(0).astype(int)

    # Time features
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["hour_of_day"] = df["created_at"].dt.hour.fillna(-1).astype(int)
    df["day_of_week"] = df["created_at"].dt.dayofweek.fillna(-1).astype(int)
    df["month"] = df["created_at"].dt.month.fillna(-1).astype(int)
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["is_business_hours"] = ((df["hour_of_day"] >= 8) & (df["hour_of_day"] <= 18)).astype(int)

    # Resolution features
    df["is_resolved"] = df["status"].isin(["Resolved", "Closed"]).astype(int)
    df["resolution_hours"] = df["resolution_hours"].fillna(
        df.groupby("category")["resolution_hours"].transform("median")
    ).fillna(24)

    # Priority encoding
    priority_order = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
    df["priority_numeric"] = df["priority"].map(priority_order).fillna(2).astype(int)

    # SLA target hours by priority
    sla_hours = {"Low": 72, "Medium": 24, "High": 8, "Critical": 2}
    df["sla_target_hours"] = df["priority"].map(sla_hours).fillna(24)
    df["sla_risk"] = (df["resolution_hours"] > df["sla_target_hours"]).astype(int)

    # Agent workload (tickets per agent in dataset)
    if "assigned_agent" in df.columns:
        workload = df["assigned_agent"].value_counts().to_dict()
        df["agent_workload"] = df["assigned_agent"].map(workload).fillna(0).astype(int)

    return df


# ── Label encoding ────────────────────────────────────────────────────────────

def encode_labels(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Encode categorical labels, save encoders for inference."""
    encoders = {}
    label_cols = ["category", "priority", "status", "department", "language"]

    for col in label_cols:
        if col in df.columns:
            le = LabelEncoder()
            df[f"{col}_encoded"] = le.fit_transform(df[col].astype(str))
            encoders[col] = le

    # Save encoders
    encoder_path = MODELS_DIR / "label_encoders.pkl"
    with open(encoder_path, "wb") as f:
        pickle.dump(encoders, f)
    logger.info(f"  Saved label encoders → {encoder_path}")

    # Save category classes as JSON for API use
    classes = {col: list(enc.classes_) for col, enc in encoders.items()}
    with open(PROCESSED_DIR / "label_classes.json", "w") as f:
        json.dump(classes, f, indent=2)

    return df, encoders


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run_pipeline():
    logger.info("=" * 60)
    logger.info("OpsDesk AI — Data Pipeline Starting")
    logger.info("=" * 60)

    # 1. Ingest all datasets
    logger.info("\n[1/5] Ingesting raw datasets...")
    frames = []
    loaders = [
        (load_main_classifier_dataset, "classifier_v3"),
        (load_ticketing_2024_dataset, "ticketing_2024"),
        (load_multilang_dataset, "multilang"),
        (load_resolution_dataset, "resolution"),
        (load_mendeley_dataset, "mendeley"),
        (load_synthetic_dataset, "synthetic"),
    ]
    for loader_fn, source in loaders:
        try:
            raw = loader_fn()
            if not raw.empty:
                canon = canonicalize(raw, source)
                frames.append(canon)
                logger.info(f"  ✓ {source}: {len(canon)} rows canonicalized")
        except Exception as e:
            logger.error(f"  ✗ {source}: {e}")

    if not frames:
        raise RuntimeError("No datasets loaded. Check data/raw/ directory.")

    # 2. Merge all frames
    logger.info("\n[2/5] Merging and deduplicating...")
    df = pd.concat(frames, ignore_index=True)
    initial_count = len(df)
    df = df.drop_duplicates(subset=["ticket_id"], keep="first")
    logger.info(f"  {initial_count} → {len(df)} rows after dedup")

    # 3. Engineer features
    logger.info("\n[3/5] Engineering features...")
    df = engineer_features(df)
    logger.info(f"  ✓ Features engineered. Shape: {df.shape}")

    # 4. Encode labels
    logger.info("\n[4/5] Encoding labels...")
    df, encoders = encode_labels(df)

    # 5. Save outputs
    logger.info("\n[5/5] Saving processed datasets...")

    # Full unified dataset
    full_path = PROCESSED_DIR / "tickets_unified.csv"
    df.to_csv(full_path, index=False)
    logger.info(f"  ✓ Unified dataset → {full_path} ({len(df)} rows)")

    # Classification dataset (for ticket category model)
    clf_cols = ["ticket_id", "text_clean", "text_length", "word_count",
                "hour_of_day", "day_of_week", "is_weekend", "is_business_hours",
                "category", "category_encoded", "source_dataset"]
    clf_df = df[clf_cols].dropna(subset=["text_clean", "category"])
    clf_df = clf_df[clf_df["text_clean"].str.len() > 5]
    clf_path = PROCESSED_DIR / "classification_dataset.csv"
    clf_df.to_csv(clf_path, index=False)
    logger.info(f"  ✓ Classification dataset → {clf_path} ({len(clf_df)} rows)")

    # Routing dataset
    route_cols = ["ticket_id", "text_clean", "category_encoded", "priority_numeric",
                  "hour_of_day", "is_weekend", "department", "assigned_agent"]
    route_df = df[route_cols].dropna(subset=["assigned_agent"])
    route_df = route_df[route_df["assigned_agent"].str.strip() != ""]
    route_path = PROCESSED_DIR / "routing_dataset.csv"
    route_df.to_csv(route_path, index=False)
    logger.info(f"  ✓ Routing dataset → {route_path} ({len(route_df)} rows)")

    # Resolution time dataset
    res_cols = ["ticket_id", "category_encoded", "priority_numeric", "text_length",
                "word_count", "hour_of_day", "day_of_week", "is_weekend",
                "is_business_hours", "resolution_hours", "sla_target_hours", "sla_risk"]
    res_df = df[res_cols].dropna(subset=["resolution_hours"])
    res_df = res_df[res_df["resolution_hours"] > 0]
    res_path = PROCESSED_DIR / "resolution_time_dataset.csv"
    res_df.to_csv(res_path, index=False)
    logger.info(f"  ✓ Resolution time dataset → {res_path} ({len(res_df)} rows)")

    # Time-series dataset (for Prophet/LSTM)
    ts_df = df[["created_at", "category", "priority", "is_resolved"]].copy()
    ts_df["ds"] = pd.to_datetime(ts_df["created_at"]).dt.floor("h")
    ts_agg = ts_df.groupby("ds").size().reset_index(name="y")
    ts_path = PROCESSED_DIR / "timeseries_hourly.csv"
    ts_agg.to_csv(ts_path, index=False)
    logger.info(f"  ✓ Time-series dataset → {ts_path} ({len(ts_agg)} rows)")

    # Multilang subset
    ml_df = df[df["language"] != "en"][["ticket_id", "text_clean", "language", "category", "category_encoded"]]
    ml_path = PROCESSED_DIR / "multilang_dataset.csv"
    ml_df.to_csv(ml_path, index=False)
    logger.info(f"  ✓ Multilang dataset → {ml_path} ({len(ml_df)} rows)")

    # Dataset stats
    stats = {
        "total_tickets": int(len(df)),
        "date_range": {
            "start": str(df["created_at"].min()),
            "end": str(df["created_at"].max()),
        },
        "category_distribution": df["category"].value_counts().to_dict(),
        "priority_distribution": df["priority"].value_counts().to_dict(),
        "status_distribution": df["status"].value_counts().to_dict(),
        "language_distribution": df["language"].value_counts().to_dict(),
        "tenant_distribution": df["tenant_id"].value_counts().to_dict(),
        "avg_resolution_hours": float(df["resolution_hours"].mean()),
        "sla_breach_rate": float(df["sla_breached"].mean()) if "sla_breached" in df.columns else None,
        "source_distribution": df["source_dataset"].value_counts().to_dict(),
    }
    with open(PROCESSED_DIR / "pipeline_stats.json", "w") as f:
        json.dump(stats, f, indent=2, default=str)

    logger.info("\n" + "=" * 60)
    logger.info("Pipeline complete!")
    logger.info(f"  Total tickets processed: {len(df):,}")
    logger.info(f"  Outputs in: {PROCESSED_DIR}/")
    logger.info("=" * 60)
    return df, encoders


if __name__ == "__main__":
    run_pipeline()
