"""Consumes raw events from Kafka and runs them through the same
validate -> enrich -> feature-engineer -> sink pipeline as
processing/batch_runner.py, in micro-batches (poll for up to
`batch_seconds`, process whatever arrived, repeat).

Baselines are recomputed once per micro-batch from that batch's own
validated activity. In a real deployment this would instead read baselines
maintained incrementally in the warehouse; recomputing per-batch here keeps
the demo self-contained without a second moving part.
"""
from __future__ import annotations

import argparse
import json
import logging
import time
from collections import defaultdict

import pandas as pd

from config import KAFKA_BOOTSTRAP_SERVERS, TOPIC_ATM_EVENTS, TOPIC_AUTH_EVENTS, TOPIC_TRANSACTION_EVENTS
from processing.sink import write_features_to_warehouse, write_to_data_lake
from processing.validation import validate_events
from transformations.baseline import compute_baselines
from transformations.features import build_feature_table

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

STREAM_BY_TOPIC = {
    TOPIC_ATM_EVENTS: "atm",
    TOPIC_TRANSACTION_EVENTS: "transaction",
    TOPIC_AUTH_EVENTS: "auth",
}


def _process_batch(raw_by_stream: dict) -> pd.DataFrame:
    valid_by_stream = {}
    for stream, rows in raw_by_stream.items():
        if not rows:
            valid_by_stream[stream] = pd.DataFrame()
            continue
        df = pd.DataFrame(rows)
        result = validate_events(df, stream)
        logger.info("%s: %d valid, %d rejected", stream, len(result.valid), len(result.rejected))
        write_to_data_lake(result.valid, stream)
        valid_by_stream[stream] = result.valid

    activity = pd.concat(
        [valid_by_stream.get("atm", pd.DataFrame()), valid_by_stream.get("transaction", pd.DataFrame())],
        ignore_index=True,
    )
    baselines = compute_baselines(activity) if not activity.empty else {}
    features = build_feature_table(
        valid_by_stream.get("atm", pd.DataFrame()),
        valid_by_stream.get("transaction", pd.DataFrame()),
        valid_by_stream.get("auth", pd.DataFrame()),
        baselines,
    )
    write_features_to_warehouse(features)
    return features


def run(bootstrap_servers: str = KAFKA_BOOTSTRAP_SERVERS, batch_seconds: float = 10.0,
       max_batches: int | None = None) -> None:
    from kafka import KafkaConsumer  # local import: only required when actually talking to Kafka

    consumer = KafkaConsumer(
        TOPIC_ATM_EVENTS, TOPIC_TRANSACTION_EVENTS, TOPIC_AUTH_EVENTS,
        bootstrap_servers=bootstrap_servers,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        consumer_timeout_ms=int(batch_seconds * 1000),
    )

    batches_done = 0
    try:
        while max_batches is None or batches_done < max_batches:
            raw_by_stream: dict = defaultdict(list)
            deadline = time.time() + batch_seconds
            for message in consumer:
                stream = STREAM_BY_TOPIC.get(message.topic)
                if stream:
                    raw_by_stream[stream].append(message.value)
                if time.time() >= deadline:
                    break
            if raw_by_stream:
                _process_batch(raw_by_stream)
            batches_done += 1
    finally:
        consumer.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Consume SilentShield events from Kafka and run the pipeline")
    parser.add_argument("--bootstrap-servers", default=KAFKA_BOOTSTRAP_SERVERS)
    parser.add_argument("--batch-seconds", type=float, default=10.0)
    args = parser.parse_args()
    run(args.bootstrap_servers, args.batch_seconds)


if __name__ == "__main__":
    main()
