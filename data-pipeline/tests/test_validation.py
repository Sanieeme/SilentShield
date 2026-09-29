import pandas as pd
import pytest

from processing.validation import validate_events


def _valid_atm_row(**overrides):
    row = {
        "event_id": "e1", "customer_id": "CUST-1", "account_id": "ACC-1",
        "atm_id": "ATM-1", "amount": 500.0, "location": "Sandton",
        "timestamp": pd.Timestamp.now(tz="UTC") - pd.Timedelta(minutes=5),
    }
    row.update(overrides)
    return row


def test_all_valid_rows_pass_through():
    df = pd.DataFrame([_valid_atm_row(event_id="e1"), _valid_atm_row(event_id="e2")])
    result = validate_events(df, "atm")
    assert len(result.valid) == 2
    assert result.rejected.empty


def test_rejects_non_positive_amount():
    df = pd.DataFrame([_valid_atm_row(event_id="e1", amount=0), _valid_atm_row(event_id="e2", amount=-5)])
    result = validate_events(df, "atm")
    assert result.valid.empty
    assert len(result.rejected) == 2


def test_rejects_future_timestamp():
    future = pd.Timestamp.now(tz="UTC") + pd.Timedelta(hours=2)
    df = pd.DataFrame([_valid_atm_row(event_id="e1", timestamp=future)])
    result = validate_events(df, "atm")
    assert result.valid.empty
    assert result.rejected.iloc[0]["_reject_reason"] == "invalid_timestamp"


def test_deduplicates_by_event_id_keeping_first():
    df = pd.DataFrame([_valid_atm_row(event_id="dup"), _valid_atm_row(event_id="dup")])
    result = validate_events(df, "atm")
    assert len(result.valid) == 1
    assert len(result.rejected) == 1


def test_missing_required_column_rejects_whole_batch():
    df = pd.DataFrame([_valid_atm_row(event_id="e1")]).drop(columns=["atm_id"])
    result = validate_events(df, "atm")
    assert result.valid.empty
    assert len(result.rejected) == 1
    assert "missing required columns" in result.reasons[0]


def test_missing_customer_id_rejected():
    df = pd.DataFrame([_valid_atm_row(event_id="e1", customer_id=None)])
    result = validate_events(df, "atm")
    assert result.valid.empty
    assert result.rejected.iloc[0]["_reject_reason"] == "missing_customer_id"


def test_rejection_rate_property():
    df = pd.DataFrame([_valid_atm_row(event_id="e1"), _valid_atm_row(event_id="e2", amount=-1)])
    result = validate_events(df, "atm")
    assert result.rejection_rate == pytest.approx(0.5)
