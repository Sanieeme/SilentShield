import pandas as pd

from ingestion.simulator import events_to_dataframe, generate_events


def test_generate_events_produces_events_for_all_streams():
    events = generate_events(n_customers=5, days=3, seed=1)
    assert len(events) > 0
    streams = {e["stream"] for e in events}
    assert streams == {"atm", "transaction", "auth"}


def test_generate_events_is_deterministic_given_seed():
    # event_id is a random UUID by design, and a handful of timestamps are
    # clamped against wall-clock "now" (so they can shift by microseconds
    # between two calls a moment apart). What the seed actually pins down is
    # the shape of the run: how many events per stream, for which customers,
    # at what amounts.
    def fingerprint(events):
        by_stream = {}
        for e in events:
            by_stream.setdefault(e["stream"], []).append((e["customer_id"], e.get("amount")))
        return {stream: sorted(rows) for stream, rows in by_stream.items()}

    a = generate_events(n_customers=5, days=3, seed=7)
    b = generate_events(n_customers=5, days=3, seed=7)
    assert fingerprint(a) == fingerprint(b)
    assert len(a) == len(b)


def test_no_event_has_a_future_timestamp():
    events = generate_events(n_customers=10, days=5, seed=3)
    now = pd.Timestamp.now(tz="UTC")
    for e in events:
        assert pd.Timestamp(e["timestamp"]) <= now


def test_events_to_dataframe_has_expected_columns():
    events = generate_events(n_customers=3, days=2, seed=2)
    df = events_to_dataframe(events)
    assert "customer_id" in df.columns
    assert "stream" in df.columns
    assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])
