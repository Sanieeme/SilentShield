"""Synthetic banking-event generator.

Generates a population of simulated customers, each with a stable behavioural
pattern (typical hours, typical location, typical amounts, typical devices),
plus a small number of injected anomalies (odd hours, new locations/devices,
larger amounts, failed auth bursts) so the downstream pipeline has something
realistic to detect.

No real customer data of any kind is used or referenced.
"""
from __future__ import annotations

import argparse
import os
import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List

import pandas as pd

from ingestion.event_models import AtmEvent, AuthEvent, AuthMethod, TransactionChannel, TransactionEvent

LOCATIONS = ["Sandton", "Rosebank", "Midrand", "Pretoria CBD", "Fourways", "Soweto"]
DEVICES_POOL_SIZE = 3


@dataclass
class CustomerProfile:
    customer_id: str
    account_id: str
    home_location: str
    typical_hour_mean: float          # 0-23, centre of the customer's usual activity window
    typical_hour_std: float
    typical_amount_mean: float
    typical_amount_std: float
    devices: List[str] = field(default_factory=list)
    daily_tx_rate: float = 1.5        # average transactions per day


def _make_population(n_customers: int, seed: int) -> List[CustomerProfile]:
    rng = random.Random(seed)
    profiles = []
    for i in range(n_customers):
        customer_id = f"CUST-{1000 + i}"
        home = rng.choice(LOCATIONS)
        devices = [f"DEV-{customer_id}-{d}" for d in range(rng.randint(1, DEVICES_POOL_SIZE))]
        profiles.append(CustomerProfile(
            customer_id=customer_id,
            account_id=f"ACC-{customer_id}",
            home_location=home,
            typical_hour_mean=rng.uniform(8, 19),
            typical_hour_std=rng.uniform(1.5, 3.5),
            typical_amount_mean=rng.uniform(150, 1200),
            typical_amount_std=rng.uniform(30, 250),
            devices=devices,
            daily_tx_rate=rng.uniform(0.5, 4.0),
        ))
    return profiles


def _sample_hour(rng: random.Random, profile: CustomerProfile, anomalous: bool) -> int:
    if anomalous:
        # push into the night window regardless of the customer's normal pattern
        return rng.choice(list(range(0, 5)) + list(range(23, 24)))
    hour = int(round(rng.gauss(profile.typical_hour_mean, profile.typical_hour_std)))
    return max(0, min(23, hour))


def _sample_amount(rng: random.Random, profile: CustomerProfile, anomalous: bool) -> float:
    if anomalous:
        return round(profile.typical_amount_mean * rng.uniform(4, 12), 2)
    return round(max(50.0, rng.gauss(profile.typical_amount_mean, profile.typical_amount_std)), 2)


def _sample_location(rng: random.Random, profile: CustomerProfile, anomalous: bool) -> str:
    if anomalous:
        others = [loc for loc in LOCATIONS if loc != profile.home_location]
        return rng.choice(others)
    return profile.home_location


def _sample_device(rng: random.Random, profile: CustomerProfile, anomalous: bool) -> str:
    if anomalous or not profile.devices:
        return f"DEV-UNKNOWN-{uuid.uuid4().hex[:8]}"
    return rng.choice(profile.devices)


def generate_events(n_customers: int, days: int, anomaly_rate: float = 0.04,
                    seed: int = 42) -> List[dict]:
    """Returns a flat list of event dicts (already schema-validated), spanning
    `days` days ending now, for `n_customers` simulated customers."""
    rng = random.Random(seed)
    profiles = _make_population(n_customers, seed)
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)

    events: List[dict] = []

    for profile in profiles:
        expected_tx_count = max(1, int(profile.daily_tx_rate * days))
        for _ in range(expected_tx_count):
            anomalous = rng.random() < anomaly_rate
            offset_days = rng.uniform(0, days)
            ts = start + timedelta(days=offset_days)
            hour = _sample_hour(rng, profile, anomalous)
            ts = ts.replace(hour=hour, minute=rng.randint(0, 59), second=rng.randint(0, 59))
            ts = min(ts, now - timedelta(seconds=1))

            amount = _sample_amount(rng, profile, anomalous)
            location = _sample_location(rng, profile, anomalous)
            device = _sample_device(rng, profile, anomalous)

            channel = rng.choice(list(TransactionChannel))

            if channel == TransactionChannel.ATM:
                evt = AtmEvent(
                    customer_id=profile.customer_id,
                    account_id=profile.account_id,
                    atm_id=f"ATM-{location.replace(' ', '')}-{rng.randint(1, 9)}",
                    amount=amount,
                    location=location,
                    device_id=device,
                    timestamp=ts,
                )
                events.append({"stream": "atm", **evt.model_dump()})
            else:
                evt = TransactionEvent(
                    customer_id=profile.customer_id,
                    account_id=profile.account_id,
                    transaction_type="WITHDRAWAL" if rng.random() < 0.7 else "PAYMENT",
                    amount=amount,
                    channel=channel,
                    device_id=device,
                    location=location,
                    timestamp=ts,
                )
                events.append({"stream": "transaction", **evt.model_dump()})

            # each transaction/withdrawal is preceded by an auth attempt
            auth_success = not anomalous or rng.random() > 0.3
            auth_ts = ts - timedelta(seconds=rng.randint(5, 120))
            auth_ts = max(auth_ts, start)
            auth_evt = AuthEvent(
                customer_id=profile.customer_id,
                success=auth_success,
                method=AuthMethod.REAL_PIN,
                device_id=device,
                location=location,
                timestamp=auth_ts,
            )
            events.append({"stream": "auth", **auth_evt.model_dump()})

            # occasionally simulate a short burst of failed auth attempts
            if anomalous and rng.random() < 0.5:
                for _ in range(rng.randint(1, 3)):
                    fail_ts = auth_ts - timedelta(seconds=rng.randint(5, 60))
                    fail_ts = max(fail_ts, start)
                    fail_evt = AuthEvent(
                        customer_id=profile.customer_id,
                        success=False,
                        method=AuthMethod.UNKNOWN,
                        device_id=device,
                        location=location,
                        timestamp=fail_ts,
                    )
                    events.append({"stream": "auth", **fail_evt.model_dump()})

    events.sort(key=lambda e: e["timestamp"])
    return events


def events_to_dataframe(events: List[dict]) -> pd.DataFrame:
    df = pd.DataFrame(events)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate simulated SilentShield banking events")
    parser.add_argument("--customers", type=int, default=25)
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--anomaly-rate", type=float, default=0.04)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=str, default="data_lake/events.parquet")
    args = parser.parse_args()

    events = generate_events(args.customers, args.days, args.anomaly_rate, args.seed)
    df = events_to_dataframe(events)
    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    df.to_parquet(args.out, index=False)
    print(f"Wrote {len(df)} simulated events to {args.out}")


if __name__ == "__main__":
    main()
