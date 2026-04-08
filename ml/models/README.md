# OpsDesk AI — ML Models Directory

This directory contains all trained model artifacts.

## Files

| File | Description | Size |
|---|---|---|
| `ticket_classifier.pkl` | TF-IDF + LogisticRegression — classifies tickets into 10 categories | ~85KB |
| `ticket_classifier_rf.pkl` | TF-IDF + RandomForest — A/B test variant B | ~3MB |
| `routing_model.pkl` | TF-IDF + RandomForest — routes tickets to agents/queues | ~1.8MB |
| `resolution_predictor.pkl` | GradientBoosting regressor — predicts resolution time in hours | ~494KB |
| `sla_risk_classifier.pkl` | RandomForest — predicts SLA breach probability (0–1) | ~31MB |
| `knowledge_base.pkl` | TF-IDF index over resolved tickets for semantic KB search | ~753KB |
| `label_encoders.pkl` | sklearn LabelEncoders for categorical features | ~1KB |
| `routing_rules.json` | Rule-based routing fallback map (category → agent) | <1KB |
| `*_metadata.json` | Training metrics, timestamps, and model configs | <1KB each |
| `training_report.json` | Summary report of last training run | <1KB |

## Re-training

```bash
# From project root:
python3 ml/data_pipeline.py   # re-process datasets
python3 ml/train.py           # re-train all models
```

## Model Versioning

Each model file has a corresponding `*_metadata.json` with:
- `trained_at`: ISO timestamp
- `version`: semantic version
- `accuracy` / `mae_hours` / `r2_score`: performance metrics
- `model_type`: algorithm description

In production, use MLflow or DVC for full model versioning and experiment tracking.

## Large Files

`sla_risk_classifier.pkl` (~31MB) is large due to the RandomForest with 100 trees.
For production, consider:
- Reducing `n_estimators` to 50
- Using `joblib` compression: `joblib.dump(model, path, compress=3)`
- Storing in S3/GCS and loading at startup
