# PyroSafe

**An SI-powered fire safety dashboard for space habitats.**
Built for the NASA International Space Apps Challenge 2026.

## The problem

Fire is one of the most dangerous hazards in human spaceflight. NASA has run combustion experiments in microgravity for decades, and the results are available in the Physical Science Informatics (PSI) database. But there is so much data that it is hard to find, compare, and interpret. Planned Moon Base and rover cabins will use more oxygen (about 30% or more at 10.2 psi or less) than Earth's air (21% at 14.7 psi), which makes materials more flammable.

## What PyroSafe does

An engineer picks a habitat scenario (ISS, Artemis capsule, Moon Base, pressurized rover) and gets:

1. **Ranked investigations:** the NASA experiments most relevant to that scenario, with a plain explanation of why each ranks where it does.
2. **Flame analysis from real experiment video:** flame detection and measurement (area, sphericity, spread rate) over time.
3. **Flammability risk prediction:** a what-if tool where sliders for oxygen, airflow and pressure give a burn probability, with SHAP charts showing why.
4. **SI-written interpretation:** a retrieval-based assistant that answers questions and writes a short safety briefing, with citations back to the investigations.

## Honest limits

- PSI currently contains **microgravity** data (from the ISS) and no partial-gravity data. Predictions for Moon or Mars gravity are **extrapolations** and are labeled that way in the dashboard.
- The ranking weights and risk-level thresholds are our own design choices, not NASA standards.
- Our flame detector is trained on selected PSI runs and tested on held-out runs. It is not a general flame detector for any video.
- [Add model accuracy and dataset sizes here once known.]

## How it works

```
PSI data and videos
   -> ETL (ml/) + OpenCV and YOLO (vision/)
   -> feature tables + flame metrics CSVs
   -> FastAPI backend (backend/)
   -> Next.js dashboard (frontend/)
```

Main endpoints: `/investigations`, `/rank`, `/predict`, `/scenario-risk`, `/flame-metrics/{video_id}`, `/ask`. See `docs/api-contract.md`.

## Quickstart

```bash
git clone [repo-url]
cd pyrosafe
# Backend
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload
# Frontend (new terminal)
cd frontend && npm install && npm run dev
```

[Update these commands to match the final setup. Add Docker instructions if used.]

Copy `.env.example` to `.env` and fill in the values. Never commit secrets.

## Repository structure

| Folder | Contents | Owner |
|---|---|---|
| `docs/`, `contracts/` | API contract, data schemas, decisions log | Fawad |
| `backend/` | FastAPI: `/investigations`, `/rank`, `/ask` | Fawad |
| `backend/` | ML endpoints: `/predict`, `/scenario-risk`, `/flame-metrics` | Osama |
| `frontend/` | Next.js dashboard | Shahbaz |
| `data/`, `ml/` | ETL, XGBoost, SHAP, investigation summaries | Maira |
| `vision/` | Extraction, detection, tracking | Tayyab |
| `vision/` | Segmentation, metrics | Asiya |
| `deck/` | Pitch visuals and diagrams | Asiya |

## Data and sources

- NASA Physical Science Informatics (PSI) database: [add link and access date]
- Challenge statement and resources: NASA Space Apps Challenge 2026
- Raw videos and extracted frames are not stored in this repo. To get them, [describe where to download them and how to place them in `data/raw/`].

## Built during the hackathon

All project code in this repository was written during the NASA Space Apps Challenge 2026 (14 to 15 Nov 2026). The commit history shows the work as it happened. Open-source libraries we used: FastAPI, Next.js, Recharts, OpenCV, Ultralytics YOLO, XGBoost, SHAP, [add others]. [List any small generic utilities reused from earlier work, if any.]

## Data formats

- Flame metrics CSV: `video_id, frame, time_s, box_x, box_y, box_w, box_h, confidence, mask_path, area_px, sphericity, spread_rate` (pixels unless a scale reference exists)
- Video index CSV: `video_id, investigation, o2_percent, pressure_psi, airflow, fuel, duration_s, file`

Full schemas are in `docs/data-schemas.md`.

## Beyond space

Findings from combustion in microgravity also support fire safety on Earth, such as fine-water-mist extinguishers, smoke detection and firefighter gear.

## Team

- Fawad Ahmed Baig (Lead): architecture, FastAPI backend, integration
- Shahbaz Ahmad Mazari: Next.js dashboard and UI/UX
- Muhammad Tayyab: video extraction and flame tracking
- Asiya Ali Khan: flame segmentation and pitch visuals
- Osama Sohail Rana: model inference and API endpoints
- Maira Naveed: data ETL and XGBoost hazard analytics

## License

MIT License
