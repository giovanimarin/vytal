from app.adapters.cloud.base import StorageProvider, WarehouseProvider, PipelineProvider
from app.config.cloud_config import get_cloud_config

_storage: StorageProvider | None = None
_warehouse: WarehouseProvider | None = None
_pipeline: PipelineProvider | None = None


def _build_providers():
    global _storage, _warehouse, _pipeline
    cfg = get_cloud_config()

    if cfg.provider == "local":
        from app.adapters.cloud.local import (
            LocalStorageProvider,
            LocalWarehouseProvider,
            LocalPipelineProvider,
        )
        _storage = LocalStorageProvider(cfg.local)
        _warehouse = LocalWarehouseProvider(cfg.local)
        _pipeline = LocalPipelineProvider()

    elif cfg.provider == "gcp":
        from app.adapters.cloud.gcp import (
            GCSStorageProvider,
            BigQueryWarehouseProvider,
            DataflowPipelineProvider,
        )
        _storage = GCSStorageProvider(cfg.gcp)
        _warehouse = BigQueryWarehouseProvider(cfg.gcp)
        _pipeline = DataflowPipelineProvider(cfg.gcp)

    else:
        raise ValueError(f"Unknown cloud provider: {cfg.provider}")


def get_storage() -> StorageProvider:
    if _storage is None:
        _build_providers()
    return _storage


def get_warehouse() -> WarehouseProvider:
    if _warehouse is None:
        _build_providers()
    return _warehouse


def get_pipeline() -> PipelineProvider:
    if _pipeline is None:
        _build_providers()
    return _pipeline


async def init_warehouse() -> None:
    """Chamado no startup da app para criar tabelas se necessário."""
    await get_warehouse().init_schema()
