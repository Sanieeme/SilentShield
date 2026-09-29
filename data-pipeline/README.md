# SilentShield Data Pipeline

Phase 3 of the roadmap: simulated banking events -> ingestion -> validation ->
enrichment -> behavioural feature engineering -> storage layers.

## Layout

```
data-pipeline/
├── ingestion/
│   ├── event_models.py     Pydantic schemas for ATM, auth and transaction events
│   ├── simulator.py        Generates synthetic customer behaviour + anomalies
│   └── kafka_producer.py   Publishes simulated events to Kafka topics
├── processing/
│   ├── validation.py       Data-quality checks (schema, ranges, duplicates)
│   ├── enrichment.py       Attaches customer behavioural baselines to events
│   ├── sink.py             Writes to data lake (Parquet) / data warehouse (Postgres)
│   └── kafka_consumer.py   Consumes raw events and runs them through the pipeline
├── transformations/
│   ├── baseline.py         Computes each customer's behavioural baseline
│   └── features.py         Builds the behavioural feature vector + risk features
├── orchestration/
│   └── airflow_dag.py      Airflow DAG skeleton wiring the stages together
└── tests/                  Unit tests for validation, baseline and feature logic
```

## Design principle

All the logic that matters (validation rules, baseline maths, feature
engineering) is plain Python/pandas with **no Kafka or Postgres dependency**,
so it can be unit tested and reasoned about in isolation. Kafka and Postgres
are thin adapters bolted on around that core in `kafka_producer.py`,
`kafka_consumer.py` and `sink.py`. This mirrors the architecture diagram in
the top-level README: ingestion and storage are swappable around a stable
processing core.

## Running locally

```bash
pip install -r requirements.txt --break-system-packages   # or use a venv

# 1. Generate a batch of simulated events straight to the data lake, no Kafka needed:
python -m ingestion.simulator --customers 25 --days 14 --out data_lake/events.parquet

# 2. Run the batch pipeline over that file (validate -> enrich -> features -> sink):
python -m processing.batch_runner --in data_lake/events.parquet --out data_lake/features.parquet
```

## Running with Kafka

```bash
# requires a Kafka broker, e.g. via infrastructure/docker
python -m ingestion.kafka_producer --bootstrap-servers localhost:9092 --customers 25
python -m processing.kafka_consumer --bootstrap-servers localhost:9092
```

## Tests

```bash
pytest tests/ -v
```
