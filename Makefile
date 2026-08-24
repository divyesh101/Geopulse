PY := python
export PYTHONUTF8 := 1
export PYTHONIOENCODING := utf-8

.PHONY: help ingest clean weather events registry traffic trafficclean devsample phase1 test

help:
	@echo "make ingest     - raw Citi Bike CSV -> typed UTC parquet (data/raw/trips)"
	@echo "make clean      - data-quality report + cleaning rules -> data/interim"
	@echo "make weather    - pull Open-Meteo hourly weather -> data/external"
	@echo "make events     - filter/prepare NYC permitted events -> data/external"
	@echo "make registry   - build station registry -> data/spatial"
	@echo "make traffic    - pull DOT traffic speeds from Socrata -> data/raw/traffic"
	@echo "make trafficclean - profile + clean traffic -> data/interim"
	@echo "make devsample  - build the 7-day dev sample -> data/dev_sample"
	@echo "make phase1     - run the whole Phase 1 pipeline"
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

phase1: ingest clean weather events registry traffic trafficclean devsample

test:
	$(PY) -m pytest tests -q
