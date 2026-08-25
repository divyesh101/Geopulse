# GeoPulse app

A map-first assistant over the Phase 1–8 models. Ask where you are; it forecasts how
bikes will move around you and explains why — using only what the models actually use.

## Run it

```bash
python -m uvicorn app.server:app --reload --port 8000
```

Open <http://127.0.0.1:8000>.

That works with **no API key** — the assistant falls back to a deterministic keyword
router that calls the same tools. To use an LLM instead, set a key in the environment
**before** starting the server. Never put it in a file in this repo.

```bash
# bash
export MISTRAL_API_KEY="..."        # or ANTHROPIC_API_KEY
python -m uvicorn app.server:app --port 8000
```

```powershell
# PowerShell (persists; open a new shell afterwards)
setx MISTRAL_API_KEY "..."
```

| variable | effect |
|---|---|
| `MISTRAL_API_KEY` | uses Mistral (default `mistral-large-2512`) |
| `ANTHROPIC_API_KEY` | uses Claude (default `claude-sonnet-5`) |
| `GEOPULSE_LLM` | force `mistral`, `claude`, or `router` |
| `MISTRAL_MODEL` / `ANTHROPIC_MODEL` | override the model id |

The badge in the panel header shows which brain is live. If an LLM call fails for any
reason the request degrades to the router rather than erroring, and says so.

## What it does

- **Map** — every H3-8 or S2-13 cell shaded by predicted pickups (log scale: a few
  Midtown cells carry most of the demand). Click any cell to forecast it.
- **Search** — offline gazetteer over 2,459 station names and 19,011 geocoded NYC
  landmarks. No external geocoding API.
- **Cards** — the four nearest docks with predicted pickups, returns, and an
  availability verdict.
- **Chat** — natural questions, with follow-ups ("why?", "compare models").
- **Controls** — switch between all five models and both spatial grids live.

## Three things it deliberately will not do

**It will not tell you how many bikes are at a dock.** The models forecast *trips*.
Citi Bike publishes no historical dock occupancy for 2023–24, so a bike count would be
an invention. Instead every station gets a flow-pressure verdict — *draining*,
*balanced*, *filling* — derived from predicted pickups versus returns.

**It will not blame demand on events, weather or traffic.** The Phase 4 ablation tested
all three, twice, and measured them at roughly zero (events −0.01%, weather −0.05%,
traffic −0.05% MAE). They are excluded from the deployed model. Nearby events still
appear, tagged `influences_forecast: false`, because people want to know — but the
*explanation* only ever cites features the model really consumes: recent momentum,
weekly seasonality, and time of week.

**It is not live.** The models cover Jan 2023 – Dec 2024. A request for "now" is mapped
to the equivalent 2024 weekday and clock time and labelled *typical conditions*.

One more approximation, surfaced on every card: the models forecast **cells** of
~0.74 km² holding ~8 stations. Per-station numbers are the cell's forecast split by
that station's historical share of its cell's trips. Real per-station modelling would
mean re-running Phases 2–6 with 2,459 regions.

## Layout

```
app/
  server.py          FastAPI; every route is a shim over the same tools the agent uses
  static/            index.html · app.css · app.js
src/serving/
  engine.py          all five models behind one call, with the deep tensor path
  stations.py        cell -> station disaggregation by historical share
  context.py         explanations, split into drivers vs non-causal context
  predict.py         the Phase 8 contract (unchanged)
src/agent/
  gazetteer.py       offline place lookup
  tools.py           the six tools
  assistant.py       Mistral / Claude / router, one payload shape
```

## API

`GET /api/config` · `GET /api/geojson` · `GET /api/overview` · `GET /api/stations`
`GET /api/place` · `GET /api/station_forecast` · `GET /api/explain` · `GET /api/compare`
`POST /api/chat` · `GET /api/health`

Interactive docs at `/api/docs`.
