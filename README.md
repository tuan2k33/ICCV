# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

**Inventory Count** — an automated warehouse inventory system that counts stock from video recordings of shelf racks. An operator walks a shelf row with a camera; the pipeline detects each bin, reads the bin code (OCR), reads the product ID, and classifies the bin as empty/full.

This repo (`iccv`, remote: `github.com/tuan2k33/ICCV` — GitHub still redirects the old `inventorycount` name) is a **monorepo assembled from five originally-independent repositories**, squashed into a single initial commit on `main`. There is no meaningful per-service git history for those five — treat each subfolder as its own project with its own toolchain:

| Folder | Service | Stack |
|---|---|---|
| `VideoCopy/` | Desktop app that copies video off cameras/drives and announces new footage | Python, PySide6 (Qt), Kafka producer |
| `ic_ai/` | AI/CV processing pipeline (GPU) | Python, FastAPI, PyTorch, PaddleOCR, Decord (custom NVDEC build) |
| `kafka_consumer_service/` | Glue service: reacts to new footage, calls the AI service, forwards results to the backend | Python, kafka-python |
| `ic_be/` | Backend of record (auth, tasks, tenants, batches) | Python, FastAPI, Postgres (raw SQL), Poetry |
| `ic_fe/` | Operator web UI | React Router v7, Redux Toolkit, Tailwind v4, TypeScript |
| `research/` | Earlier CV-counting research prototype (notebooks, training/tuning scripts) — merged in from the old `master` branch, which had no commit history in common with `main`. Not part of the running system. | Python, Jupyter |

## Data flow / pipeline

```
VideoCopy (native app)
   │  copies video files to shared storage, publishes Kafka event
   │  topic "video_copy_events", event_type "copy_complete"
   ▼
Kafka broker
   ▼
kafka_consumer_service (consumer_service.py)
   │  1. POST video paths → ic_ai  /process-videos/
   │  2. group resulting bins by rack prefix + parity (see gotchas)
   │  3. PUT grouped results     → ic_be  /api/task
   ▼
ic_ai (api_server.py → main.py: VideoProcessing.get_inventory_informations)
   concat videos → GPU decode (Decord/NVDEC) →
   ResNet50 frame classifier (background/carton/code) ∥ PaddleOCR bin-code reader →
   group frames by bin code → save code/front/top images + per-bin clip →
   PaddleOCR product-ID reader + fullness (ResNet50) classifier →
   dict_total.json (no DB — all AI output is files under outputs/)
   ▼
ic_be (FastAPI + Postgres)
   persists tasks/batches/tenants, pushes live updates over /ws
   ▼
ic_fe (React Router)
   operator reviews/corrects counts: Dashboard, Entry, Checker, Admin, MyTasks
```

## Commands

### ic_be (backend)
```bash
cd ic_be
poetry install                                    # Python 3.10+
poetry run uvicorn app.main:app --reload           # dev server, localhost:8000
make run                                           # alt: python -m app.main
make create-admin-default                          # seeds admin/Rsc@2025 (requires DB)
make import-temp-data                              # seeds temp data
poetry run pytest                                  # all tests
poetry run pytest tests/auth/test_auth_service.py  # single file
poetry run pytest -m unit                          # marker-filtered (unit/integration/slow)
poetry run flake8 app/ --max-line-length=120        # lint, matches CI
```
DB schema changes are raw SQL files in `app/migrations/upgrade/` (+ matching `app/migrations/downgrade/`), applied in order by `scripts/setup.sh` — this project does **not** use Alembic.

### ic_ai (AI/CV pipeline, requires NVIDIA GPU + CUDA 13)
```bash
cd ic_ai
pip install -r requirements.txt
cd /tmp/decord2/python && pip install .            # custom GPU (NVDEC) Decord build
python main.py --video_input <path> --output_path outputs --config configs/config.yaml --mode 1
uvicorn api_server:app --host 0.0.0.0 --port 8000   # run as the API kafka_consumer_service calls
```
`ic_ai/DOCUMENTATION.md` is a full Vietnamese-language design doc (architecture, config reference, per-module API) — read it before making non-trivial changes to the pipeline.

### ic_fe (frontend)
```bash
cd ic_fe
npm install            # Node >= 20
npm run dev            # react-router dev server
npm run build
npm run typecheck      # react-router typegen && tsc
npm run lint / lint:fix
```
Backend base URL comes from `VITE_API_URL` (`.env`). Routes live in `src/app/routes/`, registered in `src/app/routes.ts`; app entry directory is `src/app` (set via `appDirectory` in `react-router.config.ts`), SSR is disabled (`ssr: false`).

### kafka_consumer_service
```bash
cd kafka_consumer_service
pip install -r requirements.txt
python consumer_service.py
```
Configured entirely via env vars: `KAFKA_BROKER_URL`, `KAFKA_TOPIC`, `PROCESSING_API_URL` (ic_ai), `UI_API_URL` (ic_be `/api/task`), `AI_FOLDER_PATH`, `AI_OUTPUT_SUBPATH`.

### VideoCopy (native desktop app)
```bash
cd VideoCopy
conda activate copyvideo    # or: pip install -r requirements.txt
python main.py
```
Kafka target (`kafka_servers`, `kafka_topic`) is read from `config.json` alongside the script.

### Full stack
```bash
bash start.sh [test|dev]   # default: test
```
Reads root `.env` (`HOST`, `BASE`, data/weights/template paths) and brings up, in order: Kafka broker → `ic_be` (Postgres + API) → `ic_ai` → `kafka_consumer_service` → `ic_fe`, each via its own `docker-compose.<env>.yml`. `VideoCopy` is never dockerized by `start.sh` — it runs natively next to the capture hardware. Every service ships three compose files (`docker-compose.yml` prod / `.dev.yml` / `.test.yml`); see `test.md` for the full container/port table and default login (`admin / Rsc@2025`).

## Architecture notes / gotchas

- **Watch for stray absolute imports in the working tree**: `ic_be` and `VideoCopy` have, more than once, ended up with uncommitted local edits that rewrite their imports to an absolute path rooted at the *original* per-service repo layout, e.g. `from projects.inventory_count.AI_IC_BE.app.core.setting import settings` instead of the committed `from app.core.setting import settings` (same pattern for `VideoCopy` under `projects.inventory_count.VideoCopy.*`). This does not match the committed code and breaks every import (`ModuleNotFoundError: No module named 'projects'`) — if you see it, diff the file against `git show HEAD:<path>` before rewriting; it's almost always a straight revert, not a real refactor. `ic_ai` and `kafka_consumer_service` use plain relative imports and have not shown this problem.
- **Bin code format**: `XX-NNN-P` — 2-letter aisle prefix, 3-digit rack number, 1–6 position digit (e.g. `AT-076-3`). `kafka_consumer_service.group_and_send_to_ui` splits this to group racks into `<prefix>-odd` / `<prefix>-even` (by parity of the numeric part) before PUTting to `ic_be`.
- **No database in `ic_ai`**: every pipeline run is self-contained on disk — `dict_total.json`, `output_raw.csv`/`output_processed.csv`, images, and per-bin video clips under `outputs/<video>_<timestamp>_result/` and `outputs/<bin_code>/`.
- **Timezone**: `ic_ai` logging (`utils/logger.py`) is fixed to Asia/Ho_Chi_Minh regardless of host timezone.
- **Multi-tenant**: `ic_be` has a `tenant` module and most task/batch operations are tenant-scoped; `kafka_consumer_service` currently hardcodes `tenant_id=1` when calling `PUT /api/task`.
- **Storage layout convention**: shared data lives under `/ssd1` and `/hdd1` on the deployment host (see root `.env`: `AI_WEIGHTS_DIR`, `AI_FOLDER_PATH`, `SSD1`/`HDD1`), mounted straight into containers rather than copied in.
- `note.md` / `test.md` at the repo root are operator scratch notes (Vietnamese) with real ops commands: DB snapshot/restore via `pg_dump`/`psql` against the deployed Postgres container, deleting non-seed users, resetting a half-finished count batch, and the full service/port table for the `tuannq` test environment.
