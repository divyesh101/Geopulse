PY := python
export PYTHONUTF8 := 1
export PYTHONIOENCODING := utf-8

.PHONY: help ingest clean weather events registry traffic trafficclean devsample \n        panel paneldev features featuresdev baseline baselinedev \n        phase1 phase1check phase2 phase2check phase3 phase3check test

help:
	@echo "make ingest     - raw Citi Bike CSV -> typed UTC parquet (data/raw/trips)"
	@echo "make clean      - data-quality report + cleaning rules -> data/interim"
	@echo "make weather    - pull Open-Meteo hourly weather -> data/external"
	@echo "make events     - filter/prepare NYC permitted events -> data/external"
	@echo "make registry   - build station registry -> data/spatial"
	@echo "make traffic    - pull DOT traffic speeds from Socrata -> data/raw/traffic"
	@echo "make trafficclean - profile + clean traffic -> data/interim"
	@echo "make devsample  - build the 7-day dev sample -> data/dev_sample"
	@echo "make panel      - build the dense region x 15-min demand panel -> data/processed"
	@echo "make paneldev   - same, on the 7-day dev sample"
	@echo "make phase1     - run the whole Phase 1 pipeline"
	@echo "make phase1check- verify the Phase 1 Definition of Done"
	@echo "make phase2     - build the panel (Phase 2)"
	@echo "make phase2check- verify the Phase 2 Definition of Done"
	@echo "make features   - panel -> model-ready feature table (Phase 3)"
	@echo "make baseline   - Seasonal Naive + 8 LightGBM models"
	@echo "make phase3     - features + baseline (the STOP-AND-VERIFY gate)"
	@echo "make phase3check- verify the Phase 3 Definition of Done"
	@echo "make test       - run pytest"

ingest:
	$(PY) scripts/01_ingest.py

clean:
	$(PY) scripts/02_clean.py

weather:
	$(PY) scripts/03_fetch_weather.py

events:
	$(PY) scripts/04_prepare_events.py

registry:
	$(PY) scripts/05_station_registry.py

traffic:
	$(PY) scripts/07_fetch_traffic.py

trafficclean:
	$(PY) scripts/08_clean_traffic.py

devsample:
	$(PY) scripts/06_dev_sample.py

panel:
	$(PY) scripts/10_build_panel.py

paneldev:
	$(PY) scripts/10_build_panel.py --dev-sample

phase1: ingest clean weather events registry traffic trafficclean devsample

phase1check:
	$(PY) scripts/09_phase1_check.py

phase2: paneldev panel

phase2check:
	$(PY) scripts/11_phase2_check.py

features:
	$(PY) scripts/12_build_features.py

featuresdev:
	$(PY) scripts/12_build_features.py --dev-sample

baseline:
	$(PY) scripts/13_train_baseline.py

baselinedev:
	$(PY) scripts/13_train_baseline.py --dev-sample

phase3: featuresdev baselinedev features baseline

phase3check:
	$(PY) scripts/14_phase3_check.py

test:
	$(PY) -m pytest tests -q
