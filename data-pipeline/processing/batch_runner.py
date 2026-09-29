"""Batch entry point: validate -> enrich -> feature-engineer -> sink,
over a Parquet file of raw simulated events (as produced by
ingestion/simulator.py). This is the non-Kafka path used for local
development, tests, and CI, and mirrors exactly what
processing/kafka_consumer.py does per micro-batch.
"""
from __future__ import annotations

import argparse
import logging
import os

import pandas as pd

from processing.sink import write_features_to_warehouse, write_to_data_lake
from processing.validation import validate_events
from transformations.baseline import compute_baselines
from transformations.features import build_feature_table

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def run(events_path: str, features_out: str | None = None) -> pd.DataFrame:
    raw = pd.read_parquet(events_path)

    frames = {}
    for stream in ("atm", "transaction", "auth"):
        subset = raw[raw["stream"] == stream].dropna(axis=1, how="all") if "stream" in raw.columns else pd.DataFrame()
        result = validate_events(subset, stream) if not subset.empty else None
        if result is None:
            frames[stream] = pd.DataFrame()
            continue
        logger.info("%s: %d valid, %d rejected (%.1f%%)", stream, len(result.valid), len(result.rejected),
                   100 * result.rejection_rate)
        for path_written in [write_to_data_lake(result.valid, stream)]:
            if path_written:
                logger.info("wrote %s -> %s", stream, path_written)
        frames[stream] = result.valid

    activity = pd.concat([frames["atm"], frames["transaction"]], ignore_index=True) if not (
        frames["atm"].empty and frames["transaction"].empty) else pd.DataFrame(
        columns=["customer_id", "amount", "timestamp", "location", "device_id"])

    baselines = compute_baselines(activity) if not activity.empty else {}
    features = build_feature_table(frames["atm"], frames["transaction"], frames["auth"], baselines)

    if features_out:
        out_dir = os.path.dirname(features_out)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        features.to_parquet(features_out, index=False)
        logger.info("wrote %d feature rows -> %s", len(features), features_out)

    written = write_features_to_warehouse(features)
    logger.info("wrote %d feature rows to warehouse", written)

    return features


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the SilentShield batch pipeline over a Parquet event file")
    parser.add_argument("--in", dest="events_path", required=True)
    parser.add_argument("--out", dest="features_out", default=None)
    args = parser.parse_args()
    run(args.events_path, args.features_out)


if __name__ == "__main__":
    main()
