"""Attaches customer behavioural baselines to validated events.

Kept deliberately thin: enrichment here means "look up and carry along the
baseline a customer is being compared against", not feature computation
itself (that's transformations/features.py). Separating the two lets the
feature step stay a pure function of (activity window, baseline).
"""
from __future__ import annotations

from typing import Dict

import pandas as pd

from transformations.baseline import CustomerBaseline


def enrich_with_baseline(df: pd.DataFrame, baselines: Dict[str, CustomerBaseline]) -> pd.DataFrame:
    if df.empty:
        return df.assign(has_baseline=pd.Series(dtype=bool))
    out = df.copy()
    out["has_baseline"] = out["customer_id"].map(lambda c: baselines.get(c) is not None
                                                 and baselines[c].is_reliable)
    return out
