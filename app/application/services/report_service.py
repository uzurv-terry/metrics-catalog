import re
from typing import Callable, List

from app.application.dto.report_dto import ReportDTO
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.exceptions import ConflictError, ValidationError
from app.domain.models import Report


class ReportService:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]):
        self._uow_factory = uow_factory

    def list_recent(self, limit: int = 100) -> List[Report]:
        with self._uow_factory() as uow:
            return uow.reports.list_recent(limit=limit)

    def list_recent_summary(self, limit: int = 100) -> list[dict]:
        with self._uow_factory() as uow:
            return uow.reports.list_recent_summary(limit=limit)

    def get_by_report_id(self, report_id: int) -> Report | None:
        with self._uow_factory() as uow:
            return uow.reports.get_by_report_id(report_id)

    def search(self, query: str, limit: int = 20) -> list[dict]:
        query = query.strip()
        if len(query) < 2:
            return []
        with self._uow_factory() as uow:
            return uow.reports.search(query, limit=limit)

    def create(self, dto: ReportDTO) -> None:
        self._validate_dto(dto)
        report_slug = self._derive_slug(dto.report_name)
        model = self._to_model(dto, report_slug=report_slug)
        with self._uow_factory() as uow:
            existing = uow.reports.get_by_tool_and_slug(dto.consumer_tool, report_slug)
            if existing is not None:
                raise ConflictError("A report with this tool and derived slug already exists")
            uow.reports.insert(model)
            uow.commit()

    def update(self, report_id: int, dto: ReportDTO) -> None:
        self._validate_dto(dto)
        report_slug = self._derive_slug(dto.report_name)
        with self._uow_factory() as uow:
            existing = uow.reports.get_by_report_id(report_id)
            if existing is None:
                raise ValidationError("Report not found")
            collision = uow.reports.get_by_tool_and_slug(dto.consumer_tool, report_slug)
            if collision is not None and collision.report_id != report_id:
                raise ConflictError("A report with this tool and derived slug already exists")
            uow.reports.update(
                self._to_model(dto, report_slug=report_slug, report_id=report_id)
            )
            uow.commit()

    @staticmethod
    def _validate_dto(dto: ReportDTO) -> None:
        if not dto.report_name or not dto.report_name.strip():
            raise ValidationError("report_name is required")
        if not dto.consumer_tool or not dto.consumer_tool.strip():
            raise ValidationError("consumer_tool is required")
        if not dto.report_type or not dto.report_type.strip():
            raise ValidationError("report_type is required")

    @staticmethod
    def _derive_slug(report_name: str) -> str:
        slug = report_name.strip().lower()
        slug = re.sub(r"[^a-z0-9]+", "_", slug)
        slug = re.sub(r"_+", "_", slug).strip("_")
        if not slug:
            raise ValidationError("Unable to derive slug from report_name")
        return slug

    @staticmethod
    def _to_model(dto: ReportDTO, report_slug: str, report_id: int | None = None) -> Report:
        return Report(
            report_id=report_id,
            report_slug=report_slug,
            report_name=dto.report_name,
            report_type=dto.report_type,
            consumer_tool=dto.consumer_tool,
            report_url=dto.report_url,
            source_system=dto.source_system,
            owner_person=dto.owner_person,
            owner_team=dto.owner_team,
            status=dto.status,
        )
