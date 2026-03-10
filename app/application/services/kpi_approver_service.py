from typing import Callable, List

from app.application.dto.kpi_approver_dto import KpiApproverDTO
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.exceptions import ConflictError, ValidationError
from app.domain.models import KpiApprover


class KpiApproverService:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]):
        self._uow_factory = uow_factory

    def list_recent(self, limit: int = 100) -> List[KpiApprover]:
        with self._uow_factory() as uow:
            return uow.approvers.list_recent(limit=limit)

    def list_recent_summary(self, limit: int = 100) -> list[dict]:
        with self._uow_factory() as uow:
            return uow.approvers.list_recent_summary(limit=limit)

    def create(self, dto: KpiApproverDTO) -> None:
        if not dto.approver_name or not dto.approver_name.strip():
            raise ValidationError("approver_name is required")
        if dto.kpi_version < 1:
            raise ValidationError("kpi_version must be >= 1")

        with self._uow_factory() as uow:
            definition = uow.definitions.get_by_identity(dto.kpi_id, dto.kpi_slug, dto.kpi_version)
            if definition is None:
                raise ValidationError("Referenced metric definition does not exist for provided id/slug/version")

            if uow.approvers.exists_for_kpi(dto.kpi_id, dto.kpi_slug, dto.kpi_version, dto.approver_name):
                raise ConflictError("Approver name already exists for this metric version")

            approver = KpiApprover(
                kpi_id=dto.kpi_id,
                kpi_slug=dto.kpi_slug,
                kpi_version=dto.kpi_version,
                approver_name=dto.approver_name.strip(),
                approver_email=dto.approver_email,
                approver_role=dto.approver_role,
                approval_notes=dto.approval_notes,
            )
            uow.approvers.insert(approver)
            uow.commit()
