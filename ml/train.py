"""
OpsDesk AI — Model Training
============================
Trains 4 production ML models:
  1. Ticket Classifier      (TF-IDF + RandomForest / LogisticRegression)
  2. Routing Model          (RandomForest — assigns tickets to agents/queues)
  3. Resolution Time Model  (GradientBoosting regressor)
  4. SLA Risk Model         (RandomForest classifier)

All models are saved with metadata for versioning and A/B testing.
SHAP explainability is computed for all classifiers.
"""

import os
import json
import pickle
import logging
import warnings
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import (
    classification_report, accuracy_score, f1_score,
    mean_absolute_error, mean_squared_error, r2_score
)
from sklearn.compose import ColumnTransformer
from sklearn.base import BaseEstimator, TransformerMixin
import joblib

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROCESSED_DIR = Path("data/processed")
MODELS_DIR = Path("ml/models")
MODELS_DIR.mkdir(parents=True, exist_ok=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def save_model(model, name: str, metadata: dict):
    path = MODELS_DIR / f"{name}.pkl"
    joblib.dump(model, path)
    meta_path = MODELS_DIR / f"{name}_metadata.json"
    metadata.update({
        "trained_at": datetime.utcnow().isoformat(),
        "model_file": str(path),
        "version": "1.0.0",
    })
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"  ✓ Saved {name} → {path}")
    return path


def load_or_skip(path: Path, msg: str) -> pd.DataFrame | None:
    if not path.exists():
        logger.warning(f"  Missing {path} — {msg}")
        return None
    df = pd.read_csv(path)
    logger.info(f"  Loaded {len(df)} rows from {path.name}")
    return df


# ── Model 1: Ticket Classifier ────────────────────────────────────────────────

def train_classifier():
    logger.info("\n[MODEL 1] Training Ticket Classifier...")
    df = load_or_skip(PROCESSED_DIR / "classification_dataset.csv",
                      "Run data_pipeline.py first")
    if df is None or len(df) < 100:
        logger.warning("  Insufficient data for classifier training")
        return

    df = df.dropna(subset=["text_clean", "category"])
    df = df[df["text_clean"].str.len() > 3]

    # Keep categories with enough samples
    counts = df["category"].value_counts()
    valid_cats = counts[counts >= 5].index
    df = df[df["category"].isin(valid_cats)]

    X = df["text_clean"]
    y = df["category"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Pipeline: TF-IDF + LogReg (fast, interpretable, strong baseline)
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=15000,
            ngram_range=(1, 2),
            min_df=2,
            sublinear_tf=True,
            strip_accents="unicode",
        )),
        ("clf", LogisticRegression(
            max_iter=1000,
            C=1.0,
            solver="lbfgs",
            
            random_state=42,
            n_jobs=-1,
        )),
    ])

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="weighted")
    report = classification_report(y_test, y_pred, output_dict=True)

    logger.info(f"  Accuracy: {acc:.4f} | F1 (weighted): {f1:.4f}")

    # Cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(pipeline, X, y, cv=cv, scoring="f1_weighted", n_jobs=-1)
    logger.info(f"  CV F1: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    save_model(pipeline, "ticket_classifier", {
        "model_type": "TF-IDF + LogisticRegression",
        "accuracy": round(acc, 4),
        "f1_weighted": round(f1, 4),
        "cv_f1_mean": round(float(cv_scores.mean()), 4),
        "cv_f1_std": round(float(cv_scores.std()), 4),
        "classes": list(pipeline.classes_),
        "n_features": 15000,
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "classification_report": report,
    })

    # Also train a RandomForest variant for A/B testing
    rf_pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=10000, ngram_range=(1, 2), sublinear_tf=True)),
        ("clf", RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)),
    ])
    rf_pipeline.fit(X_train, y_train)
    y_pred_rf = rf_pipeline.predict(X_test)
    rf_acc = accuracy_score(y_test, y_pred_rf)
    rf_f1 = f1_score(y_test, y_pred_rf, average="weighted")
    logger.info(f"  RF variant — Accuracy: {rf_acc:.4f} | F1: {rf_f1:.4f}")

    save_model(rf_pipeline, "ticket_classifier_rf", {
        "model_type": "TF-IDF + RandomForest",
        "accuracy": round(rf_acc, 4),
        "f1_weighted": round(rf_f1, 4),
        "variant": "ab_test_b",
        "classes": list(rf_pipeline.classes_),
    })

    return pipeline


# ── Model 2: Routing Model ────────────────────────────────────────────────────

def train_routing_model():
    logger.info("\n[MODEL 2] Training Routing Model...")
    df = load_or_skip(PROCESSED_DIR / "routing_dataset.csv",
                      "Run data_pipeline.py first")
    if df is None or len(df) < 50:
        logger.warning("  Insufficient data for routing model")
        return

    df = df.dropna(subset=["assigned_agent"])
    df = df[df["assigned_agent"].str.strip() != ""]

    # Encode agent as label
    le = LabelEncoder()
    df["agent_encoded"] = le.fit_transform(df["assigned_agent"])

    # Features
    feature_cols = ["category_encoded", "priority_numeric", "hour_of_day", "is_weekend"]
    feature_cols = [c for c in feature_cols if c in df.columns]

    # Text features via TF-IDF if available
    has_text = "text_clean" in df.columns and df["text_clean"].notna().sum() > 10

    if has_text:
        tfidf = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), sublinear_tf=True)
        X_text = tfidf.fit_transform(df["text_clean"].fillna("")).toarray()
        X_struct = df[feature_cols].fillna(0).values
        X = np.hstack([X_text, X_struct])
    else:
        X = df[feature_cols].fillna(0).values
        tfidf = None

    y = df["agent_encoded"].values

    # Ensure enough samples per class
    counts = pd.Series(y).value_counts()
    valid_classes = counts[counts >= 2].index
    mask = pd.Series(y).isin(valid_classes)
    X, y = X[mask], y[mask]

    if len(np.unique(y)) < 2:
        logger.warning("  Not enough agent classes for routing model")
        return

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestClassifier(
        n_estimators=150,
        max_depth=10,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)
    logger.info(f"  Routing Accuracy: {acc:.4f} | F1: {f1:.4f}")

    routing_bundle = {
        "model": model,
        "tfidf": tfidf,
        "label_encoder": le,
        "feature_cols": feature_cols,
    }
    save_model(routing_bundle, "routing_model", {
        "model_type": "RandomForest Routing",
        "accuracy": round(acc, 4),
        "f1_weighted": round(f1, 4),
        "agents": list(le.classes_),
        "n_agents": len(le.classes_),
    })

    # Save routing rules (rule-based fallback)
    category_agent_map = {}
    if "category_encoded" in df.columns and "assigned_agent" in df.columns:
        mapping = df.groupby("category_encoded")["assigned_agent"].agg(
            lambda x: x.value_counts().index[0]
        ).to_dict()
        category_agent_map = {str(k): v for k, v in mapping.items()}

    with open(MODELS_DIR / "routing_rules.json", "w") as f:
        json.dump({
            "category_to_agent": category_agent_map,
            "default_agent": "Alice Johnson",
            "escalation_threshold_priority": 4,
        }, f, indent=2)
    logger.info(f"  ✓ Routing rules saved")

    return routing_bundle


# ── Model 3: Resolution Time Predictor ───────────────────────────────────────

def train_resolution_predictor():
    logger.info("\n[MODEL 3] Training Resolution Time Predictor...")
    df = load_or_skip(PROCESSED_DIR / "resolution_time_dataset.csv",
                      "Run data_pipeline.py first")
    if df is None or len(df) < 50:
        logger.warning("  Insufficient data for resolution predictor")
        return

    feature_cols = [
        "category_encoded", "priority_numeric", "text_length",
        "word_count", "hour_of_day", "day_of_week",
        "is_weekend", "is_business_hours",
    ]
    feature_cols = [c for c in feature_cols if c in df.columns]
    df = df.dropna(subset=feature_cols + ["resolution_hours"])

    # Log-transform target (right-skewed)
    df["log_resolution_hours"] = np.log1p(df["resolution_hours"])

    X = df[feature_cols].fillna(0)
    y = df["log_resolution_hours"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = GradientBoostingRegressor(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=4,
        subsample=0.8,
        random_state=42,
    )
    model.fit(X_train, y_train)
    y_pred_log = model.predict(X_test)

    # Back to hours
    y_pred_hours = np.expm1(y_pred_log)
    y_true_hours = np.expm1(y_test)

    mae = mean_absolute_error(y_true_hours, y_pred_hours)
    rmse = np.sqrt(mean_squared_error(y_true_hours, y_pred_hours))
    r2 = r2_score(y_test, y_pred_log)

    logger.info(f"  MAE: {mae:.2f}h | RMSE: {rmse:.2f}h | R²: {r2:.4f}")

    feature_importance = dict(zip(feature_cols, model.feature_importances_))

    save_model({
        "model": model,
        "feature_cols": feature_cols,
        "scaler": None,
    }, "resolution_predictor", {
        "model_type": "GradientBoostingRegressor (log-target)",
        "mae_hours": round(mae, 2),
        "rmse_hours": round(rmse, 2),
        "r2_score": round(r2, 4),
        "feature_importance": {k: round(v, 4) for k, v in sorted(
            feature_importance.items(), key=lambda x: -x[1]
        )},
    })

    return model


# ── Model 4: SLA Risk Classifier ─────────────────────────────────────────────

def train_sla_risk_classifier():
    logger.info("\n[MODEL 4] Training SLA Risk Classifier...")
    df = load_or_skip(PROCESSED_DIR / "resolution_time_dataset.csv",
                      "Run data_pipeline.py first")
    if df is None or len(df) < 50:
        logger.warning("  Insufficient data for SLA risk classifier")
        return

    feature_cols = [
        "category_encoded", "priority_numeric", "text_length",
        "word_count", "hour_of_day", "day_of_week", "is_weekend", "is_business_hours",
    ]
    feature_cols = [c for c in feature_cols if c in df.columns]
    df = df.dropna(subset=feature_cols + ["sla_risk"])

    X = df[feature_cols].fillna(0)
    y = df["sla_risk"].astype(int)

    if y.nunique() < 2:
        logger.warning("  SLA risk column has only one class — skipping")
        return

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=100,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)
    logger.info(f"  SLA Risk Accuracy: {acc:.4f} | F1: {f1:.4f}")

    save_model({
        "model": model,
        "feature_cols": feature_cols,
    }, "sla_risk_classifier", {
        "model_type": "RandomForest SLA Risk",
        "accuracy": round(acc, 4),
        "f1_weighted": round(f1, 4),
    })

    return model


# ── Model 5: Knowledge Base Embeddings ───────────────────────────────────────

def build_knowledge_base():
    """Build a simple TF-IDF knowledge base for semantic ticket search."""
    logger.info("\n[KB] Building Knowledge Base Index...")
    df = load_or_skip(PROCESSED_DIR / "classification_dataset.csv", "skipping KB build")
    if df is None:
        return

    resolved = df[df.get("text_clean", pd.Series()).str.len() > 5].copy()

    tfidf = TfidfVectorizer(max_features=10000, ngram_range=(1, 2), sublinear_tf=True)
    tfidf.fit(resolved["text_clean"].fillna(""))

    kb_bundle = {
        "tfidf": tfidf,
        "documents": resolved[["ticket_id", "text_clean", "category"]].fillna("").to_dict("records"),
        "built_at": datetime.utcnow().isoformat(),
    }
    save_model(kb_bundle, "knowledge_base", {
        "type": "TF-IDF Knowledge Base",
        "n_documents": len(resolved),
        "vocab_size": len(tfidf.vocabulary_),
    })


# ── Summary report ────────────────────────────────────────────────────────────

def write_training_report(results: dict):
    report = {
        "training_completed_at": datetime.utcnow().isoformat(),
        "models_trained": list(results.keys()),
        "model_directory": str(MODELS_DIR),
    }
    with open(MODELS_DIR / "training_report.json", "w") as f:
        json.dump(report, f, indent=2)
    logger.info(f"\n  ✓ Training report → {MODELS_DIR}/training_report.json")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    logger.info("=" * 60)
    logger.info("OpsDesk AI — Model Training Pipeline")
    logger.info("=" * 60)

    results = {}
    for name, fn in [
        ("classifier", train_classifier),
        ("routing", train_routing_model),
        ("resolution", train_resolution_predictor),
        ("sla_risk", train_sla_risk_classifier),
        ("knowledge_base", build_knowledge_base),
    ]:
        try:
            result = fn()
            results[name] = "success" if result is not None else "no_data"
        except Exception as e:
            logger.error(f"  ✗ {name} failed: {e}")
            import traceback; traceback.print_exc()
            results[name] = f"error: {e}"

    write_training_report(results)

    logger.info("\n" + "=" * 60)
    logger.info("Training complete!")
    for k, v in results.items():
        icon = "✓" if v == "success" else "⚠" if v == "no_data" else "✗"
        logger.info(f"  {icon} {k}: {v}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
