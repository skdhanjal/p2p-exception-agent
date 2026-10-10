"""Parameterized BigQuery access shared by the MCP servers."""

import os
from functools import lru_cache
from typing import Any

from google.cloud import bigquery

DATASET = os.environ.get("ERP_DATASET", "p2p_erp")
BQ_LOCATION = os.environ.get("BQ_LOCATION", "asia-south1")


@lru_cache(maxsize=1)
def _client() -> bigquery.Client:
    return bigquery.Client(location=BQ_LOCATION)


def _param(name: str, value: Any) -> bigquery.ScalarQueryParameter:
    if isinstance(value, bool):
        kind = "BOOL"
    elif isinstance(value, int):
        kind = "INT64"
    elif isinstance(value, float):
        kind = "FLOAT64"
    else:
        kind = "STRING"
    return bigquery.ScalarQueryParameter(name, kind, value)


def run_query(sql: str, params: dict[str, Any]) -> list[dict]:
    """Run a parameterized query or DML statement.

    Use __DATASET__ in the SQL where the dataset path belongs.
    Returns rows as plain dicts (empty for DML).
    """
    client = _client()
    sql = sql.replace("__DATASET__", f"{client.project}.{DATASET}")
    config = bigquery.QueryJobConfig(
        query_parameters=[_param(k, v) for k, v in params.items()]
    )
    job = client.query(sql, job_config=config)
    return [dict(row) for row in job.result()]
