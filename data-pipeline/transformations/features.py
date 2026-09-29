"""Behavioural feature engineering.

Builds the feature vector named in the top-level README:
  customer_id, transactions_last_24h, average_transaction_amount,
  failed_authentication_attempts, new_device, new_location,
  night_transactions, transaction_velocity, behaviour_deviation_score

`behaviour_deviation_score` is a simple, explainable 0-1 blend of signals
(not a black-box model) so it's easy to reason about and to hand to the
Phase 5 machine-learning experiments as a labelled baseline feature.
"""
from __future__ import annotations

from typing import Dict

import pandas as pd

from config import HIGH_RISK_DEVIATION_SCORE, MEDIUM_RISK_DEVIATION_SCORE, NIGHT_END_HOUR, NIGHT_START_HOUR
from transformations.baseline import CustomerBaseline


def _is_night(hour: int) -> bool:
    if NIGHT_START_HOUR > NIGHT_END_HOUR:
        return hour >= NIGHT_START_HOUR or hour < NIGHT_END_HOUR
    return NIGHT_START_HOUR <= hour < NIGHT_END_HOUR


def _amount_deviation(amount_mean: float, baseline: CustomerBaseline) -> float:
    if not baseline.is_reliable or baseline.avg_amount <= 0:
        return 0.0
    spread = max(baseline.std_amount, baseline.avg_amount * 0.15)  # floor so tiny std doesn't explode
    z = abs(amount_mean - baseline.avg_amount) / spread
    return min(1.0, z / 4.0)  # squash: ~4 std devs away saturates the signal


def _hour_deviation(hours: pd.Series, baseline: CustomerBaseline) -> float:
    if not baseline.is_reliable or hours.empty:
        return 0.0
    spread = max(baseline.typical_hour_std, 1.0)
    z = (abs(hours - baseline.typical_hour_mean) / spread).mean()
    return min(1.0, z / 3.0)


def build_feature_row(customer_id: str, activity: pd.DataFrame, auth: pd.DataFrame,
                      baseline: CustomerBaseline | None, window_hours: int = 24) -> Dict:
    """`activity` = this customer's ATM+transaction rows already filtered to
    the lookback window. `auth` = this customer's auth rows in the same
    window. Both may be empty."""
    now = pd.Timestamp.now(tz="UTC")

    tx_count = len(activity)
    avg_amount = float(activity["amount"].mean()) if tx_count else 0.0

    if not auth.empty:
        # `success` can arrive as object dtype (e.g. after being split out of a
        # mixed-schema raw events file where other streams left it all-NaN).
        # `~` on an object-dtype column of Python bools does a bitwise
        # complement (~True == -2), not a logical NOT - always coerce first.
        success = auth["success"].fillna(False).astype(bool)
        failed_auth = int((~success).sum())
    else:
        failed_auth = 0

    devices_seen = set(activity.get("device_id", pd.Series(dtype=str)).dropna().unique()) \
        | set(auth.get("device_id", pd.Series(dtype=str)).dropna().unique())
    locations_seen = set(activity.get("location", pd.Series(dtype=str)).dropna().unique()) \
        | set(auth.get("location", pd.Series(dtype=str)).dropna().unique())

    known_devices = baseline.known_devices if baseline else set()
    known_locations = baseline.known_locations if baseline else set()

    new_device = bool(devices_seen - known_devices) if baseline and baseline.is_reliable else False
    new_location = bool(locations_seen - known_locations) if baseline and baseline.is_reliable else False

    hours = pd.to_datetime(activity["timestamp"], utc=True).dt.hour if tx_count else pd.Series(dtype=int)
    night_tx = int(hours.apply(_is_night).sum()) if tx_count else 0

    velocity = round(tx_count / window_hours, 4)  # transactions per hour over the window

    if baseline and baseline.is_reliable:
        amount_dev = _amount_deviation(avg_amount, baseline) if tx_count else 0.0
        hour_dev = _hour_deviation(hours, baseline) if tx_count else 0.0
        novelty_dev = 0.3 * new_device + 0.3 * new_location
        velocity_dev = min(1.0, velocity / max(baseline.avg_daily_tx_count / 24.0, 0.05) - 1.0) \
            if baseline.avg_daily_tx_count > 0 else 0.0
        velocity_dev = max(0.0, min(1.0, velocity_dev))
        failed_auth_dev = min(1.0, failed_auth / 3.0)

        deviation_score = round(
            0.30 * amount_dev + 0.20 * hour_dev + 0.20 * novelty_dev +
            0.15 * velocity_dev + 0.15 * failed_auth_dev,
            4,
        )
        insufficient_history = False
    else:
        # Not enough history to trust a deviation score - surface that explicitly
        # rather than silently defaulting to "normal".
        deviation_score = 0.0
        insufficient_history = True

    return {
        "customer_id": customer_id,
        "window_end": now.isoformat(),
        "transactions_last_24h": tx_count,
        "average_transaction_amount": round(avg_amount, 2),
        "failed_authentication_attempts": failed_auth,
        "new_device": new_device,
        "new_location": new_location,
        "night_transactions": night_tx,
        "transaction_velocity": velocity,
        "behaviour_deviation_score": deviation_score,
        "insufficient_history": insufficient_history,
        "risk_level": _risk_level(deviation_score, insufficient_history),
    }


def _risk_level(score: float, insufficient_history: bool) -> str:
    if insufficient_history:
        return "UNKNOWN"
    if score >= HIGH_RISK_DEVIATION_SCORE:
        return "HIGH"
    if score >= MEDIUM_RISK_DEVIATION_SCORE:
        return "MEDIUM"
    return "LOW"


def build_feature_table(atm_df: pd.DataFrame, transaction_df: pd.DataFrame, auth_df: pd.DataFrame,
                        baselines: Dict[str, CustomerBaseline], window_hours: int = 24) -> pd.DataFrame:
    """Builds one feature row per customer seen in the input frames, using
    only the most recent `window_hours` of activity for each customer."""
    activity = pd.concat([
        atm_df.assign(source="atm") if not atm_df.empty else atm_df,
        transaction_df.assign(source="transaction") if not transaction_df.empty else transaction_df,
    ], ignore_index=True) if not (atm_df.empty and transaction_df.empty) else pd.DataFrame(
        columns=["customer_id", "amount", "timestamp", "location", "device_id"])

    if not activity.empty:
        activity["timestamp"] = pd.to_datetime(activity["timestamp"], utc=True)
    if not auth_df.empty:
        auth_df = auth_df.copy()
        auth_df["timestamp"] = pd.to_datetime(auth_df["timestamp"], utc=True)

    now = pd.Timestamp.now(tz="UTC")
    window_start = now - pd.Timedelta(hours=window_hours)

    customer_ids = set(activity["customer_id"].unique()) if not activity.empty else set()
    if not auth_df.empty:
        customer_ids |= set(auth_df["customer_id"].unique())

    rows = []
    for customer_id in sorted(customer_ids):
        cust_activity = activity[(activity["customer_id"] == customer_id) &
                                 (activity["timestamp"] >= window_start)] if not activity.empty else activity
        cust_auth = auth_df[(auth_df["customer_id"] == customer_id) &
                            (auth_df["timestamp"] >= window_start)] if not auth_df.empty else auth_df
        rows.append(build_feature_row(customer_id, cust_activity, cust_auth,
                                      baselines.get(customer_id), window_hours))

    return pd.DataFrame(rows)
