import pandas as pd

from transformations.baseline import compute_baselines


def _activity_rows(customer_id, amounts, hour, location="Sandton", device_id="DEV-1", n_days=6):
    rows = []
    base = pd.Timestamp.now(tz="UTC").normalize()
    for i, amount in enumerate(amounts):
        rows.append({
            "customer_id": customer_id,
            "amount": amount,
            "timestamp": (base - pd.Timedelta(days=i % n_days)).replace(hour=hour),
            "location": location,
            "device_id": device_id,
        })
    return rows


def test_computes_baseline_for_customer_with_enough_history():
    rows = _activity_rows("CUST-1", [500, 520, 480, 510, 495, 505], hour=10)
    df = pd.DataFrame(rows)
    baselines = compute_baselines(df)
    b = baselines["CUST-1"]
    assert b.is_reliable
    assert 480 <= b.avg_amount <= 520
    assert b.typical_hour_mean == 10
    assert "Sandton" in b.known_locations
    assert "DEV-1" in b.known_devices


def test_baseline_not_reliable_with_too_few_events():
    rows = _activity_rows("CUST-2", [500, 510], hour=10)
    df = pd.DataFrame(rows)
    baselines = compute_baselines(df)
    assert baselines["CUST-2"].is_reliable is False


def test_empty_dataframe_returns_no_baselines():
    assert compute_baselines(pd.DataFrame(columns=["customer_id", "amount", "timestamp", "location", "device_id"])) == {}
