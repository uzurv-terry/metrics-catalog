from typing import List, Optional

from app.application.ports.kpi_definition_repository import KpiDefinitionRepository
from app.domain.models import KpiDefinition


class RedshiftKpiDefinitionRepository(KpiDefinitionRepository):
    def __init__(self, executor):
        self._executor = executor

    def get_by_key(self, kpi_slug: str, kpi_version: int) -> Optional[KpiDefinition]:
        sql = """
            select kpi_id, kpi_name, kpi_slug, kpi_version, business_definition,
                   owner_person, owner_team, status, certification_level, formula,
                   business_question, effective_start_date, effective_end_date,
                   change_reason, breaking_change_flag, metric_query_reference,
                   json_serialize(source_objects) as source_objects_json,
                   json_serialize(filter_conditions) as filter_conditions_json,
                   created_at, updated_at
            from kpi_catalog.kpi_definition
            where kpi_slug = :kpi_slug and kpi_version = cast(:kpi_version as integer)
            limit 1
        """
        rows = self._executor.query(sql, {"kpi_slug": kpi_slug, "kpi_version": kpi_version})
        return self._map(rows[0]) if rows else None

    def get_by_identity(self, kpi_id: str, kpi_slug: str, kpi_version: int) -> Optional[KpiDefinition]:
        sql = """
            select kpi_id, kpi_name, kpi_slug, kpi_version, business_definition,
                   owner_person, owner_team, status, certification_level, formula,
                   business_question, effective_start_date, effective_end_date,
                   change_reason, breaking_change_flag, metric_query_reference,
                   json_serialize(source_objects) as source_objects_json,
                   json_serialize(filter_conditions) as filter_conditions_json,
                   created_at, updated_at
            from kpi_catalog.kpi_definition
            where kpi_id = :kpi_id
              and kpi_slug = :kpi_slug
              and kpi_version = cast(:kpi_version as integer)
            limit 1
        """
        rows = self._executor.query(
            sql,
            {"kpi_id": kpi_id, "kpi_slug": kpi_slug, "kpi_version": kpi_version},
        )
        return self._map(rows[0]) if rows else None

    def get_by_name(self, kpi_name: str) -> Optional[KpiDefinition]:
        sql = """
            select kpi_id, kpi_name, kpi_slug, kpi_version, business_definition,
                   owner_person, owner_team, status, certification_level, formula,
                   business_question, effective_start_date, effective_end_date,
                   change_reason, breaking_change_flag, metric_query_reference,
                   json_serialize(source_objects) as source_objects_json,
                   json_serialize(filter_conditions) as filter_conditions_json,
                   created_at, updated_at
            from kpi_catalog.kpi_definition
            where lower(kpi_name) = lower(:kpi_name)
            order by created_at desc
            limit 1
        """
        rows = self._executor.query(sql, {"kpi_name": kpi_name})
        return self._map(rows[0]) if rows else None

    def list_recent(self, limit: int = 100) -> List[KpiDefinition]:
        sql = """
            select kpi_id, kpi_name, kpi_slug, kpi_version, business_definition,
                   owner_person, owner_team, status, certification_level, formula,
                   business_question, effective_start_date, effective_end_date,
                   change_reason, breaking_change_flag, metric_query_reference,
                   json_serialize(source_objects) as source_objects_json,
                   json_serialize(filter_conditions) as filter_conditions_json,
                   created_at, updated_at
            from kpi_catalog.kpi_definition
            order by created_at desc
            limit cast(:limit as integer)
        """
        rows = self._executor.query(sql, {"limit": limit})
        return [self._map(row) for row in rows]

    def list_recent_summary(self, limit: int = 100) -> list[dict]:
        sql = """
            select kpi_id, kpi_slug, kpi_version, kpi_name,
                   status, certification_level, owner_team, created_at
            from kpi_catalog.kpi_definition
            order by created_at desc
            limit cast(:limit as integer)
        """
        return self._executor.query(sql, {"limit": limit})

    def insert(self, definition: KpiDefinition) -> None:
        sql = """
            insert into kpi_catalog.kpi_definition (
                kpi_id, kpi_name, kpi_slug, kpi_version,
                business_definition, owner_person, owner_team,
                status, certification_level, formula,
                business_question, effective_start_date, effective_end_date,
                change_reason, breaking_change_flag, metric_query_reference,
                source_objects, filter_conditions
            )
            values (
                :kpi_id, :kpi_name, :kpi_slug, cast(:kpi_version as integer),
                :business_definition, :owner_person, :owner_team,
                :status, :certification_level, :formula,
                nullif(:business_question, '__APP_NULL_SENTINEL__'),
                cast(nullif(:effective_start_date, '__APP_NULL_SENTINEL__') as date),
                cast(nullif(:effective_end_date, '__APP_NULL_SENTINEL__') as date),
                nullif(:change_reason, '__APP_NULL_SENTINEL__'),
                cast(:breaking_change_flag as boolean),
                nullif(:metric_query_reference, '__APP_NULL_SENTINEL__'),
                case when nullif(:source_objects_json, '__APP_NULL_SENTINEL__') is null then null else json_parse(:source_objects_json) end,
                case when nullif(:filter_conditions_json, '__APP_NULL_SENTINEL__') is null then null else json_parse(:filter_conditions_json) end
            )
        """
        self._executor.execute(
            sql,
            {
                "kpi_id": definition.kpi_id,
                "kpi_name": definition.kpi_name,
                "kpi_slug": definition.kpi_slug,
                "kpi_version": definition.kpi_version,
                "business_definition": definition.business_definition,
                "owner_person": definition.owner_person,
                "owner_team": definition.owner_team,
                "status": definition.status,
                "certification_level": definition.certification_level,
                "formula": definition.formula,
                "business_question": definition.business_question,
                "effective_start_date": definition.effective_start_date,
                "effective_end_date": definition.effective_end_date,
                "change_reason": definition.change_reason,
                "breaking_change_flag": definition.breaking_change_flag,
                "metric_query_reference": definition.metric_query_reference,
                "source_objects_json": definition.source_objects_json,
                "filter_conditions_json": definition.filter_conditions_json,
            },
        )

    def update_by_key(
        self, current_kpi_slug: str, current_kpi_version: int, definition: KpiDefinition
    ) -> None:
        sql = """
            update kpi_catalog.kpi_definition
            set
                kpi_slug = :new_kpi_slug,
                kpi_name = :kpi_name,
                business_definition = :business_definition,
                owner_person = :owner_person,
                owner_team = :owner_team,
                status = :status,
                certification_level = :certification_level,
                formula = :formula,
                business_question = nullif(:business_question, '__APP_NULL_SENTINEL__'),
                effective_start_date = cast(nullif(:effective_start_date, '__APP_NULL_SENTINEL__') as date),
                effective_end_date = cast(nullif(:effective_end_date, '__APP_NULL_SENTINEL__') as date),
                change_reason = nullif(:change_reason, '__APP_NULL_SENTINEL__'),
                breaking_change_flag = cast(:breaking_change_flag as boolean),
                metric_query_reference = nullif(:metric_query_reference, '__APP_NULL_SENTINEL__'),
                source_objects = case when nullif(:source_objects_json, '__APP_NULL_SENTINEL__') is null then null else json_parse(:source_objects_json) end,
                filter_conditions = case when nullif(:filter_conditions_json, '__APP_NULL_SENTINEL__') is null then null else json_parse(:filter_conditions_json) end,
                updated_at = getdate()
            where kpi_slug = :current_kpi_slug
              and kpi_version = cast(:current_kpi_version as integer)
        """
        self._executor.execute(
            sql,
            {
                "new_kpi_slug": definition.kpi_slug,
                "kpi_name": definition.kpi_name,
                "business_definition": definition.business_definition,
                "owner_person": definition.owner_person,
                "owner_team": definition.owner_team,
                "status": definition.status,
                "certification_level": definition.certification_level,
                "formula": definition.formula,
                "business_question": definition.business_question,
                "effective_start_date": definition.effective_start_date,
                "effective_end_date": definition.effective_end_date,
                "change_reason": definition.change_reason,
                "breaking_change_flag": definition.breaking_change_flag,
                "metric_query_reference": definition.metric_query_reference,
                "source_objects_json": definition.source_objects_json,
                "filter_conditions_json": definition.filter_conditions_json,
                "current_kpi_slug": current_kpi_slug,
                "current_kpi_version": current_kpi_version,
            },
        )

    @staticmethod
    def _map(row: dict) -> KpiDefinition:
        return KpiDefinition(
            kpi_id=row["kpi_id"],
            kpi_name=row["kpi_name"],
            kpi_slug=row["kpi_slug"],
            kpi_version=int(row["kpi_version"]),
            business_definition=row["business_definition"],
            owner_person=row["owner_person"],
            owner_team=row["owner_team"],
            status=row["status"],
            certification_level=row["certification_level"],
            formula=row["formula"],
            business_question=row.get("business_question"),
            effective_start_date=row.get("effective_start_date"),
            effective_end_date=row.get("effective_end_date"),
            change_reason=row.get("change_reason"),
            breaking_change_flag=bool(row.get("breaking_change_flag")),
            metric_query_reference=row.get("metric_query_reference"),
            source_objects_json=row.get("source_objects_json"),
            filter_conditions_json=row.get("filter_conditions_json"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )
