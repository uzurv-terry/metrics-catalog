from typing import Callable

from app.application.dto.catalog_note_dto import CatalogNoteDTO
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.exceptions import ValidationError
from app.domain.models import CatalogNote


class CatalogNoteService:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]):
        self._uow_factory = uow_factory

    def list_recent(self, limit: int = 100) -> list[CatalogNote]:
        with self._uow_factory() as uow:
            return uow.notes.list_recent(limit=limit)

    def list_recent_summary(self, limit: int = 100) -> list[dict]:
        with self._uow_factory() as uow:
            return uow.notes.list_recent_summary(limit=limit)

    def list_by_metric(self, kpi_slug: str, kpi_version: int) -> list[CatalogNote]:
        with self._uow_factory() as uow:
            return uow.notes.list_by_metric(kpi_slug, kpi_version)

    def list_by_report_id(self, report_id: int) -> list[CatalogNote]:
        with self._uow_factory() as uow:
            return uow.notes.list_by_report_ids([report_id])

    def list_by_report_ids(self, report_ids: list[int]) -> dict[int, list[CatalogNote]]:
        with self._uow_factory() as uow:
            notes = uow.notes.list_by_report_ids(report_ids)
        grouped: dict[int, list[CatalogNote]] = {}
        for note in notes:
            if note.report_id is None:
                continue
            grouped.setdefault(note.report_id, []).append(note)
        return grouped

    def create(self, dto: CatalogNoteDTO) -> None:
        self._validate_dto(dto)
        with self._uow_factory() as uow:
            if dto.note_scope == "metric_definition":
                definition = uow.definitions.get_by_identity(dto.kpi_id or "", dto.kpi_slug or "", dto.kpi_version or 0)
                if definition is None:
                    raise ValidationError("Referenced metric definition does not exist")
            elif dto.note_scope == "report":
                report = uow.reports.get_by_report_id(dto.report_id or 0)
                if report is None:
                    raise ValidationError("Referenced report does not exist")

            uow.notes.insert(
                CatalogNote(
                    note_scope=dto.note_scope,
                    note_body=dto.note_body,
                    author_name=dto.author_name,
                    kpi_id=dto.kpi_id,
                    kpi_slug=dto.kpi_slug,
                    kpi_version=dto.kpi_version,
                    report_id=dto.report_id,
                    note_type=dto.note_type,
                    note_title=dto.note_title,
                    author_email=dto.author_email,
                    is_active=bool(dto.is_active),
                )
            )
            uow.commit()

    @staticmethod
    def _validate_dto(dto: CatalogNoteDTO) -> None:
        if not dto.note_body or not dto.note_body.strip():
            raise ValidationError("note_body is required")
        if not dto.author_name or not dto.author_name.strip():
            raise ValidationError("author_name is required")
        if dto.note_scope not in {"metric_definition", "report"}:
            raise ValidationError("note_scope must be metric_definition or report")
        if dto.note_scope == "metric_definition":
            if not dto.kpi_id or not dto.kpi_slug or not dto.kpi_version:
                raise ValidationError("Metric notes require kpi_id, kpi_slug, and kpi_version")
            if dto.report_id is not None:
                raise ValidationError("Metric notes cannot include report_id")
        if dto.note_scope == "report":
            if not dto.report_id:
                raise ValidationError("Report notes require report_id")
            if dto.kpi_id or dto.kpi_slug or dto.kpi_version:
                raise ValidationError("Report notes cannot include metric identity")
