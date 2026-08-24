# Data Sources

**Date range for all sources below: Jan 1, 2023 - Dec 31, 2024** (matches the Citi
Bike trip data actually on hand).

## Required for v1

### Citi Bike trip history
- **Source:** https://citibikenyc.com/system-data (monthly CSV/zip files)
- **Period:** Jan 2023 - Dec 2024 (already acquired: 90 CSVs, ~15 GB)
- **Fields used:** ride_id, rideable_type, started_at, ended_at, start/end
  station_id + name + lat/lng, member_casual
- **Note:** the station roster changes over this period (system expanded through
  2023-2024) - use *actual trip activity* to define active stations/regions per
  Phase 1-2, not any static station list, since a roster reflects the system at
  whatever date it was pulled, not what existed at each point in the training window.

### Weather
- **Source:** Open-Meteo Historical API (https://archive-api.open-meteo.com/v1/archive,
  free, no key) or NOAA LCD
- **Reference point:** Central Park (lat 40.7831, lon -73.9712)
- **Fields:** temperature, precipitation, humidity, wind speed/direction, snow,
  visibility - hourly
- Join rule: `weather_timestamp <= forecast_time`, latest available reading, no
  future readings. See Phase 4 for missing-value handling.
- **Status:** pulled by `scripts/03_fetch_weather.py` into `data/external/weather_hourly.parquet`.

### Events / festivals
- **Source:** NYC Open Data - "NYC Permitted Event Information - Historical"
- Filter to 2023-2024
- Fields: event name, start/end timestamp, event type, borough, location
- **Geocoding gap:** the export has NO lat/lng - only a free-text street description
  ("BROADWAY between WEST 43 STREET and WEST 44 STREET"), plus borough, community
  board and police precinct. Mapping events to H3 cells therefore requires
  geocoding the street description or falling back to a coarser polygon join.
  See Phase 4 for the chosen approach.
- **Known gap:** covers *permitted* public events (parades, street fairs, block
  parties) - it does not reliably capture ticketed arena events (MSG, Barclays,
  stadiums). Documented limitation, not a bug.

### Traffic
- **Source:** NYC Open Data - "DOT Traffic Speeds"
  https://data.cityofnewyork.us/Transportation/DOT-traffic-speeds-after-2018-07-01/wa4a-ebba
- **STATUS: the local export is unusable.** `DOT_traffic_speeds_after_2018-07-01_20260824.csv`
  contains 194,130 rows spanning **2018-07-26 to 2018-07-30 only** - the Socrata UI
  export was row-capped, not date-filtered. Zero overlap with the 2023-2024 window.
- **To fix:** re-pull via the Socrata API with an explicit date filter and paging, e.g.
  `https://data.cityofnewyork.us/resource/wa4a-ebba.csv?$where=data_as_of between '2023-01-01T00:00:00' and '2025-01-01T00:00:00'&$limit=...&$offset=...`
  The raw feed is ~1 reading/link/minute across ~1000 links, so 2 years is on the
  order of 10^9 rows. Pull **pre-aggregated** (hourly or 15-min mean speed per link)
  via `$select`/`$group` server-side rather than downloading raw.
- Derived features: `traffic_speed_mean/min`, `congestion_index`,
  `travel_time_index`, `traffic_change_15m`. Test whether these actually help in
  the ablation study (Phase 4) - don't assume they will. Family F of the ablation is
  skipped and documented as skipped until the data is re-pulled.

### Station roster (supplementary)
- `citibike_stations_data.csv`: id, name, latitude, longitude for ~2.3k stations.
- **No capacity/dock count column** - so Phase 8 uses statistical capacity
  estimation as planned.
- Used only as a cross-check on the trip-derived station registry, never as the
  definition of "active station" (see the roster note above).

## Deferred - not required for v1, add later if pursued

### Station capacity / dock counts
- Phase 8 estimates capacity statistically from trip-flow patterns (q95 of daily
  cumulative net-flow range) because no ground-truth capacity data is on hand.
- Citi Bike's live GBFS feed (`station_information.json`) has *current* capacity
  only - not historical. A historical GBFS archive would be needed for accurate
  2023-2024 capacity.
- Until then the statistical estimate is the real v1 approach, not a placeholder.

### Road quality / pavement condition
- NYC DOT pavement rating + resurfacing records. Low priority.

### Subway/transit proximity
- MTA subway entrance locations. Plausible demand driver, optional.

### Venue-specific event schedules
- Would fill the "ticketed arena events" gap. No single clean public dataset.

### School calendar
- NYC DOE academic calendar. Minor effect. Skip unless ablation shows a gap.

## Not a data pull - handle in code
- **Public holidays:** Python `holidays` library.
- **Sunrise/sunset / daylight:** `astral` or a formula; not worth sourcing externally.
