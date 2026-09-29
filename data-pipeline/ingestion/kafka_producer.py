"""Publishes simulated events onto the three Kafka topics, one message per
event, JSON-encoded, keyed by customer_id (so all of one customer's events
land on the same partition and are processed in order downstream).

This module is a thin adapter around ingestion/simulator.py: it does not
contain any event-generation logic itself.
"""
from __future__ import annotations

import argparse
import json
import logging
import time

from config import KAFKA_BOOTSTRAP_SERVERS, TOPIC_ATM_EVENTS, TOPIC_AUTH_EVENTS, TOPIC_TRANSACTION_EVENTS
from ingestion.simulator import generate_events

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

TOPIC_BY_STREAM = {
    "atm": TOPIC_ATM_EVENTS,
    "transaction": TOPIC_TRANSACTION_EVENTS,
    "auth": TOPIC_AUTH_EVENTS,
}


def _json_default(o):
    if hasattr(o, "isoformat"):
        return o.isoformat()
    return str(o)


def publish_events(events: list[dict], bootstrap_servers: str = KAFKA_BOOTSTRAP_SERVERS,
                   throttle_seconds: float = 0.0) -> int:
    from kafka import KafkaProducer  # local import: only required when actually talking to Kafka

    producer = KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v, default=_json_default).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
        acks="all",
    )
    sent = 0
    try:
        for event in events:
            topic = TOPIC_BY_STREAM[event["stream"]]
            producer.send(topic, key=event["customer_id"], value=event)
            sent += 1
            if throttle_seconds:
                time.sleep(throttle_seconds)
        producer.flush()
    finally:
        producer.close()
    return sent


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish simulated SilentShield events to Kafka")
    parser.add_argument("--bootstrap-servers", default=KAFKA_BOOTSTRAP_SERVERS)
    parser.add_argument("--customers", type=int, default=25)
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--throttle-seconds", type=float, default=0.0,
                        help="Delay between messages, to simulate a live stream instead of a burst replay")
    args = parser.parse_args()

    events = generate_events(args.customers, args.days)
    logger.info("Generated %d simulated events", len(events))
    sent = publish_events(events, args.bootstrap_servers, args.throttle_seconds)
    logger.info("Published %d events to Kafka at %s", sent, args.bootstrap_servers)


if __name__ == "__main__":
    main()
