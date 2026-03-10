from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.models import KpiDefinition


class KpiDefinitionRepository(ABC):
    @abstractmethod
    def get_by_key(self, kpi_slug: str, kpi_version: int) -> Optional[KpiDefinition]:
        raise NotImplementedError

    @abstractmethod
    def get_by_identity(self, kpi_id: str, kpi_slug: str, kpi_version: int) -> Optional[KpiDefinition]:
        raise NotImplementedError

    @abstractmethod
    def get_by_name(self, kpi_name: str) -> Optional[KpiDefinition]:
        raise NotImplementedError

    @abstractmethod
    def list_recent(self, limit: int = 100) -> List[KpiDefinition]:
        raise NotImplementedError

    @abstractmethod
    def list_recent_summary(self, limit: int = 100) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def insert(self, definition: KpiDefinition) -> None:
        raise NotImplementedError

    @abstractmethod
    def update_by_key(
        self, current_kpi_slug: str, current_kpi_version: int, definition: KpiDefinition
    ) -> None:
        raise NotImplementedError
