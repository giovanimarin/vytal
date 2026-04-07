from app.adapters.connectors.base import HealthDataProvider

# Registry — adicionar novo provider = registrar aqui
PROVIDER_REGISTRY: dict[str, type[HealthDataProvider]] = {
    "google_fit": lambda: __import__(
        "app.adapters.connectors.google_fit", fromlist=["GoogleFitAdapter"]
    ).GoogleFitAdapter(),
}


def get_connector(provider: str) -> HealthDataProvider:
    if provider not in PROVIDER_REGISTRY:
        raise ValueError(f"Unknown health data provider: '{provider}'. Available: {list(PROVIDER_REGISTRY)}")
    return PROVIDER_REGISTRY[provider]()
