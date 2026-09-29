"""Airflow DAG skeleton wiring the pipeline stages together (README Phase 3:
'Add Airflow orchestration'). This DAG is deliberately thin - each task
calls straight into the tested functions in ingestion/ and processing/
rather than reimplementing logic in the DAG file, so the DAG is just
scheduling glue.

Not runnable in this sandbox (no Airflow installed / no scheduler here);
drop this file into an Airflow `dags/` folder to use it. Update
DATA_LAKE_DIR / KAFKA_BOOTSTRAP_SERVERS via Airflow Variables or plain
environment variables as usual.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "silentshield",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def _task_generate_events(**context):
    from ingestion.simulator import events_to_dataframe, generate_events
    events = generate_events(n_customers=50, days=1)
    df = events_to_dataframe(events)
    path = f"/tmp/silentshield_events_{context['ds']}.parquet"
    df.to_parquet(path, index=False)
    context["ti"].xcom_push(key="events_path", value=path)


def _task_run_pipeline(**context):
    from processing.batch_runner import run
    events_path = context["ti"].xcom_pull(key="events_path", task_ids="generate_events")
    features_path = f"/tmp/silentshield_features_{context['ds']}.parquet"
    run(events_path, features_path)
    context["ti"].xcom_push(key="features_path", value=features_path)


def _task_alert_on_high_risk(**context):
    """Placeholder hook for Phase 4: read the feature table just written and
    raise alerts for any HIGH risk_level rows. Kept separate from the
    feature-engineering task so alerting logic can evolve independently."""
    import pandas as pd
    features_path = context["ti"].xcom_pull(key="features_path", task_ids="run_pipeline")
    features = pd.read_parquet(features_path)
    high_risk = features[features["risk_level"] == "HIGH"]
    if not high_risk.empty:
        # TODO(Phase 4): wire this into the security-engine's alerting channel
        # instead of just logging.
        print(f"{len(high_risk)} HIGH risk customers: {high_risk['customer_id'].tolist()}")


with DAG(
    dag_id="silentshield_data_pipeline",
    description="Simulate events -> validate -> enrich -> feature-engineer -> sink -> alert",
    default_args=default_args,
    schedule="@hourly",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["silentshield", "data-pipeline"],
) as dag:

    generate_events = PythonOperator(
        task_id="generate_events",
        python_callable=_task_generate_events,
    )

    run_pipeline = PythonOperator(
        task_id="run_pipeline",
        python_callable=_task_run_pipeline,
    )

    alert_on_high_risk = PythonOperator(
        task_id="alert_on_high_risk",
        python_callable=_task_alert_on_high_risk,
    )

    generate_events >> run_pipeline >> alert_on_high_risk
