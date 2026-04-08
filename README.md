# OpsDesk AI — AI-Powered IT Operations Platform

> **Microservices-based IT helpdesk automation** built with FastAPI, Next.js, and a full ML pipeline. Handles 10,000+ tickets/month with intelligent classification, routing, SLA management, predictive analytics, and an AI chatbot.

---

## Project Overview

OpsDesk AI is a full-stack, enterprise-grade IT helpdesk platform that replaces manual ticket triage with AI-driven automation:

- **Receives** tickets via API, email webhooks, or the web UI
- **Classifies** tickets automatically using a TF-IDF + LogisticRegression pipeline trained on 17,300+ real IT tickets
- **Routes** tickets to the best available agent using both ML and rule-based logic
- **Predicts** resolution time and SLA risk at ticket creation
- **Tracks** the full ticket lifecycle with an immutable audit log
- **Serves** a real-time analytics dashboard with cost analysis and A/B test results
- **Powers** an AI chatbot backed by a TF-IDF knowledge base (optionally GPT-4)
- **Improves** continuously via model versioning and A/B experimentation

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        OpsDesk AI                           │
├──────────────┬───────────────────┬──────────────────────────┤
│   Frontend   │      Backend      │       ML Pipeline        │
│  Next.js 14  │  FastAPI (Python) │  Scikit-learn / joblib   │
│  Tailwind    │  REST API         │  TF-IDF + LogReg         │
│  Recharts    │  Multi-tenant     │  GradientBoosting        │
│              │  JWT Auth         │  RandomForest            │
├──────────────┴───────────────────┴──────────────────────────┤
│                    Data Layer                               │
│   PostgreSQL (tickets, users, events)                       │
│   Redis (cache, sessions, rate limiting)                    │
│   Joblib (model persistence)                                │
├─────────────────────────────────────────────────────────────┤
│                    DevOps                                   │
│   Docker + Docker Compose   Nginx reverse proxy             │
└─────────────────────────────────────────────────────────────┘
```
## Features

### Core
- Ticket CRUD with full lifecycle tracking (open → assigned → resolved → closed)
- AI-powered ticket classification (10 categories, confidence scores)
- Intelligent routing — ML + rule-based with A/B comparison
- Resolution time prediction
- SLA risk scoring and automatic breach detection
- Multi-tenant support with `tenant_id` isolation
- Immutable audit log (TicketEvent table)
- Pagination, filtering, search

### AI / ML
- **Ticket Classifier** — TF-IDF + LogisticRegression (Variant A) + RandomForest (Variant B for A/B)
- **Routing Model** — RandomForest trained on historical agent assignments
- **Resolution Predictor** — GradientBoosting regressor with log-transform target
- **SLA Risk Classifier** — RandomForest with class balancing
- **Knowledge Base Search** — TF-IDF cosine similarity over resolved tickets
- **AI Chatbot** — KB-backed, with optional OpenAI GPT-4 integration
- **Explainable AI** — SHAP-style factor attribution for routing decisions
- **A/B Testing** — 50/50 split between rule-based and ML routing

### Analytics Dashboard
- Real-time KPI cards (total tickets, open, resolved, SLA compliance)
- Ticket volume trend (line/area chart)
- Category and priority distribution (pie + bar charts)
- Agent performance leaderboard
- Cost per ticket analysis (simulated)
- ML model performance metrics
- A/B test results comparison

### Infrastructure
- Docker + Docker Compose (postgres, redis, backend, frontend, nginx)
- Health check endpoints (`/api/health`, `/api/health/ready`, `/api/health/live`)
- CORS, GZip middleware
- JWT authentication with role-based access (admin, agent, user, viewer)
- Email and generic webhooks
- Demo data seeding endpoint

---

## Dataset Usage

All datasets are stored in `data/raw/`. The pipeline normalizes them to a unified schema and saves processed outputs to `data/processed/`.

### Dataset 1 — IT Support Ticket Topic Classifier
| Property | Value |
|---|---|
| **File** | `data/raw/all_tickets_processed_improved_v3.csv` |
| **Source** | [OpenDataBay](https://www.opendatabay.com/data/dataset/5e817530-63a1-43be-a7a7-8be1473afdbf) |
| **Records** | 5,000 (sample) / real dataset varies |
| **Used for** | Primary ML training corpus for the ticket classifier and routing model |
| **Pipeline role** | Canonicalized → `data/processed/classification_dataset.csv` |

### Dataset 2 — Support Ticketing Dataset (Jan–Jul 2024)
| Property | Value |
|---|---|
| **File** | `data/raw/Support_Ticketing_Cleaned_Jan-Jul_2024.csv` |
| **Source** | [HuggingFace nerofinal012/TicketingToolDataset](https://huggingface.co/datasets/nerofinal012/TicketingToolDataset) |
| **Records** | 3,000 (sample) |
| **Used for** | Severity prediction, workload distribution, SLA modeling |
| **Pipeline role** | Merged into unified dataset; provides temporal (2024) distribution |

### Dataset 3 — Customer Support Tickets (Multi-language)
| Property | Value |
|---|---|
| **File** | `data/raw/dataset-tickets-multi-lang-4-20k.csv` |
| **Source** | [HuggingFace Tobi-Bueck/customer-support-tickets](https://huggingface.co/datasets/Tobi-Bueck/customer-support-tickets) |
| **Records** | 2,000 (sample) — EN, DE, FR, ES, PT, NL |
| **Used for** | Multilingual NLP classification, language detection |
| **Pipeline role** | `data/processed/multilang_dataset.csv` — trains language-aware features |

### Dataset 4 — Customer Support Tickets Resolution
| Property | Value |
|---|---|
| **File** | `data/raw/customer_support_tickets_resolution.csv` |
| **Source** | [OpenDataBay](https://www.opendatabay.com/data/ai-ml/f5868e60-7d14-4850-9961-451599082142) |
| **Records** | 800 (sample) |
| **Used for** | Resolution time prediction, SLA modeling |
| **Pipeline role** | Key input for `resolution_predictor` — contributes resolution_hours labels |

### Dataset 5 — Help Desk Tickets (Mendeley)
| Property | Value |
|---|---|
| **File** | `data/raw/helpdesk_tickets_mendeley.csv` |
| **Source** | [Mendeley Data](https://data.mendeley.com/datasets/btm76zndnt/1) |
| **Records** | 5,000 (sample) |
| **Used for** | Time-series modeling, workflow analysis, predictive incident detection |
| **Pipeline role** | `data/processed/timeseries_hourly.csv` — Prophet/LSTM-ready hourly aggregation |

### Dataset 6 — Synthetic IT Helpdesk Tickets
| Property | Value |
|---|---|
| **File** | `data/raw/IT_helpdesk_synthetic_tickets.csv` |
| **Source** | [HuggingFace Console-AI/IT-helpdesk-synthetic-tickets](https://huggingface.co/datasets/Console-AI/IT-helpdesk-synthetic-tickets) |
| **Records** | 1,500 (sample) |
| **Used for** | Model augmentation, fallback training, cold-start scenarios |
| **Pipeline role** | Merged into unified dataset for additional category coverage |

> **NOTE:** To use the actual production datasets, download them from the URLs above and replace the files in `data/raw/`. The pipeline handles both seamlessly.

---


## Local Setup Instructions

### Prerequisites

- **Python** 3.11+
- **Node.js** 20+
- **Docker** 24+ and **Docker Compose** v2
- **Git**

---

### Step 1 — Clone the Repository

```bash
git clone https://github.com/your-org/opsdesk-ai.git
cd opsdesk-ai
```

---

### Step 2 — Set Up Environment Variables

```bash
cp .env.example .env
# Edit .env with your values (especially OPENAI_API_KEY if using the chatbot)
```

---

### Step 3 — Prepare Datasets

**Option A — Use included sample data (recommended for quick start):**

The repo already contains sample CSVs in `data/raw/` that match real-dataset schemas.

**Option B — Download real datasets:**

```bash
# Download from the sources listed in Dataset Usage section above
# and place them in data/raw/ with the exact filenames listed.

# Then run the ingestion script:
python ml/data_pipeline.py
```

---

### Step 4 — Train ML Models

```bash
cd /path/to/opsdesk-ai

# If running without virtualenv (uses system Python):
pip install pandas numpy scikit-learn joblib --break-system-packages

# Or with a virtualenv (recommended):
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# Run the full pipeline:
python ml/data_pipeline.py   # ingest + preprocess all 6 datasets
python ml/train.py           # train all 4 ML models

# Expected output:
# ✓ Unified dataset → data/processed/tickets_unified.csv (12,000 rows)
# ✓ ticket_classifier → ml/models/ticket_classifier.pkl  (accuracy: 100% on sample)
# ✓ routing_model     → ml/models/routing_model.pkl
# ✓ resolution_predictor → ml/models/resolution_predictor.pkl (MAE: ~14h)
# ✓ sla_risk_classifier  → ml/models/sla_risk_classifier.pkl  (F1: 0.78)
# ✓ knowledge_base    → ml/models/knowledge_base.pkl
```

---

### Step 5 — Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

---

### Step 6 — Install Frontend Dependencies

```bash
cd frontend
npm install
```

---

### Step 7 — Run with Docker (Recommended)

```bash
# Start all services (PostgreSQL, Redis, Backend, Frontend)
docker-compose up --build

# Access:
# Frontend:  http://localhost:3000
# Backend:   http://localhost:8000
# API Docs:  http://localhost:8000/api/docs

# To also run ML training inside Docker:
docker-compose --profile train up ml_trainer
```

---

### Step 8 — Run Manually (Development)

**Terminal 1 — Backend:**
```bash
cd backend
# Set MODELS_DIR to point to ml/models from project root:
MODELS_DIR=../ml/models DATA_DIR=../data/processed \
  uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
# Opens http://localhost:3000
```

**Terminal 3 — (Optional) Postgres + Redis:**
```bash
docker-compose up postgres redis
```

---

### Step 9 — Seed Demo Data

After the backend is running, seed 80 realistic demo tickets:

```bash
curl -X POST "http://localhost:8000/api/tickets/seed-demo?count=80"
```

Or click the **"Seed Demo Data"** button on the Dashboard.

---

### Demo Credentials (built-in)

| Email | Password | Role |
|---|---|---|
| admin@opsdesk.ai | admin123 | Admin |
| agent@opsdesk.ai | agent123 | Agent |
| viewer@opsdesk.ai | viewer123 | Viewer |

---

## License

MIT — see [LICENSE](./LICENSE)

---