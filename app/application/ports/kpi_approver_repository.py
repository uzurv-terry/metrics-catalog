from abc import ABC, abstractmethod
from typing import List

from app.domain.models import KpiApprover


class KpiApproverRepository(ABC):
    @abstractmethod
    def list_recent(self, limit: int = 100) -> List[KpiApprover]:
        raise NotImplementedError

    @abstractmethod
    def list_recent_summary(self, limit: int = 100) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def insert(self, approver: KpiApprover) -> None:
        raise NotImplementedError

    @abstractmethod
    def exists_for_kpi(self, kpi_id: str, kpi_slug: str, kpi_version: int, approver_name: str) -> bool:
        raise NotImplementedError
