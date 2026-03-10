from app.application.ports.unit_of_work import UnitOfWork
from app.infrastructure.redshift.repositories.kpi_definition_repository import (
    RedshiftKpiDefinitionRepository,
)
from app.infrastructure.redshift.repositories.kpi_approver_repository import RedshiftKpiApproverRepository
from app.infrastructure.redshift.repositories.kpi_usage_repository import RedshiftKpiUsageRepository
from app.infrastructure.redshift.repositories.lineage_repository import RedshiftLineageRepository


class RedshiftUnitOfWork(UnitOfWork):
    def __init__(self, connection_factory):
        self._connection_factory = connection_factory
        self._executor = None
        self.definitions = None
        self.usage = None
        self.approvers = None
        self.lineage = None

    def __enter__(self):
        self._executor = self._connection_factory.create()
        self.definitions = RedshiftKpiDefinitionRepository(self._executor)
        self.usage = RedshiftKpiUsageRepository(self._executor)
        self.approvers = RedshiftKpiApproverRepository(self._executor)
        self.lineage = RedshiftLineageRepository(self._executor)
        return self

    def __exit__(self, exc_type, exc, tb):
        # Data API is connectionless from app perspective.
        return False

    def commit(self) -> None:
        # No-op for Data API statement execution model.
        return None

    def rollback(self) -> None:
        # No-op for Data API statement execution model.
        return None
