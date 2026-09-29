import pandas as pd

from transformations.baseline import compute_baselines
from transformations.features import build_feature_row, build_feature_table


def _baseline_history(customer_id, hour=10, amount=500, n=8):
    base = pd.Timestamp.now(tz="UTC").normalize()
    rows = [{
        "customer_id": customer_id,
        "amount": amount,
        "timestamp": (base - pd.Timedelta(days=i)).replace(hour=hour),
        "location": "Sandton",
        "device_id": "DEV-1",
    } for i in range(n)]
    return pd.DataFrame(rows)


def test_normal_activity_scores_low_risk():
    history = _baseline_history("CUST-1")
    baselines = compute_baselines(history)

    now = pd.Timestamp.now(tz="UTC")
    activity = pd.DataFrame([{
        "customer_id": "CUST-1", "amount": 510.0, "timestamp": now - pd.Timedelta(hours=1),
        "location": "Sandton", "device_id": "DEV-1",
    }])
    auth = pd.DataFrame([{"customer_id": "CUST-1", "success": True,
                          "timestamp": now - pd.Timedelta(hours=1, minutes=1),
                          "location": "Sandton", "device_id": "DEV-1"}])

    row = build_feature_row("CUST-1", activity, auth, baselines["CUST-1"])
    assert row["risk_level"] == "LOW"
    assert row["new_device"] is False
    assert row["new_location"] is False


def test_anomalous_activity_scores_higher_than_normal():
    history = _baseline_history("CUST-1")
    baselines = compute_baselines(history)
    now = pd.Timestamp.now(tz="UTC")

    normal_activity = pd.DataFrame([{
        "customer_id": "CUST-1", "amount": 510.0, "timestamp": now - pd.Timedelta(hours=1),
        "location": "Sandton", "device_id": "DEV-1",
    }])
    anomalous_activity = pd.DataFrame([{
        "customer_id": "CUST-1", "amount": 6000.0, "timestamp": now.replace(hour=3),
        "location": "Soweto", "device_id": "DEV-UNKNOWN",
    }])
    auth = pd.DataFrame([{"customer_id": "CUST-1", "success": False,
                          "timestamp": now - pd.Timedelta(minutes=1),
                          "location": "Soweto", "device_id": "DEV-UNKNOWN"}])

    normal_row = build_feature_row("CUST-1", normal_activity, pd.DataFrame(), baselines["CUST-1"])
    anomalous_row = build_feature_row("CUST-1", anomalous_activity, auth, baselines["CUST-1"])

    assert anomalous_row["behaviour_deviation_score"] > normal_row["behaviour_deviation_score"]
    assert anomalous_row["new_device"] is True
    assert anomalous_row["new_location"] is True
    assert anomalous_row["failed_authentication_attempts"] == 1


def test_insufficient_history_yields_unknown_risk_not_low():
    now = pd.Timestamp.now(tz="UTC")
    activity = pd.DataFrame([{
        "customer_id": "CUST-NEW", "amount": 9000.0, "timestamp": now,
        "location": "Soweto", "device_id": "DEV-X",
    }])
    row = build_feature_row("CUST-NEW", activity, pd.DataFrame(), None)
    assert row["insufficient_history"] is True
    assert row["risk_level"] == "UNKNOWN"


def test_failed_auth_count_correct_when_success_column_is_object_dtype():
    # Regression test: `success` can arrive as object dtype (e.g. after
    # being isolated from a mixed-schema raw file where other streams left
    # it all-NaN). `~` on object-dtype Python bools does a bitwise
    # complement, not a logical NOT, and silently produces negative counts.
    now = pd.Timestamp.now(tz="UTC")
    auth = pd.DataFrame({
        "customer_id": ["CUST-1"] * 4,
        "success": pd.array([True, False, False, True], dtype=object),
        "timestamp": [now - pd.Timedelta(minutes=i) for i in range(4)],
        "location": ["Sandton"] * 4,
        "device_id": ["DEV-1"] * 4,
    })
    row = build_feature_row("CUST-1", pd.DataFrame(), auth, None)
    assert row["failed_authentication_attempts"] == 2


def test_build_feature_table_one_row_per_customer():
    history = pd.concat([_baseline_history("CUST-1"), _baseline_history("CUST-2")], ignore_index=True)
    baselines = compute_baselines(history)
    now = pd.Timestamp.now(tz="UTC")
    atm_df = pd.DataFrame([
        {"customer_id": "CUST-1", "amount": 505.0, "timestamp": now - pd.Timedelta(hours=2),
         "location": "Sandton", "device_id": "DEV-1"},
        {"customer_id": "CUST-2", "amount": 495.0, "timestamp": now - pd.Timedelta(hours=3),
         "location": "Sandton", "device_id": "DEV-1"},
    ])
    table = build_feature_table(atm_df, pd.DataFrame(), pd.DataFrame(), baselines)
    assert set(table["customer_id"]) == {"CUST-1", "CUST-2"}
    assert len(table) == 2
