"""
GCP Adapters — implementados quando provider=gcp no config.yaml.
Requer: google-cloud-storage, google-cloud-bigquery instalados.
"""
from app.adapters.cloud.base import PipelineProvider, StorageProvider, WarehouseProvider
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

    async def query(self, sql: str, params: dict | None = None) -> list[dict]:
        result = self.client.query(sql).result()
        return [dict(row) for row in result]

    async def execute_affected(self, sql: str, params: dict) -> int:
        import asyncio
        import re

        from google.cloud import bigquery

        def execute() -> int:
            config = bigquery.QueryJobConfig(
                default_dataset=f"{self.project}.{self.dataset}",
                query_parameters=[bigquery.ScalarQueryParameter(key, "STRING", value)
                                  for key, value in params.items()],
            )
            job = self.client.query(re.sub(r":(\w+)", r"@\1", sql), job_config=config)
            job.result()
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
