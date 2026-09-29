"""Data-quality checks applied to raw events before they enter the pipeline.

Kept as pure functions over dicts/DataFrames (no Kafka, no DB) so they're
trivially unit-testable and reusable from both the streaming consumer and
the batch runner.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable, List

import pandas as pd

REQUIRED_COLUMNS_BY_STREAM = {
    "atm": {"event_id", "customer_id", "account_id", "atm_id", "amount", "location", "timestamp"},
    "transaction": {"event_id", "customer_id", "account_id", "transaction_type", "amount",
                    "channel", "location", "timestamp"},
    "auth": {"event_id", "customer_id", "success", "device_id", "location", "timestamp"},
}


@dataclass
class ValidationResult:
    valid: pd.DataFrame
    rejected: pd.DataFrame
    reasons: List[str] = field(default_factory=list)

    @property
    def rejection_rate(self) -> float:
        total = len(self.valid) + len(self.rejected)
        return 0.0 if total == 0 else len(self.rejected) / total


def _missing_required_columns(df: pd.DataFrame, stream: str) -> set:
    required = REQUIRED_COLUMNS_BY_STREAM.get(stream, set())
    return required - set(df.columns)


def validate_events(df: pd.DataFrame, stream: str) -> ValidationResult:
    """Runs schema, range and freshness checks; deduplicates by event_id.

    Rules (mirrors the README's "Data Quality Testing" section):
      - missing required fields          -> rejected
      - non-positive amount (where present) -> rejected
      - future timestamp                 -> rejected
      - duplicate event_id                -> rejected (keep first occurrence)
    """
    reasons: List[str] = []
    missing_cols = _missing_required_columns(df, stream)
    if missing_cols:
        reasons.append(f"missing required columns: {sorted(missing_cols)}")
        # Treat the whole batch as rejected if the schema itself is broken -
        # there's nothing safe to salvage row by row.
        return ValidationResult(valid=df.iloc[0:0], rejected=df, reasons=reasons)

    working = df.copy()
    working["_reject_reason"] = None

    if "amount" in working.columns:
        bad_amount = working["amount"].isna() | (working["amount"] <= 0)
        working.loc[bad_amount, "_reject_reason"] = "invalid_amount"

    now = pd.Timestamp.now(tz=timezone.utc)
    ts = pd.to_datetime(working["timestamp"], utc=True, errors="coerce")
    working["timestamp"] = ts
    bad_ts = ts.isna() | (ts > now)
    working.loc[bad_ts & working["_reject_reason"].isna(), "_reject_reason"] = "invalid_timestamp"

    missing_customer = working["customer_id"].isna() | (working["customer_id"].astype(str).str.strip() == "")
    working.loc[missing_customer & working["_reject_reason"].isna(), "_reject_reason"] = "missing_customer_id"

    dup_mask = working["event_id"].duplicated(keep="first")
    working.loc[dup_mask & working["_reject_reason"].isna(), "_reject_reason"] = "duplicate_event_id"

    rejected = working[working["_reject_reason"].notna()].copy()
    valid = working[working["_reject_reason"].isna()].drop(columns=["_reject_reason"])

    if not rejected.empty:
        reasons.append(f"{len(rejected)} rows rejected: " +
                       rejected["_reject_reason"].value_counts().to_dict().__str__())

    return ValidationResult(valid=valid, rejected=rejected, reasons=reasons)


def validate_streams(frames_by_stream: dict) -> dict:
    """Convenience wrapper: validates {stream_name: DataFrame} for each of
    'atm', 'transaction', 'auth' and returns {stream_name: ValidationResult}."""
    return {stream: validate_events(df, stream) for stream, df in frames_by_stream.items()}
