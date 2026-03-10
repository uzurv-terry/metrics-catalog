import json
import re
from datetime import date
from typing import Callable, List
from uuid import uuid4

from app.application.dto.kpi_definition_dto import KpiDefinitionDTO
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.exceptions import ConflictError, ValidationError
from app.domain.models import KpiDefinition


class KpiDefinitionService:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]):
        self._uow_factory = uow_factory

    def list_recent(self, limit: int = 100) -> List[KpiDefinition]:
        with self._uow_factory() as uow:
            return uow.definitions.list_recent(limit=limit)

    def list_recent_summary(self, limit: int = 100) -> list[dict]:
        with self._uow_factory() as uow:
            return uow.definitions.list_recent_summary(limit=limit)

    def get_by_key(self, kpi_slug: str, kpi_version: int) -> KpiDefinition | None:
        with self._uow_factory() as uow:
            return uow.definitions.get_by_key(kpi_slug, kpi_version)

    def create(self, dto: KpiDefinitionDTO) -> None:
        self._validate_dto(dto)
        kpi_slug = self._derive_slug(dto.kpi_name)
        model = self._to_model(dto, kpi_id=str(uuid4()), kpi_slug=kpi_slug)

        with self._uow_factory() as uow:
            existing_name = uow.definitions.get_by_name(dto.kpi_name)
            if existing_name:
                raise ConflictError("Metric name already exists")

            if uow.definitions.get_by_key(kpi_slug, dto.kpi_version):
                raise ConflictError("Derived metric slug/version already exists")

            if dto.status == "active":
                self._validate_two_approvals(dto)

            uow.definitions.insert(model)
            uow.commit()

    def update(self, current_kpi_slug: str, current_kpi_version: int, dto: KpiDefinitionDTO) -> None:
        self._validate_dto(dto)
        derived_slug = self._derive_slug(dto.kpi_name)

        with self._uow_factory() as uow:
            existing = uow.definitions.get_by_key(current_kpi_slug, current_kpi_version)
            if existing is None:
                raise ValidationError("Metric slug/version not found")

            existing_name = uow.definitions.get_by_name(dto.kpi_name)
            if existing_name and (
                existing_name.kpi_slug != existing.kpi_slug or existing_name.kpi_version != existing.kpi_version
            ):
                raise ConflictError("Metric name already exists")

            slug_collision = uow.definitions.get_by_key(derived_slug, dto.kpi_version)
            if slug_collision and slug_collision.kpi_id != existing.kpi_id:
                raise ConflictError("Derived metric slug/version already exists")

            if existing.status != "active" and dto.status == "active":
                self._validate_two_approvals(dto)

            model = self._to_model(dto, kpi_id=existing.kpi_id, kpi_slug=derived_slug)
            uow.definitions.update_by_key(current_kpi_slug, current_kpi_version, model)
            uow.commit()

    def _validate_dto(self, dto: KpiDefinitionDTO) -> None:
        if not dto.kpi_name or not dto.kpi_name.strip():
            raise ValidationError("kpi_name is required")
        if dto.kpi_version < 1:
            raise ValidationError("kpi_version must be >= 1")

        if dto.status == "active" and not dto.owner_team:
            raise ValidationError("owner_team is required when status is active")

        if dto.status == "draft" and dto.certification_level == "certified":
            raise ValidationError("status cannot be draft when certification level is certified")

        if dto.filter_conditions_json:
            json.loads(dto.filter_conditions_json)

        if dto.source_objects_json:
            json.loads(dto.source_objects_json)

    @staticmethod
    def _validate_two_approvals(dto: KpiDefinitionDTO) -> None:
        if not dto.approval_1_by or not dto.approval_2_by:
            raise ValidationError("status can only be set to active after two approvals")

    @staticmethod
    def _derive_slug(kpi_name: str) -> str:
        slug = kpi_name.strip().lower()
        slug = re.sub(r"[^a-z0-9]+", "_", slug)
        slug = re.sub(r"_+", "_", slug).strip("_")
        if not slug:
            raise ValidationError("Unable to derive slug from kpi_name")
        return slug

    def _to_model(self, dto: KpiDefinitionDTO, kpi_id: str, kpi_slug: str) -> KpiDefinition:
        return KpiDefinition(
            kpi_id=kpi_id,
            kpi_name=dto.kpi_name,
            kpi_slug=kpi_slug,
            kpi_version=dto.kpi_version,
            business_definition=dto.business_definition,
            owner_person=dto.owner_person,
            owner_team=dto.owner_team,
            status=dto.status,
            certification_level=dto.certification_level,
            formula=dto.formula,
            business_question=dto.business_question,
            effective_start_date=date.fromisoformat(dto.effective_start_date) if dto.effective_start_date else None,
            effective_end_date=date.fromisoformat(dto.effective_end_date) if dto.effective_end_date else None,
            change_reason=dto.change_reason,
            breaking_change_flag=bool(dto.breaking_change_flag),
            metric_query_reference=dto.metric_query_reference,
            source_objects_json=dto.source_objects_json,
            filter_conditions_json=dto.filter_conditions_json,
        )
