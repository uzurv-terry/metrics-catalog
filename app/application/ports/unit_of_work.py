from abc import ABC, abstractmethod

from app.application.ports.kpi_definition_repository import KpiDefinitionRepository
from app.application.ports.kpi_approver_repository import KpiApproverRepository
from app.application.ports.kpi_usage_repository import KpiUsageRepository
from app.application.ports.lineage_repository import LineageRepository
from app.application.ports.report_repository import ReportRepository
from app.application.ports.catalog_note_repository import CatalogNoteRepository


class UnitOfWork(ABC):
    definitions: KpiDefinitionRepository
    usage: KpiUsageRepository
    approvers: KpiApproverRepository
    lineage: LineageRepository
    reports: ReportRepository
    notes: CatalogNoteRepository

    @abstractmethod
    def __enter__(self):
        raise NotImplementedError

    @abstractmethod
    def __exit__(self, exc_type, exc, tb):
        raise NotImplementedError

    @abstractmethod
    def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def rollback(self) -> None:
        raise NotImplementedError
