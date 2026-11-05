from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class QueryParameter:
    """Explicit scalar type for ambiguous values, such as a typed NULL."""

    type_: str
    value: object


class StorageProvider(ABC):
    @abstractmethod
    async def upload(self, path: str, data: bytes, content_type: str | None = None) -> str:
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
    async def query(self, sql: str, params: dict | list | tuple | None = None) -> list[dict]:
        pass

    @abstractmethod
    async def execute_affected(self, sql: str, params: dict | list | tuple) -> int:
        """Execute one conditional DML statement and return committed affected rows."""



class PipelineProvider(ABC):
    @abstractmethod
    def get_runner_name(self) -> str:
        """Ex: 'DirectRunner', 'DataflowRunner'."""

    @abstractmethod
    def get_runner_options(self) -> dict:
        """Opções específicas do runner para pipelines Beam."""
