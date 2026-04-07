from abc import ABC, abstractmethod


class StorageProvider(ABC):
    @abstractmethod
    async def upload(self, path: str, data: bytes, content_type: str = None) -> str:
        """Persiste o objeto e retorna sua URI."""

    @abstractmethod
    async def download(self, path: str) -> bytes:
        pass

    @abstractmethod
    async def list(self, prefix: str) -> list[str]:
        pass


class WarehouseProvider(ABC):
    @abstractmethod
    async def init_schema(self) -> None:
        """Cria tabelas/datasets se não existirem."""

    @abstractmethod
    async def insert(self, table: str, rows: list[dict]) -> int:
        """Insere rows e retorna quantidade inserida."""

    @abstractmethod
    async def query(self, sql: str, params: dict = None) -> list[dict]:
        pass


class PipelineProvider(ABC):
    @abstractmethod
    def get_runner_name(self) -> str:
        """Ex: 'DirectRunner', 'DataflowRunner'."""

    @abstractmethod
    def get_runner_options(self) -> dict:
        """Opções específicas do runner para pipelines Beam."""
