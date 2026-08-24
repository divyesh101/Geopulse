"""GeoPulse Phase 6 - TFT + ST-GNN on a Kaggle GPU.

Paste this into a Kaggle notebook cell (or run as a script) after attaching the
exported bundle as a dataset. It carries its own copies of the model definitions so
the notebook is self-contained - no repo checkout needed on Kaggle.

SETUP
-----
1. Locally:  python scripts/20_export_deep_bundle.py --spatial h3 --resolution 9
             python scripts/20_export_deep_bundle.py --spatial s2 --resolution <matched>
2. Upload `data/processed/deep_bundle_h39/` (and the S2 one) as a Kaggle Dataset,
   e.g. named `geopulse-deep-bundles`.
3. Notebook settings: Accelerator = GPU T4 x2 (or P100), Internet = off.
4. Set BUNDLE_DIR below to the attached path and run.
5. Download `/kaggle/working/deep_metrics_*.json` and `*.pt` back into
   `outputs/metrics/` and `outputs/models/` locally, then run Phase 7.

WHY THIS RUNS HERE AND THE REST RUNS LOCALLY
--------------------------------------------
The LightGBM, DuckDB and polars stages are CPU- and disk-bound and need the 5.9 GB
feature table, so they stay on the workstation. Only these two models want a GPU, and
they need just the ~400 MB demand/calendar/weather/graph bundle.
"""

import json
import time
from pathlib import Path

import numpy as np
import torch

# ----------------------------------------------------------------- configuration
BUNDLE_DIR = Path("/kaggle/input/geopulse-deep-bundles/deep_bundle_h39")
OUT_DIR = Path("/kaggle/working")
EPOCHS = 8
STGNN_BATCH = 8            # one sample = one timestamp = every region at once
TFT_BATCH = 512
BATCHES_PER_EPOCH = 500
SEASONAL_LAGS = [96, 672]  # same-time-yesterday, same-time-last-week
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# The model definitions are identical to src/models/deep.py in the repo. Kaggle
# notebooks cannot import from the repo, so they are inlined via exec of the file if
# present, else copy src/models/deep.py into a dataset and point at it here.
DEEP_SRC = Path("/kaggle/input/geopulse-deep-bundles/deep.py")
if DEEP_SRC.exists():
    exec(DEEP_SRC.read_text())  # noqa: S102 - trusted, self-authored source
else:
    raise SystemExit(
        "Upload src/models/deep.py alongside the bundle so the model definitions "
        "match the repo exactly - re-implementing them here would let the Kaggle "
        "run and the local run silently diverge."
    )


def run(model_name: str) -> dict:
    bundle = Bundle.load(BUNDLE_DIR)  # noqa: F821 - from deep.py
    horizons = bundle.meta["horizons"]
    scaled = bundle.scaled_demand()
    weather = bundle.scaled_weather()
    static_np = bundle.scaled_static()
    static_t = torch.from_numpy(static_np).float().to(DEVICE)
    edges = torch.from_numpy(bundle.edges.astype(np.int64)).to(DEVICE)

    window = 24 if model_name == "stgnn" else 96
    batch_size = STGNN_BATCH if model_name == "stgnn" else TFT_BATCH
    seasonal_max = max(SEASONAL_LAGS) + window
    train_anchors = valid_window_starts(bundle, "train", window, seasonal_max)  # noqa: F821
    valid_anchors = valid_window_starts(bundle, "validate", window, seasonal_max)  # noqa: F821
    print(f"{model_name}: {len(train_anchors):,} train / {len(valid_anchors):,} valid anchors")

    rng = np.random.default_rng(42)
    torch.manual_seed(42)
    if model_name == "stgnn":
        n_dynamic = 2 + 2 * len(SEASONAL_LAGS) + bundle.calendar.shape[1] + weather.shape[1]
        model = STGNN(n_dynamic, static_np.shape[1], len(horizons)).to(DEVICE)  # noqa: F821
    else:
        model = CompactTFT(2 + weather.shape[1], bundle.calendar.shape[1],  # noqa: F821
                           static_np.shape[1], len(horizons)).to(DEVICE)
    print(f"  parameters: {sum(p.numel() for p in model.parameters()):,}")
    optimiser = torch.optim.Adam(model.parameters(), lr=1e-3)

    def make_batch(anchors, train: bool):
        offsets = np.arange(-window + 1, 1)
        idx = anchors[:, None] + offsets[None, :]
        if model_name == "stgnn":
            demand = scaled[idx]
            n = demand.shape[2]
            calendar = bundle.calendar[idx][:, :, None, :].repeat(n, axis=2)
            wx = weather[idx][:, :, None, :].repeat(n, axis=2)
            seasonal = [scaled[idx - lag] for lag in SEASONAL_LAGS]
            dynamic = np.concatenate([demand, *seasonal, calendar, wx], axis=-1)
            targets = np.stack([bundle.demand[anchors + h] for h in horizons], axis=2)
            return ((torch.from_numpy(dynamic).float().to(DEVICE),),
                    torch.from_numpy(targets.astype(np.float32)).to(DEVICE))
        regions = rng.integers(0, bundle.n_regions, size=len(anchors))
        observed = np.concatenate([scaled[idx, regions[:, None]], weather[idx]], axis=-1)
        known = bundle.calendar[idx]
        targets = np.stack([bundle.demand[anchors + h, regions] for h in horizons], axis=1)
        return ((torch.from_numpy(observed).float().to(DEVICE),
                 torch.from_numpy(known).float().to(DEVICE),
                 torch.from_numpy(static_np[regions]).float().to(DEVICE)),
                torch.from_numpy(targets.astype(np.float32)).to(DEVICE))

    def forward(inputs):
        return (model(inputs[0], static_t, edges) if model_name == "stgnn"
                else model(*inputs))

    best, history = float("inf"), []
    for epoch in range(1, EPOCHS + 1):
        model.train()
        started, losses = time.perf_counter(), []
        for _ in range(BATCHES_PER_EPOCH):
            anchors = rng.choice(train_anchors, size=batch_size, replace=False)
            inputs, targets = make_batch(anchors, True)
            optimiser.zero_grad()
            loss = poisson_nll(forward(inputs), targets)  # noqa: F821
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimiser.step()
            losses.append(float(loss.detach()))

        model.eval()
        preds, actuals = [], []
        with torch.no_grad():
            for i in range(0, min(len(valid_anchors), batch_size * 120), batch_size):
                anchors = valid_anchors[i:i + batch_size]
                if len(anchors) == 0:
                    break
                inputs, targets = make_batch(anchors, False)
                preds.append(forward(inputs).cpu().numpy().reshape(-1, len(horizons), 2))
                actuals.append(targets.cpu().numpy().reshape(-1, len(horizons), 2))
        prediction, actual = np.concatenate(preds), np.concatenate(actuals)
        mae = float(np.abs(prediction - actual).mean())
        history.append({"epoch": epoch, "loss": float(np.mean(losses)),
                        "valid_mae": mae, "seconds": round(time.perf_counter() - started, 1)})
        print(f"  epoch {epoch}/{EPOCHS} loss={history[-1]['loss']:.4f} "
              f"MAE={mae:.4f} ({history[-1]['seconds']:.0f}s)")
        if mae < best:
            best = mae
            torch.save(model.state_dict(), OUT_DIR / f"{model_name}_{bundle.meta['tag']}.pt")

    result = {"model": model_name, "tag": bundle.meta["tag"], "device": DEVICE,
              "best_valid_mae": best, "history": history}
    (OUT_DIR / f"deep_metrics_{model_name}_{bundle.meta['tag']}.json").write_text(
        json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    print(f"device: {DEVICE}")
    if DEVICE == "cuda":
        print(torch.cuda.get_device_name(0),
              f"{torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    for name in ("stgnn", "tft"):
        print(f"\n=== {name} ===")
        print(run(name))
