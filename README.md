# AI-Powered Aviation Incident Analysis and Contributing Factor Discovery

An end-to-end NLP/ML web application that reads free-text aviation incident
narratives and — **without any labels** — discovers the recurring themes,
latent topics, clusters, and *potential contributing factors* behind them, then
presents the findings through an interactive analytics dashboard with
meaning-based semantic search.

---

## What it does

Aviation safety reports are written in dense, unstructured prose. Reading them
one at a time hides the systemic patterns. This project applies unsupervised
NLP to a corpus of incident narratives and answers:

- **What themes recur?** — a 7-theme safety taxonomy grouped from discovered topics.
- **What are the latent topics?** — BERTopic (transformer embeddings + UMAP + HDBSCAN + c-TF-IDF), validated against a classical LDA baseline.
- **How do incidents cluster?** — KMeans over sentence embeddings, projected to a 2-D semantic map.
- **What contributing factors dominate, and how do they co-occur?** — factor ranking plus a co-occurrence network (count / lift / Jaccard).
- **How are factors trending over time?** — per-theme trajectories with rising/falling signals.
- **"Find me reports like this."** — semantic search that matches *concepts*, not keywords (a query for *engine fire* surfaces powerplant blazes even when those exact words never appear).

Everything is computed once into cached artifacts and served through a single
FastAPI process that also hosts the React dashboard.

---

## The 14-stage pipeline

Each analytic stage is an independent module under `backend/app/pipeline/`,
orchestrated by `runner.py` into the cached analysis. The dashboard surfaces the
results through the REST API.

| # | Stage | Module | API endpoint | Dashboard view |
|---|-------|--------|--------------|----------------|
| 1 | Data Collection | `app/data/generate_dataset.py` | — | — |
| 2 | Data Preparation | `pipeline/data_loader.py` | — | — |
| 3 | NLP Preprocessing | `pipeline/preprocess.py` | — | — |
| 4 | Named Entity Recognition | `pipeline/ner.py` (spaCy) | `GET /api/entities` | **Entities** |
| 5 | Text Embeddings | `pipeline/embeddings.py` (sentence-transformers) | — | (powers 7, 11, 12) |
| 6 | Topic Modelling (BERTopic + LDA) | `pipeline/topics.py` | `GET /api/topics` | **Topics** |
| 7 | Clustering | `pipeline/clustering.py` (KMeans) | `GET /api/clusters`, `GET /api/scatter` | **Clusters** |
| 8 | Contributing-Factor Analysis | `pipeline/factors.py` | `GET /api/factors` | **Factors** |
| 9 | Relationship (Co-occurrence) Analysis | `pipeline/relationships.py` | `GET /api/relationships` | **Relationships** |
| 10 | Trend Analysis | `pipeline/trends.py` | `GET /api/trends` | **Trends** |
| 11 | Interactive Dashboard | `frontend/` (React + Vite) | — | (the whole app) |
| 12 | Semantic Search | `pipeline/search.py` | `GET /api/search` | **Search** |
| 13 | Cloud Deployment | `Dockerfile`, `docker-compose.yml` | — | — |
| 14 | Testing & Evaluation | `backend/evaluate.py` (+ intrinsic metrics) | `GET /api/health` | **Overview** |

---

## Architecture

```
                         ┌───────────────────────────────────────┐
   Browser  ────────────▶│  FastAPI  (uvicorn, port 8000)         │
                         │                                        │
   /            SPA ─────┤  • serves frontend/dist (React build)  │
   /api/*  REST JSON ────┤  • REST API  (app/api/routes.py)       │
                         │  • AnalysisStore singleton (in-memory) │
                         └──────────────┬─────────────────────────┘
                                        │ loads at startup
                                        ▼
                         ┌───────────────────────────────────────┐
                         │  data_store/  (cached artifacts)       │
                         │  • analysis.json   (all stage outputs) │
                         │  • embeddings.npy  (384-d, L2-norm)    │
                         │  • embedder.pkl    (encoder descriptor)│
                         │  • meta.json                           │
                         └───────────────────────────────────────┘
                                        ▲ built once by
                                        │ pipeline/runner.py
        Stages 1–10 (data → NER → embeddings → topics → clusters →
        factors → relationships → trends)  +  Stage 12 search index
```

- **One process, one origin.** In production FastAPI serves the built SPA *and*
  the API, so there is no CORS or proxy to configure.
- **Precomputed.** The heavy NLP runs once into `data_store/`. Requests just read
  the cached analysis; only semantic search encodes the query live (the
  transformer model is loaded lazily on the first search).
- **Graceful degradation.** The full stack (sentence-transformers, BERTopic,
  spaCy) is primary; a scikit-learn fallback (TF-IDF+SVD embeddings, NMF topics,
  rule-based/gazetteer NER) runs automatically if a heavy library is unavailable
  (`AV_FORCE_LIGHTWEIGHT=1` forces it). `GET /api/health` reports which engines
  are active.

---

## Tech stack

**Backend** · Python · FastAPI · uvicorn · sentence-transformers (`all-MiniLM-L6-v2`) ·
BERTopic (UMAP + HDBSCAN + c-TF-IDF) · spaCy (`en_core_web_sm`) · scikit-learn
(KMeans, LDA, TF-IDF+SVD fallback) · NumPy · pandas

**Frontend** · React 18 · Vite · hash routing + React Context (no router lib) ·
**custom SVG charts** (no charting library — every mark is hand-built for a
validated, colorblind-safe, light/dark data-viz design system)

---

## Repository structure

```
aviation-incident-analysis/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app: API + serves the SPA
│   │   ├── config.py            # env-driven configuration
│   │   ├── api/routes.py        # all /api/* endpoints
│   │   ├── core/
│   │   │   ├── store.py         # AnalysisStore singleton (load/serve/rebuild)
│   │   │   └── capabilities.py  # detects which ML engines are available
│   │   ├── pipeline/            # the 14-stage analysis (see table above)
│   │   └── data/                # dataset generation / loading
│   ├── requirements.txt
│   ├── run.py                   # convenience launcher (python run.py)
│   └── evaluate.py              # Stage 14: offline evaluation / smoke test
├── frontend/
│   ├── src/
│   │   ├── views/               # 9 dashboard views (Overview, Topics, …)
│   │   ├── components/          # UI + custom SVG chart components
│   │   ├── lib/                 # palette, formatting, useApi hook
│   │   ├── theme.css            # design-system tokens (light + dark)
│   │   └── api.js               # typed API client (BASE = /api)
│   ├── package.json
│   └── vite.config.js           # dev proxy /api -> 127.0.0.1:8000
├── data_store/                  # cached analysis artifacts (generated)
├── Dockerfile                   # multi-stage build (node → python)
├── docker-compose.yml
└── README.md
```

---

## Quick start — Docker (recommended)

The single container builds the frontend, installs the NLP stack, bakes the
embedding + spaCy models, and serves the ready-to-use dashboard on port 8000.

```bash
docker compose up --build
```

Then open **http://localhost:8000**.

Equivalent without compose:

```bash
docker build -t aviation-incident-analysis .
docker run --rm -p 8000:8000 aviation-incident-analysis
```

> **First build is heavy.** It installs PyTorch + the transformer/spaCy models,
> so expect a multi-hundred-MB download and a few minutes. Subsequent builds are
> cached. See *Slimmer CPU-only image* below to shrink it.

---

## Local development

Two processes: the API on `:8000` and the Vite dev server on `:5173` (which
proxies `/api` to the backend).

**1 · Backend**

```bash
cd backend
python -m venv .venv && source .venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python run.py
```

On the **first** run the pipeline builds `data_store/` (downloads the embedding
+ spaCy models, runs all stages — a few minutes). Later runs load the cached
artifacts and start in seconds. The API is then at http://127.0.0.1:8000 and
interactive docs at http://127.0.0.1:8000/docs.

**2 · Frontend**

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

**Production-style build** (served by FastAPI, single origin):

```bash
cd frontend && npm run build     # emits frontend/dist
cd ../backend && python run.py   # open http://127.0.0.1:8000
```

---

## Configuration (environment variables)

All are optional; defaults match the shipped artifacts.

| Variable | Default | Purpose |
|----------|---------|---------|
| `AV_HOST` | `127.0.0.1` (`0.0.0.0` in Docker) | Bind address |
| `AV_PORT` | `8000` | Port |
| `AV_STORE_DIR` | `<project>/data_store` | Where cached artifacts live |
| `AV_SKIP_STARTUP_BUILD` | *(unset)* | `1` = don't build/load on startup |
| `AV_FORCE_LIGHTWEIGHT` | `0` | `1` = force the scikit-learn fallback stack |
| `AV_EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | sentence-transformers model |
| `AV_SPACY_MODEL` | `en_core_web_sm` | spaCy NER model |
| `AV_N_CLUSTERS` | `14` | KMeans cluster count |
| `AV_MIN_TOPIC_SIZE` | `10` | BERTopic minimum topic size |
| `AV_SYNTHETIC_N` | `480` | Size of the generated corpus |
| `AV_DATASET_CSV` | *(none)* | Path to a real CSV export (e.g. NTSB/ASRS) to use instead of the synthetic corpus |
| `AV_CORS_ORIGINS` | `localhost:5173,127.0.0.1:5173,localhost:4173` | Allowed origins (only needed if the frontend is hosted separately) |

---

## API reference

Base path: `/api` · interactive docs at `/docs`.

| Method & path | Description |
|---------------|-------------|
| `GET /api/health` | Liveness + which ML engines are active |
| `GET /api/overview` | Corpus stats, top factors, trend signals, topic-model comparison |
| `GET /api/topics` | Primary (BERTopic) topics + LDA baseline + comparison |
| `GET /api/clusters` | Cluster summaries |
| `GET /api/scatter` | Per-report 2-D coordinates for the semantic map |
| `GET /api/factors` | Ranked contributing factors + theme rollup |
| `GET /api/relationships` | Factor co-occurrence (count / lift / Jaccard) |
| `GET /api/trends` | Per-theme yearly series + rising/falling signals |
| `GET /api/entities` | Aggregated named entities (aircraft, orgs, airports, …) |
| `GET /api/reports` | Filter/paginate reports (`topic_id, cluster_id, theme, severity, year, q, limit, offset`) |
| `GET /api/reports/{idx}` | Full report + 6 nearest-neighbour reports |
| `GET /api/search?q=&k=` | Semantic search (cosine over embeddings) |
| `POST /api/rebuild` | Recompute all artifacts from scratch |

---

## How the analysis is cached

`data_store/` holds the entire precomputed analysis:

- **`analysis.json`** — every stage's output (topics, clusters, factors,
  relationships, trends, entities, per-report records).
- **`embeddings.npy`** — the L2-normalised embedding matrix used for search and
  the semantic map.
- **`embedder.pkl`** — a small descriptor of the encoder (backend + model name;
  the scikit-learn fallback also stores its fitted pipeline here). At search
  time this tells the app how to encode the query the same way the corpus was
  encoded.
- **`meta.json`** — build metadata.

To regenerate after changing hyper-parameters or supplying a real dataset:
`POST /api/rebuild`, or delete `data_store/` and restart. In the Docker image the
models are baked in, so a rebuild needs no network.

---

## Slimmer CPU-only image

The default `Dockerfile` installs the standard PyTorch wheel from PyPI, which is
reliable but large. For a much smaller CPU-only image, install PyTorch from its
CPU wheel index before the rest of the requirements. Replace the `pip install`
line in the `RUN` block with:

```dockerfile
pip install torch --index-url https://download.pytorch.org/whl/cpu; \
pip install -r backend/requirements.txt; \
```

(The second install sees PyTorch already satisfied and skips it.) This drops the
bundled CUDA runtime and typically cuts image size by several GB.

Alternatively, build a lightweight variant that avoids the transformer stack
entirely by setting `AV_FORCE_LIGHTWEIGHT=1` and rebuilding the artifacts — the
scikit-learn fallback (TF-IDF+SVD, NMF, rule-based NER) then powers search with a
much smaller dependency footprint, at some cost to semantic quality.

---

## Testing & evaluation (Stage 14)

A self-contained evaluation harness, `backend/evaluate.py`, loads the same
analysis store the API uses and runs structural + quality checks offline (it
also doubles as a CI smoke test — non-zero exit on any hard failure):

```bash
cd backend && python evaluate.py
```

It verifies, and reports on:

- **Engine introspection** — confirms which stack actually ran (full
  transformer stack vs the scikit-learn fallback).
- **Corpus integrity** — report counts and `stats` agree; date range is sane.
- **Silhouette score** for cluster cohesion/separation (intrinsic, label-free).
- **LDA perplexity** and the **BERTopic ↔ LDA comparison** — the primary topic
  model is validated against a classical baseline rather than trusted blindly.
- **Contributing factors, themes, relationships, trends, entities** are present
  and non-empty.
- **Semantic-search relevance** — five conceptual queries (e.g. *bird strike on
  takeoff*, *loss of control in icing*) must return results, and their top hits
  are scored for topical relevance.
- **Nearest-neighbour** lookup returns valid neighbours.

On the shipped full-stack artifacts this reports **19/19 checks passed** with
**5/5 search queries relevant in the top-3**. `GET /api/health` gives the same
engine check as a quick liveness probe.

---

## Notes on the dataset

The shipped corpus is **synthetically generated** (deterministic, ~480
narratives) so the project is fully reproducible without redistributing a
licensed safety database. The entire pipeline is dataset-agnostic: point
`AV_DATASET_CSV` at a real export (e.g. NTSB or NASA ASRS) with a narrative
column and rebuild to run the identical analysis on real data.

---

## License

Academic project — provided as-is for educational purposes.
