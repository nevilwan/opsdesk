# OpsDesk AI — Data Directory

## Structure

```
data/
├── raw/                    ← Source datasets (download from URLs in README)
│   ├── all_tickets_processed_improved_v3.csv
│   ├── Support_Ticketing_Cleaned_Jan-Jul_2024.csv
│   ├── dataset-tickets-multi-lang-4-20k.csv
│   ├── customer_support_tickets_resolution.csv
│   ├── helpdesk_tickets_mendeley.csv
│   └── IT_helpdesk_synthetic_tickets.csv
│
├── processed/              ← Pipeline outputs (auto-generated)
│   ├── tickets_unified.csv         ← 12,000+ merged tickets
│   ├── classification_dataset.csv  ← ML training: text + category labels
│   ├── routing_dataset.csv         ← ML training: structured + agent labels
│   ├── resolution_time_dataset.csv ← ML training: features + hours target
│   ├── timeseries_hourly.csv       ← Prophet/LSTM: ds + y (hourly counts)
│   ├── multilang_dataset.csv       ← Non-English tickets subset
│   ├── label_classes.json          ← Category/priority/status class lists
│   └── pipeline_stats.json         ← Distribution statistics
│
└── samples/
    └── generate_samples.py    ← Generates sample CSVs matching real schemas
```

## Replacing Sample Data with Real Datasets

The project ships with **high-fidelity sample CSVs** that mirror real dataset schemas.
To use actual production data:

1. Download from sources listed in `README.md`
2. Place in `data/raw/` with exact filenames above
3. Run the pipeline: `python3 ml/data_pipeline.py`
4. Re-train models: `python3 ml/train.py`

The pipeline handles schema variations automatically via column aliasing.

## Data Privacy

In production:
- Never commit real PII to git
- Use `.gitignore` to exclude `data/raw/*.csv`
- Store in encrypted S3/GCS buckets
- Apply anonymization in the ingestion step
