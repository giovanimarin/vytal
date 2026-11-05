import os

os.environ.setdefault("ENVIRONMENT", "test")


# Garante que pytest-asyncio trate todos os testes async automaticamente
pytest_plugins = ["pytest_asyncio"]
