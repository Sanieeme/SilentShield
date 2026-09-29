"""Storage-layer adapters.

- Data lake  : raw, validated events written as partitioned Parquet -
              cheap, append-only, replayable history.
- Data warehouse : processed feature rows written to PostgreSQL for
              analytics/reporting and for the security dashboard to query.

Both are optional/best-effort: a missing Postgres connection should not stop
the pipeline from writing to the data lake, and vice versa - matches the
architecture diagram where the two storage layers are siblings, not a chain.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

import pandas as pd

from config import DATA_LAKE_DIR, WAREHOUSE_URL

logger = logging.getLogger(__name__)


def write_to_data_lake(df: pd.DataFrame, stream: str, lake_dir: str = DATA_LAKE_DIR) -> Optional[str]:
    """Writes one Parquet file per (stream, ingestion date) partition,
    mirroring a typical `stream=X/date=Y/part.parquet` lake layout."""
    if df.empty:
        return None
    date_str = pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d")
    partition_dir = os.path.join(lake_dir, f"stream={stream}", f"date={date_str}")
    os.makedirs(partition_dir, exist_ok=True)
    path = os.path.join(partition_dir, f"part-{pd.Timestamp.now(tz='UTC').strftime('%H%M%S%f')}.parquet")
    df.to_parquet(path, index=False)
    return path


def write_features_to_warehouse(df: pd.DataFrame, table: str = "behaviour_features",
                                warehouse_url: str = WAREHOUSE_URL) -> int:
    """Upserts feature rows into the warehouse. Requires the table to already
    exist (see infrastructure/docker or a Flyway-style migration for the
    warehouse schema) - the pipeline does not implicitly create tables.
    Returns the number of rows written, or 0 if the warehouse is unreachable
    (logged, not raised, so a batch run can still succeed at the data-lake
    stage even if the warehouse is down)."""
    if df.empty:
        return 0
    try:
        import sqlalchemy  # local import: keep it optional at module load time
        engine = sqlalchemy.create_engine(warehouse_url)
        with engine.begin() as conn:
            df.to_sql(table, conn, if_exists="append", index=False)
        return len(df)
    except Exception as exc:  # noqa: BLE001 - deliberately broad, this is a best-effort sink
        logger.warning("Could not write to warehouse (%s): %s", warehouse_url, exc)
        return 0
