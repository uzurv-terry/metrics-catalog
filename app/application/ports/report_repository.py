from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.models import Report


class ReportRepository(ABC):
    @abstractmethod
    def list_recent(self, limit: int = 100) -> List[Report]:
        raise NotImplementedError

    @abstractmethod
    def list_recent_summary(self, limit: int = 100) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def get_by_report_id(self, report_id: int) -> Optional[Report]:
        raise NotImplementedError

    @abstractmethod
    def get_by_tool_and_slug(self, consumer_tool: str, report_slug: str) -> Optional[Report]:
        raise NotImplementedError

    @abstractmethod
    def search(self, query: str, limit: int = 20) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def insert(self, report: Report) -> None:
        raise NotImplementedError

    @abstractmethod
    def update(self, report: Report) -> None:
        raise NotImplementedError
