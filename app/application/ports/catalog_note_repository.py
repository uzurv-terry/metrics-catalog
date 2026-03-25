from abc import ABC, abstractmethod
from typing import List

from app.domain.models import CatalogNote


class CatalogNoteRepository(ABC):
    @abstractmethod
    def list_recent(self, limit: int = 100) -> List[CatalogNote]:
        raise NotImplementedError

    @abstractmethod
    def list_recent_summary(self, limit: int = 100) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def list_by_metric(self, kpi_slug: str, kpi_version: int) -> list[CatalogNote]:
        raise NotImplementedError

    @abstractmethod
    def list_by_report_ids(self, report_ids: list[int]) -> list[CatalogNote]:
        raise NotImplementedError

    @abstractmethod
    def insert(self, note: CatalogNote) -> None:
        raise NotImplementedError
