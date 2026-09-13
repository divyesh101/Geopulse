# GeoPulse — Predicting Bike Demand Across New York City

**Author:** Divyesh Jawkhede, IIT Kharagpur

GeoPulse predicts how many Citi Bikes will be picked up and dropped off across New
York City, 15 to 60 minutes in advance, and uses those predictions to plan bike
rebalancing across the city. It's trained on two full years of real data
(2023–2024) — about **79 million actual bike rides**.

## Objective

1. Find the best way to split NYC into map cells for demand forecasting.
2. Compare hexagon-based (H3) vs. square-based (S2) map grids.
3. Compare a classical gradient-boosted model against deep-learning models (a
   Transformer and a Graph Neural Network).
4. Use the forecasts to drive a real bike-rebalancing simulation.

## Best result

The final tuned model predicts bike pickups/dropoffs per cell with an average
error of **~1.14 bikes** on a completely held-out two-month test period — meaning
the model's forecast is typically off by about **one bike**.

## Methodology

1. **Data pipeline** — cleaned and de-duplicated 90 raw trip files, timezone- and
   DST-corrected timestamps, merged in weather, city events, and traffic data.
2. **Spatial gridding** — divided NYC into hexagonal cells (H3) and built a dense
   15-minute time-series panel per cell.
3. **Baseline** — a seasonal-naive baseline, beaten by every model that followed.
4. **Feature engineering** — calendar, seasonal, and rolling-trend features.
5. **Grid comparison** — tested multiple H3 resolutions and an S2 grid to find the
   best spatial resolution.
6. **Model training** — trained and tuned LightGBM (with Optuna), a Temporal
   Fusion Transformer (TFT), and a Spatio-Temporal Graph Neural Network (ST-GNN).
7. **Evaluation** — final one-time evaluation on an untouched test period.
8. **Rebalancing simulation** — used the forecasts to simulate moving bikes
   between stations to reduce shortages.

## Models used

- **LightGBM** (gradient-boosted trees, tuned with Optuna) 
- **Temporal Fusion Transformer (TFT)** — deep learning, Transformer-based 
- **Spatio-Temporal GNN (ST-GNN)** — deep learning, graph-based (best-performing model)
- **Seasonal Naive** — baseline for comparison

## A working demo app

The project also ships a working web app ([`app/`](app/)) where you can click
anywhere on a live NYC map and get a real demand forecast, nearby available docks,
and a chat assistant that explains the prediction. See
[`app/README.md`](app/README.md) to run it locally.

## Repository structure

```
configs/     All tunable settings (thresholds, model hyperparameters)
data/        Raw and processed data (not stored in this repo, see below)
src/         Pipeline code: data cleaning, spatial gridding, features, models, rebalancing
scripts/     Runnable step-by-step scripts, numbered in run order
tests/       Automated tests (146 tests)
outputs/     Trained models, metrics, and reports
app/         The live web app (FastAPI backend + map frontend)
docs/        Full project report and data source documentation
notebooks/   Exploratory data analysis only
```

**Note on data:** raw and processed datasets (tens of GB) are excluded via
`.gitignore` and are reproducible by running the numbered scripts in `scripts/`
against the sources listed in [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md).

## How to run it

```bash
pip install -r requirements.txt

make phase1         # ingest -> clean -> weather -> events -> registry -> dev sample
make test           # run the automated test suite

# Or run the demo app directly (works out of the box, no API key needed)
python -m uvicorn app.server:app --reload --port 8000
```

## Tools and technologies used

- **Data processing:** Python, Polars, DuckDB, Pandas, Parquet
- **Spatial indexing:** H3, S2, GeoPandas, Shapely
- **Modeling:** LightGBM, Optuna, PyTorch, PyTorch Forecasting (TFT), PyTorch
  Geometric (ST-GNN)
- **App:** FastAPI backend, map-based JS frontend
- **Testing:** pytest

---

*Built and documented by Divyesh Jawkhede, IIT Kharagpur.*
