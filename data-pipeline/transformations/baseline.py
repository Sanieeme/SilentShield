"""Behavioural baseline computation.

A customer's baseline is the "normal behaviour" picture referenced throughout
the top-level README (typical amount, typical hours, typical location,
typical devices). Downstream feature engineering and the risk engine compare
new activity against this baseline rather than against fixed global rules.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Set

import pandas as pd

from config import BASELINE_MIN_EVENTS


@dataclass(frozen=True)
class CustomerBaseline:
    customer_id: str
    avg_amount: float
    std_amount: float
    typical_hour_mean: float
    typical_hour_std: float
    known_locations: Set[str]
    known_devices: Set[str]
    avg_daily_tx_count: float
    sample_size: int

    @property
    def is_reliable(self) -> bool:
        """A baseline built from too few events shouldn't be trusted for
        anomaly scoring - better to flag as 'insufficient history' than
        raise false positives against noise."""
        return self.sample_size >= BASELINE_MIN_EVENTS


def compute_baselines(activity_df: pd.DataFrame) -> Dict[str, CustomerBaseline]:
    """`activity_df` must have columns: customer_id, amount, timestamp,
    location, device_id (device_id may contain NaNs, e.g. for auth-only rows
    without one). Typically this is atm + transaction events combined.
    """
    baselines: Dict[str, CustomerBaseline] = {}
    if activity_df.empty:
        return baselines

    df = activity_df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df["hour"] = df["timestamp"].dt.hour
    df["date"] = df["timestamp"].dt.date

    for customer_id, group in df.groupby("customer_id"):
        n_days = max(1, group["date"].nunique())
        baselines[customer_id] = CustomerBaseline(
            customer_id=customer_id,
            avg_amount=float(group["amount"].mean()),
            std_amount=float(group["amount"].std(ddof=0) or 0.0),
            typical_hour_mean=float(group["hour"].mean()),
            typical_hour_std=float(group["hour"].std(ddof=0) or 1.0),
            known_locations=set(group["location"].dropna().unique()),
            known_devices=set(group.get("device_id", pd.Series(dtype=str)).dropna().unique()),
            avg_daily_tx_count=float(len(group) / n_days),
            sample_size=len(group),
        )
    return baselines
