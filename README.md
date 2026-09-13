# GeoPulse — Predicting Bike Demand Across New York City

**Author:** Divyesh Jawkhede, IIT Kharagpur

GeoPulse is an end-to-end machine learning project that predicts how many bikes
will be picked up and dropped off across New York City's Citi Bike network, 15 to 60
minutes in advance — and then uses those predictions to decide where bikes should be
moved so stations don't run empty or overflow.

This is not a toy project. It runs on **two full years of real data (2023–2024)**,
around **79 million actual bike rides**, combined with weather, city events, and
traffic data, and it compares five different forecasting models before drawing
conclusions.

---

## 1. What problem does this solve?

Bike-share systems like Citi Bike constantly go out of balance — some stations
run out of bikes (a rider shows up and finds nothing), while others fill up
completely (a rider can't return their bike anywhere). Operators fix this by
manually trucking bikes between stations, but they need to know **where demand is
about to spike** to move bikes ahead of time instead of reacting late.

GeoPulse builds that forecasting system from scratch and tests whether it actually
helps.

## 2. What questions did this project try to answer?

The whole project was built around four specific research questions:

1. **What map grid size works best?** The city is split into small hexagon-shaped
   cells (using a system called H3) so demand can be predicted per-area instead of
   per-station. Which cell size — bigger or smaller — gives the best predictions?
2. **Does the shape of the grid matter?** H3 uses hexagons; a competing system
   called S2 uses rectangles/squares. Does one actually predict better than the
   other?
3. **Do fancy deep-learning models beat a simpler, well-tuned model?** Two advanced
   neural network models (a Transformer-based model called TFT, and a Graph Neural
   Network called ST-GNN) were compared against a more classical, tree-based model
   called LightGBM.
4. **Do better predictions actually lead to better bike rebalancing?** A more
   accurate forecast is only useful if it genuinely reduces the number of stations
   that run empty or overflow. This was tested directly with a rebalancing
   simulation, not assumed.

## 3. What data was used?

| Data | What it is | Size |
|---|---|---|
| Citi Bike trip history | Every real bike ride in NYC, Jan 2023 – Dec 2024 | ~79.4 million rides, ~15 GB |
| Weather | Hourly weather for NYC (temperature, rain, wind, etc.) | 2 years, no gaps |
| City events | NYC-permitted public events (parades, street fairs, etc.) | ~557k event records |
| Traffic speed | Live road traffic speed readings from NYC DOT | ~23.8 million readings |

Full sourcing details, known gaps, and honesty notes about data quality are in
[`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md).

## 4. Methodology — how the project was actually built

The project was done in **8 clearly separated phases**, each with its own
pass/fail checklist, so no phase started until the previous one was verified. Full
detail for every phase lives in [`docs/STATUS.md`](docs/STATUS.md) and
[`docs/phases/`](docs/phases/).

**Phase 1 — Getting the data ready.** All 90 raw trip files were loaded, cleaned,
and de-duplicated (99.7% of rows survived cleaning). Timestamps were carefully
converted to a consistent time zone so that daylight-saving-time changes wouldn't
silently corrupt the data. Weather, events, and traffic data were pulled in
alongside it.

**Phase 2 — Turning the city into a grid.** NYC was divided into small hexagonal
cells using the H3 spatial-indexing system. Only cells with real, sustained bike
activity were kept (1,483 out of 1,570 candidate cells, covering 99.98% of all
rides). A dense time-series table was built: one row per cell per 15-minute time
slot, for two full years, with zero missing rows.

**Phase 3 — A simple baseline, tested properly.** Before trying anything advanced,
a very simple "predict tomorrow will look like last week" baseline was built. Then
a first real model (LightGBM) was trained and had to beat that baseline on every
single target before the project was allowed to continue. It did — beating the
baseline by roughly 19–21%.

**Phase 4 — Deciding which extra information actually helps.** Extra features were
added one group at a time — calendar/seasonal patterns, rolling trends, weather,
events, traffic, and neighboring-cell information — and each group's real impact on
accuracy was measured, not assumed. Result: **only calendar/seasonal patterns and
short-term trend features actually helped.** Weather, events, and traffic did not
meaningfully improve predictions, and that negative result is reported honestly
rather than hidden.

**Phase 5 — Choosing the best grid size and shape.** Three hexagon sizes (H3
resolutions 8, 9, 10) were compared, along with the rectangular S2 grid at a
matched size. The comparison used a fair "skill score" (improvement over the naive
baseline) instead of raw error, because raw error is misleading when cell sizes
differ.

**Phase 6 — Training the advanced models.** Two deep-learning models — a
Transformer-based forecaster (TFT) and a Graph Neural Network (ST-GNN) — were
trained on a cloud GPU (Kaggle), alongside a carefully tuned version of LightGBM,
across every combination of grid type and size.

**Phase 7 — The final, one-time exam.** All models were evaluated on a completely
untouched two-month test period (Nov–Dec 2024) that had never been looked at during
development — exactly once, to keep the result honest.

**Phase 8 — Does this actually help in the real world?** The forecasts were fed
into a bike-rebalancing simulation: given predicted shortages and surpluses, which
bikes should be moved where? This was compared against doing nothing, and against
a "perfect" forecast that magically knows the future.

## 5. Results — what we actually found

**Best grid size:** The medium-sized hexagon grid (**H3 resolution 8**, 321 cells)
gave the best real skill, even though smaller cells looked better on raw error and
larger cells looked better on relative error. Skill score (improvement over the
naive baseline) is the only metric that isn't misleading here.

**Hexagons vs. squares:** Almost a tie. The S2 square-based grid scored marginally
higher on skill, but its cells were 47% bigger, which likely explains the whole
difference. **Conclusion: grid resolution matters much more than grid shape.**

**Simple model vs. deep learning:** The tuned **LightGBM model won**, beating both
deep-learning models on accuracy at both grid types. To be fair: the deep models
were only trained for 8 epochs on a free GPU and were *still improving* when
training stopped — so this shows "a well-tuned classical model beats an
undertrained deep model," not "deep learning doesn't work for this problem."

**Does better forecasting actually help rebalancing?** This is the most
interesting and honest finding of the project:
- Among the forecasting methods, LightGBM produced the *best* real-world
  rebalancing outcome — even better than a "perfect" forecast — because it tends
  to slightly under-predict, which means it moves bikes less aggressively, and in
  this system, moving bikes too often actually makes things worse.
- But overall, rebalancing at this cell size **did not clearly improve service**
  compared to doing nothing. The reason is structural, not a modeling failure:
  each cell covers a large enough area (about 7–8 real stations) that it almost
  never runs completely empty in the data. The real rebalancing opportunity likely
  exists at the individual-station level, which would need station-capacity data
  that simply isn't publicly available for this period.

**Where the model struggles most:** It under-predicts sudden demand spikes during
the evening rush hour (4–6 PM) in a small number of very busy areas — the single
most useful thing to fix in any future version of this project.

A full write-up with every number, chart, and phase-by-phase reasoning is in
[`docs/GeoPulse_Report.pdf`](docs/GeoPulse_Report.pdf), and the day-to-day running
log is in [`docs/STATUS.md`](docs/STATUS.md).

## 6. A working demo app

The project isn't just notebooks and metrics — it ships a working web app
([`app/`](app/)) where you can click anywhere on a live NYC map and get a real
demand forecast, the nearest docks with bikes available, and a chat assistant that
explains the prediction in plain language. See [`app/README.md`](app/README.md) to
run it locally.

## 7. Repository structure

```
configs/     All tunable settings (thresholds, model hyperparameters), never hardcoded in code
data/        Raw and processed data (not stored in this repo — see "Data" below)
src/         The actual pipeline code: data cleaning, spatial gridding, feature
             building, models, evaluation, rebalancing logic
scripts/     Runnable step-by-step scripts, numbered in the order they're meant to run
tests/       Automated tests that check for data leakage and correctness (146 tests)
outputs/     Trained model files, metrics, and generated reports
app/         The live web app (FastAPI backend + map-based frontend)
docs/        Full project report, phase-by-phase specs, and data source documentation
notebooks/   Exploratory data analysis only (all real logic lives in src/)
```

**Note on data:** the raw and processed datasets (tens of GB) are not included in
this repository — they're excluded via `.gitignore` and are fully reproducible by
running the numbered scripts in `scripts/` against the raw sources listed in
[`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md).

## 8. How to run it

```bash
pip install -r requirements.txt

# Run the first pipeline stage end-to-end (ingest -> clean -> weather -> events -> registry -> dev sample)
make phase1
make test          # run the automated test suite

# Or run the demo app directly (works out of the box, no API key needed)
python -m uvicorn app.server:app --reload --port 8000
```

Every pipeline stage can also be run individually and step by step — see the
numbered scripts in [`scripts/`](scripts/).

## 9. Tools and technologies used

- **Data processing:** Python, Polars, DuckDB, Pandas, Parquet
- **Spatial indexing:** H3, S2, GeoPandas, Shapely
- **Modeling:** LightGBM, Optuna (hyperparameter tuning), PyTorch, PyTorch
  Forecasting (TFT), PyTorch Geometric (ST-GNN)
- **App:** FastAPI backend, vanilla JS + map rendering frontend
- **Testing:** pytest (146 tests covering data leakage, correctness, and the app)

## 10. Honesty notes / known limitations

This project deliberately reports negative and inconclusive results instead of
hiding them:

- Weather, city events, and traffic data did **not** meaningfully improve
  predictions, despite the effort to include them.
- The deep-learning models were not trained to full convergence due to limited
  free GPU time, so the "LightGBM wins" result comes with that caveat.
- Rebalancing benefits could not be proven at the grid-cell level because no
  historical station-capacity (dock count) data is publicly available; capacity
  had to be statistically estimated.
- NYC events data only covers permitted public events, not ticketed arena events
  (e.g. Madison Square Garden, Barclays Center).

These are documented in detail, not swept under the rug — see
[`docs/STATUS.md`](docs/STATUS.md) for the full log.

---

*Built and documented by Divyesh Jawkhede, IIT Kharagpur.*
