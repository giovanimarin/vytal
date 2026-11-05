from dataclasses import dataclass, field
from pathlib import Path

import yaml

from app.config.security import ConfigurationError, is_local


@dataclass
class LocalConfig:
    data_dir: str = "./data"
    db_path: str = "./data/vytal.db"


@dataclass
class GCPConfig:
    project: str = ""
    region: str = "us-central1"
    storage_bucket: str = ""
    bigquery_dataset: str = "vytal"
    pubsub_topic: str = "health-events"
    dataflow_temp: str = ""


@dataclass
class CloudConfig:
    provider: str = "local"
    local: LocalConfig = field(default_factory=LocalConfig)
    gcp: GCPConfig = field(default_factory=GCPConfig)


def load_cloud_config(path: str = "./config.yaml", *, strict: bool = False) -> CloudConfig:
    config_file = Path(path)
    if not config_file.exists():
        if strict:
            raise ConfigurationError("CONFIG_PATH must reference an existing configuration file")
        return CloudConfig()

    try:
        with open(config_file) as f:
            raw = yaml.safe_load(f)
    except (OSError, yaml.YAMLError):
        raise ConfigurationError("Invalid cloud configuration file") from None
    if not isinstance(raw, dict) or not isinstance(raw.get("cloud", {}), dict):
        raise ConfigurationError("Invalid cloud configuration structure")
    if strict and "provider" not in raw.get("cloud", {}):
        raise ConfigurationError("Cloud provider must be explicitly configured")

    cfg = CloudConfig()
    cfg.provider = raw.get("cloud", {}).get("provider", "local")
    if cfg.provider not in {"local", "gcp"}:
        raise ConfigurationError("Unsupported cloud provider")

    if "local" in raw:
        if not isinstance(raw["local"], dict) or set(raw["local"]) - {"data_dir", "db_path"}:
            raise ConfigurationError("Invalid local configuration structure")
        cfg.local = LocalConfig(**raw["local"])

    if "gcp" in raw:
        gcp_raw = raw["gcp"]
        if not isinstance(gcp_raw, dict):
            raise ConfigurationError("Invalid GCP configuration structure")
        cfg.gcp = GCPConfig(
            project=gcp_raw.get("project", ""),
            region=gcp_raw.get("region", "us-central1"),
            storage_bucket=gcp_raw.get("storage_bucket", ""),
            bigquery_dataset=gcp_raw.get("bigquery_dataset", "vytal"),
            pubsub_topic=gcp_raw.get("pubsub_topic", "health-events"),
            dataflow_temp=gcp_raw.get("dataflow_temp", ""),
        )

    return cfg


# Singleton
_cloud_config: CloudConfig | None = None


def get_cloud_config() -> CloudConfig:
    global _cloud_config
    if _cloud_config is None:
        from app.config.settings import settings
        _cloud_config = load_cloud_config(settings.config_path, strict=not is_local(settings.environment))
    return _cloud_config
