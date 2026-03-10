from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.models import KpiUsage


class KpiUsageRepository(ABC):
    @abstractmethod
    def list_recent(self, limit: int = 100) -> List[KpiUsage]:
        raise NotImplementedError

    @abstractmethod
    def list_recent_summary(self, limit: int = 100) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def get_by_usage_id(self, usage_id: int) -> Optional[KpiUsage]:
        raise NotImplementedError

    @abstractmethod
    def list_by_metric(self, kpi_slug: str, kpi_version: int) -> list[KpiUsage]:
        raise NotImplementedError

    @abstractmethod
    def insert(self, usage: KpiUsage) -> None:
        raise NotImplementedError

    @abstractmethod
    def insert_many(self, usages: list[KpiUsage]) -> None:
        raise NotImplementedError

    @abstractmethod
    def update(self, usage: KpiUsage) -> None:
        raise NotImplementedError
