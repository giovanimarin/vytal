"""
GCP Adapters — implementados quando provider=gcp no config.yaml.
Requer: google-cloud-storage, google-cloud-bigquery instalados.
"""
import asyncio
import re
from datetime import UTC, date, datetime, time
from decimal import Decimal

from app.adapters.cloud.base import (
    PipelineProvider,
    QueryParameter,
    StorageProvider,
    WarehouseProvider,
)
from app.config.cloud_config import GCPConfig


class GCSStorageProvider(StorageProvider):
    def __init__(self, config: GCPConfig):
        from google.cloud import storage
        self.client = storage.Client(project=config.project)
        self.bucket = self.client.bucket(config.storage_bucket)

    async def upload(self, path: str, data: bytes, content_type: str | None = None) -> str:
        blob = self.bucket.blob(path)
        blob.upload_from_string(data, content_type=content_type or "application/octet-stream")
        return f"gs://{self.bucket.name}/{path}"

    async def download(self, path: str) -> bytes:
        return self.bucket.blob(path).download_as_bytes()

    async def list(self, prefix: str) -> list[str]:
        return [b.name for b in self.client.list_blobs(self.bucket, prefix=prefix)]


class BigQueryWarehouseProvider(WarehouseProvider):
    def __init__(self, config: GCPConfig):
        from google.cloud import bigquery
        self.client = bigquery.Client(project=config.project)
        self.dataset = config.bigquery_dataset
        self.project = config.project

    async def init_schema(self) -> None:
        # BigQuery — datasets e tabelas criadas via Terraform
        pass

    async def insert(self, table: str, rows: list[dict]) -> int:
        if not rows:
            return 0
        table_ref = f"{self.project}.{self.dataset}.{table}"
        errors = self.client.insert_rows_json(table_ref, rows)
        if errors:
            raise RuntimeError(f"BigQuery insert errors: {errors}")
        return len(rows)

    # Match literals/comments before placeholders; quoted text and @@ variables
    # must not be rewritten or mistaken for bound values.
    _tokens = re.compile(
        r"('''[\s\S]*?'''|\"\"\"[\s\S]*?\"\"\""
        r"|'(?:\\.|''|[^'\\])*'|\"(?:\\.|\"\"|[^\"\\])*\"|`(?:\\.|``|[^`\\])*`"
        r"|--[^\r\n]*|\#[^\r\n]*|/\*[\s\S]*?\*/)"
        r"|(?<![:@\w])[:@](?P<name>[A-Za-z_][A-Za-z0-9_]*)|(?P<positional>\?)"
    )

    @classmethod
    def _sql_parameters(cls, sql: str, params: dict | list | tuple | None):
        names = set()
        positional = 0

        def replace(match):
            nonlocal positional
            if match.group("name") is not None:
                name = match.group("name")
                names.add(name)
                return f"@{name}"
            if match.group("positional") is not None:
                positional += 1
            return match.group(0)

        statement = cls._tokens.sub(replace, sql)
        if names and positional:
            raise ValueError("Cannot mix named and positional query parameters")
        if params is None:
            params = {}
        if isinstance(params, dict):
            if positional or set(params) != names:
                raise ValueError("Named query parameters do not match SQL placeholders")
            bound = [cls._scalar_parameter(name, value) for name, value in params.items()]
        elif isinstance(params, (list, tuple)):
            if names or len(params) != positional:
                raise ValueError("Positional query parameters do not match SQL placeholders")
            bound = [cls._scalar_parameter(None, value) for value in params]
        else:
            raise TypeError("Query parameters must be a mapping or a sequence")
        return statement, bound

    @staticmethod
    def _scalar_parameter(name, value):
        from google.cloud import bigquery

        if isinstance(value, QueryParameter):
            kind, value = value.type_.upper(), value.value
            if kind not in {"STRING", "BOOL", "INT64", "FLOAT64", "NUMERIC", "BIGNUMERIC",
                            "TIMESTAMP", "DATETIME", "DATE", "TIME", "BYTES"}:
                raise ValueError("Unsupported scalar query parameter type")
        elif isinstance(value, bool):
            kind = "BOOL"
        elif isinstance(value, int):
            kind = "INT64"
        elif isinstance(value, float):
            kind = "FLOAT64"
        elif isinstance(value, Decimal):
            kind = "NUMERIC"
        elif isinstance(value, datetime):
            kind = "TIMESTAMP" if value.utcoffset() is not None else "DATETIME"
        elif isinstance(value, date):
            kind = "DATE"
        elif isinstance(value, time):
            kind = "TIME"
        elif isinstance(value, bytes):
            kind = "BYTES"
        elif isinstance(value, str):
            kind = "STRING"
        else:
            raise TypeError("Unsupported or ambiguous scalar value; use QueryParameter for typed NULL")
        if value is not None and kind == "TIMESTAMP":
            if not isinstance(value, datetime) or value.utcoffset() is None:
                raise ValueError("TIMESTAMP query parameters require timezone-aware datetime values")
            value = value.astimezone(UTC)
        if value is not None and kind == "DATETIME" and (
            not isinstance(value, datetime) or value.utcoffset() is not None
        ):
            raise ValueError("DATETIME query parameters require naive datetime values")
        if isinstance(value, time) and value.utcoffset() is not None:
            raise ValueError("TIME query parameters cannot contain a timezone")
        return bigquery.ScalarQueryParameter(name, kind, value)

    def _query_job(self, sql: str, params: dict | list | tuple | None):
        from google.cloud import bigquery

        statement, bound = self._sql_parameters(sql, params)
        config = bigquery.QueryJobConfig(
            use_legacy_sql=False,
            default_dataset=f"{self.project}.{self.dataset}", query_parameters=bound,
        )
        return self.client.query(statement, job_config=config)

    async def query(self, sql: str, params: dict | list | tuple | None = None) -> list[dict]:
        def execute():
            job = self._query_job(sql, params)
            return [dict(row) for row in job.result()]

        return await asyncio.to_thread(execute)

    async def execute_affected(self, sql: str, params: dict | list | tuple) -> int:
        def execute():
            job = self._query_job(sql, params)
            job.result()
            # Unknown row counts never indicate successful compare-and-swap.
            return job.num_dml_affected_rows or 0

        return await asyncio.to_thread(execute)


class DataflowPipelineProvider(PipelineProvider):
    def __init__(self, config: GCPConfig):
        self.config = config

    def get_runner_name(self) -> str:
        return "DataflowRunner"

    def get_runner_options(self) -> dict:
        return {
            "project": self.config.project,
            "region": self.config.region,
            "temp_location": self.config.dataflow_temp,
            "staging_location": f"{self.config.dataflow_temp}/staging",
        }
