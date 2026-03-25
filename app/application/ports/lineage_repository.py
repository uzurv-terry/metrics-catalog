from abc import ABC, abstractmethod


class LineageRepository(ABC):
    @abstractmethod
    def get_kpi_lineage_rows(self, kpi_slug: str, kpi_version: int, max_edges: int) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def get_report_lineage_rows(self, report_id: int, max_edges: int) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def search_kpis(self, query: str, limit: int) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def search_reports(self, query: str, limit: int) -> list[dict]:
        raise NotImplementedError
