"""Central configuration for the data pipeline. Everything is overridable via
environment variables so the same code runs locally, in Docker, and in CI."""
import os

KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

TOPIC_ATM_EVENTS = os.environ.get("TOPIC_ATM_EVENTS", "silentshield.atm-events")
TOPIC_AUTH_EVENTS = os.environ.get("TOPIC_AUTH_EVENTS", "silentshield.auth-events")
TOPIC_TRANSACTION_EVENTS = os.environ.get("TOPIC_TRANSACTION_EVENTS", "silentshield.transaction-events")

DATA_LAKE_DIR = os.environ.get("DATA_LAKE_DIR", "data_lake")

WAREHOUSE_URL = os.environ.get(
    "WAREHOUSE_URL",
    "postgresql://silentshield:silentshield@localhost:5432/silentshield",
)

# Behavioural feature / risk thresholds. Kept here rather than scattered
# through the code so the security-engine tuning story is in one place.
NIGHT_START_HOUR = int(os.environ.get("NIGHT_START_HOUR", "22"))
NIGHT_END_HOUR = int(os.environ.get("NIGHT_END_HOUR", "6"))
BASELINE_MIN_EVENTS = int(os.environ.get("BASELINE_MIN_EVENTS", "5"))
HIGH_RISK_DEVIATION_SCORE = float(os.environ.get("HIGH_RISK_DEVIATION_SCORE", "0.7"))
MEDIUM_RISK_DEVIATION_SCORE = float(os.environ.get("MEDIUM_RISK_DEVIATION_SCORE", "0.4"))
