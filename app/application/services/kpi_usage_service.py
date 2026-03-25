import json
from typing import Callable, List

from app.application.dto.kpi_usage_dto import KpiUsageDTO
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.exceptions import ValidationError
from app.domain.models import KpiUsage


class KpiUsageService:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]):
        self._uow_factory = uow_factory

    def list_recent(self, limit: int = 100) -> List[KpiUsage]:
        with self._uow_factory() as uow:
            return uow.usage.list_recent(limit=limit)

    def list_recent_summary(self, limit: int = 100) -> list[dict]:
        with self._uow_factory() as uow:
            return uow.usage.list_recent_summary(limit=limit)

    def get_by_usage_id(self, usage_id: int) -> KpiUsage | None:
        with self._uow_factory() as uow:
            return uow.usage.get_by_usage_id(usage_id)

    def list_by_metric(self, kpi_slug: str, kpi_version: int) -> list[KpiUsage]:
        with self._uow_factory() as uow:
            return uow.usage.list_by_metric(kpi_slug, kpi_version)

    def create(self, dto: KpiUsageDTO) -> None:
        self.create_many([dto])

    def create_many(self, dtos: list[KpiUsageDTO]) -> None:
        if not dtos:
            raise ValidationError("At least one usage row is required")

        for dto in dtos:
            if dto.preferred_filters_json:
                json.loads(dto.preferred_filters_json)

        first = dtos[0]

        with self._uow_factory() as uow:
            definition = uow.definitions.get_by_identity(first.kpi_id, first.kpi_slug, first.kpi_version)
            if definition is None:
                raise ValidationError("Referenced metric definition does not exist for provided id/slug/version")
            report = uow.reports.get_by_report_id(first.report_id)
            if report is None:
                raise ValidationError("Referenced report does not exist")

            usages: list[KpiUsage] = []
            for dto in dtos:
                if (
                    dto.kpi_id != first.kpi_id
                    or dto.kpi_slug != first.kpi_slug
                    or dto.kpi_version != first.kpi_version
                    or dto.report_id != first.report_id
                ):
                    raise ValidationError("All usage rows in a batch must reference the same metric identity and report")

                if report.consumer_tool == "tableau" and report.report_type == "dashboard":
                    if definition.status != "active" or definition.certification_level != "certified":
                        raise ValidationError("Tableau dashboard usage requires an active + certified metric")

                usages.append(
                    KpiUsage(
                        kpi_id=dto.kpi_id,
                        kpi_slug=dto.kpi_slug,
                        kpi_version=dto.kpi_version,
                        report_id=dto.report_id,
                        usage_type=dto.usage_type,
                        default_chart_type=dto.default_chart_type,
                        approved_visualizations=dto.approved_visualizations,
                        preferred_dimensions=dto.preferred_dimensions,
                        preferred_filters_json=dto.preferred_filters_json,
                        row_level_security_notes=dto.row_level_security_notes,
                    )
                )

            uow.usage.insert_many(usages)
            uow.commit()

    def update(self, usage_id: int, dto: KpiUsageDTO) -> None:
        if dto.preferred_filters_json:
            json.loads(dto.preferred_filters_json)

        with self._uow_factory() as uow:
            if uow.usage.get_by_usage_id(usage_id) is None:
                raise ValidationError("Usage row not found")

            definition = uow.definitions.get_by_identity(dto.kpi_id, dto.kpi_slug, dto.kpi_version)
            if definition is None:
                raise ValidationError("Referenced metric definition does not exist for provided id/slug/version")
            report = uow.reports.get_by_report_id(dto.report_id)
            if report is None:
                raise ValidationError("Referenced report does not exist")

            if report.consumer_tool == "tableau" and report.report_type == "dashboard":
                if definition.status != "active" or definition.certification_level != "certified":
                    raise ValidationError("Tableau dashboard usage requires an active + certified metric")

            usage = KpiUsage(
                usage_id=usage_id,
                kpi_id=dto.kpi_id,
                kpi_slug=dto.kpi_slug,
                kpi_version=dto.kpi_version,
                report_id=dto.report_id,
                usage_type=dto.usage_type,
                default_chart_type=dto.default_chart_type,
                approved_visualizations=dto.approved_visualizations,
                preferred_dimensions=dto.preferred_dimensions,
                preferred_filters_json=dto.preferred_filters_json,
                row_level_security_notes=dto.row_level_security_notes,
            )
            uow.usage.update(usage)
            uow.commit()
