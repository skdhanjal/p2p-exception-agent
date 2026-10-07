"""Thin, parameterized access to the mock ERP in BigQuery."""

import os
from functools import lru_cache

from google.cloud import bigquery

DATASET = os.environ.get("ERP_DATASET", "p2p_erp")
BQ_LOCATION = os.environ.get("BQ_LOCATION", "asia-south1")


@lru_cache(maxsize=1)
def _client() -> bigquery.Client:
    return bigquery.Client(location=BQ_LOCATION)


def run_query(sql: str, params: dict[str, str]) -> list[dict]:
    """Run a parameterized query and return rows as plain dicts.

    Use __DATASET__ in the SQL where the dataset path belongs.
    """
    client = _client()
    query_params = [
        bigquery.ScalarQueryParameter(name, "STRING", value)
        for name, value in params.items()
    ]
    sql = sql.replace("__DATASET__", f"{client.project}.{DATASET}")
    job = client.query(
        sql,
        job_config=bigquery.QueryJobConfig(query_parameters=query_params),
    )
    return [dict(row) for row in job.result()]
