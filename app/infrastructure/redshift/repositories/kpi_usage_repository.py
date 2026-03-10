from typing import List

from app.application.ports.kpi_usage_repository import KpiUsageRepository
from app.domain.models import KpiUsage


class RedshiftKpiUsageRepository(KpiUsageRepository):
    def __init__(self, executor):
        self._executor = executor

    def list_recent(self, limit: int = 100) -> List[KpiUsage]:
        sql = """
            select usage_id, kpi_id, kpi_slug, kpi_version,
                   usage_type, consumer_tool, reference_name, reference_url,
                   source_system, context_notes,
                   default_chart_type, approved_visualizations,
                   preferred_dimensions, json_serialize(preferred_filters) as preferred_filters_json,
                   row_level_security_notes, created_at
            from kpi_catalog.kpi_usage
            order by created_at desc
            limit cast(:limit as integer)
        """
        rows = self._executor.query(sql, {"limit": limit})
        return [self._map(row) for row in rows]

    def list_recent_summary(self, limit: int = 100) -> list[dict]:
        sql = """
            select usage_id, kpi_id, kpi_slug, kpi_version,
                   consumer_tool, usage_type, reference_name, created_at
            from kpi_catalog.kpi_usage
            order by created_at desc
            limit cast(:limit as integer)
        """
        return self._executor.query(sql, {"limit": limit})

    def get_by_usage_id(self, usage_id: int):
        sql = """
            select usage_id, kpi_id, kpi_slug, kpi_version,
                   usage_type, consumer_tool, reference_name, reference_url,
                   source_system, context_notes,
                   default_chart_type, approved_visualizations,
                   preferred_dimensions, json_serialize(preferred_filters) as preferred_filters_json,
                   row_level_security_notes, created_at
            from kpi_catalog.kpi_usage
            where usage_id = cast(:usage_id as bigint)
            limit 1
        """
        rows = self._executor.query(sql, {"usage_id": usage_id})
        return self._map(rows[0]) if rows else None

    def list_by_metric(self, kpi_slug: str, kpi_version: int) -> list[KpiUsage]:
        sql = """
            select usage_id, kpi_id, kpi_slug, kpi_version,
                   usage_type, consumer_tool, reference_name, reference_url,
                   source_system, context_notes,
                   default_chart_type, approved_visualizations,
                   preferred_dimensions, json_serialize(preferred_filters) as preferred_filters_json,
                   row_level_security_notes, created_at
            from kpi_catalog.kpi_usage
            where kpi_slug = :kpi_slug
              and kpi_version = cast(:kpi_version as integer)
            order by created_at desc, usage_id desc
        """
        rows = self._executor.query(sql, {"kpi_slug": kpi_slug, "kpi_version": kpi_version})
        return [self._map(row) for row in rows]

    def insert(self, usage: KpiUsage) -> None:
        sql = """
            insert into kpi_catalog.kpi_usage (
                kpi_id, kpi_slug, kpi_version,
                usage_type, consumer_tool, reference_name, reference_url,
                source_system, context_notes,
                default_chart_type, approved_visualizations,
                preferred_dimensions, preferred_filters,
                row_level_security_notes
            )
            values (
                :kpi_id, :kpi_slug, cast(:kpi_version as integer),
                :usage_type, :consumer_tool, :reference_name, nullif(:reference_url, '__APP_NULL_SENTINEL__'),
                nullif(:source_system, '__APP_NULL_SENTINEL__'), nullif(:context_notes, '__APP_NULL_SENTINEL__'),
                nullif(:default_chart_type, '__APP_NULL_SENTINEL__'), nullif(:approved_visualizations, '__APP_NULL_SENTINEL__'),
                nullif(:preferred_dimensions, '__APP_NULL_SENTINEL__'),
                case when nullif(:preferred_filters_json, '__APP_NULL_SENTINEL__') is null then null else json_parse(:preferred_filters_json) end,
                nullif(:row_level_security_notes, '__APP_NULL_SENTINEL__')
            )
        """
        self._executor.execute(
            sql,
            {
                "kpi_id": usage.kpi_id,
                "kpi_slug": usage.kpi_slug,
                "kpi_version": usage.kpi_version,
                "usage_type": usage.usage_type,
                "consumer_tool": usage.consumer_tool,
                "reference_name": usage.reference_name,
                "reference_url": usage.reference_url,
                "source_system": usage.source_system,
                "context_notes": usage.context_notes,
                "default_chart_type": usage.default_chart_type,
                "approved_visualizations": usage.approved_visualizations,
                "preferred_dimensions": usage.preferred_dimensions,
                "preferred_filters_json": usage.preferred_filters_json,
                "row_level_security_notes": usage.row_level_security_notes,
            },
        )

    def insert_many(self, usages: list[KpiUsage]) -> None:
        if not usages:
            return

        values_sql = []
        params: dict[str, object] = {}
        for idx, usage in enumerate(usages):
            values_sql.append(
                f"""(
                    :kpi_id_{idx}, :kpi_slug_{idx}, cast(:kpi_version_{idx} as integer),
                    :usage_type_{idx}, :consumer_tool_{idx}, :reference_name_{idx}, nullif(:reference_url_{idx}, '__APP_NULL_SENTINEL__'),
                    nullif(:source_system_{idx}, '__APP_NULL_SENTINEL__'), nullif(:context_notes_{idx}, '__APP_NULL_SENTINEL__'),
                    nullif(:default_chart_type_{idx}, '__APP_NULL_SENTINEL__'), nullif(:approved_visualizations_{idx}, '__APP_NULL_SENTINEL__'),
                    nullif(:preferred_dimensions_{idx}, '__APP_NULL_SENTINEL__'),
                    case when nullif(:preferred_filters_json_{idx}, '__APP_NULL_SENTINEL__') is null then null else json_parse(:preferred_filters_json_{idx}) end,
                    nullif(:row_level_security_notes_{idx}, '__APP_NULL_SENTINEL__')
                )"""
            )
            params.update(
                {
                    f"kpi_id_{idx}": usage.kpi_id,
                    f"kpi_slug_{idx}": usage.kpi_slug,
                    f"kpi_version_{idx}": usage.kpi_version,
                    f"usage_type_{idx}": usage.usage_type,
                    f"consumer_tool_{idx}": usage.consumer_tool,
                    f"reference_name_{idx}": usage.reference_name,
                    f"reference_url_{idx}": usage.reference_url,
                    f"source_system_{idx}": usage.source_system,
                    f"context_notes_{idx}": usage.context_notes,
                    f"default_chart_type_{idx}": usage.default_chart_type,
                    f"approved_visualizations_{idx}": usage.approved_visualizations,
                    f"preferred_dimensions_{idx}": usage.preferred_dimensions,
                    f"preferred_filters_json_{idx}": usage.preferred_filters_json,
                    f"row_level_security_notes_{idx}": usage.row_level_security_notes,
                }
            )

        sql = f"""
            insert into kpi_catalog.kpi_usage (
                kpi_id, kpi_slug, kpi_version,
                usage_type, consumer_tool, reference_name, reference_url,
                source_system, context_notes,
                default_chart_type, approved_visualizations,
                preferred_dimensions, preferred_filters,
                row_level_security_notes
            )
            values {", ".join(values_sql)}
        """
        self._executor.execute(sql, params)

    def update(self, usage: KpiUsage) -> None:
        sql = """
            update kpi_catalog.kpi_usage
            set
                kpi_id = :kpi_id,
                kpi_slug = :kpi_slug,
                kpi_version = cast(:kpi_version as integer),
                usage_type = :usage_type,
                consumer_tool = :consumer_tool,
                reference_name = :reference_name,
                reference_url = nullif(:reference_url, '__APP_NULL_SENTINEL__'),
                source_system = nullif(:source_system, '__APP_NULL_SENTINEL__'),
                context_notes = nullif(:context_notes, '__APP_NULL_SENTINEL__'),
                default_chart_type = nullif(:default_chart_type, '__APP_NULL_SENTINEL__'),
                approved_visualizations = nullif(:approved_visualizations, '__APP_NULL_SENTINEL__'),
                preferred_dimensions = nullif(:preferred_dimensions, '__APP_NULL_SENTINEL__'),
                preferred_filters = case when nullif(:preferred_filters_json, '__APP_NULL_SENTINEL__') is null then null else json_parse(:preferred_filters_json) end,
                row_level_security_notes = nullif(:row_level_security_notes, '__APP_NULL_SENTINEL__')
            where usage_id = cast(:usage_id as bigint)
        """
        self._executor.execute(
            sql,
            {
                "kpi_id": usage.kpi_id,
                "kpi_slug": usage.kpi_slug,
                "kpi_version": usage.kpi_version,
                "usage_type": usage.usage_type,
                "consumer_tool": usage.consumer_tool,
                "reference_name": usage.reference_name,
                "reference_url": usage.reference_url,
                "source_system": usage.source_system,
                "context_notes": usage.context_notes,
                "default_chart_type": usage.default_chart_type,
                "approved_visualizations": usage.approved_visualizations,
                "preferred_dimensions": usage.preferred_dimensions,
                "preferred_filters_json": usage.preferred_filters_json,
                "row_level_security_notes": usage.row_level_security_notes,
                "usage_id": usage.usage_id,
            },
        )

    @staticmethod
    def _map(row: dict) -> KpiUsage:
        return KpiUsage(
            usage_id=int(row["usage_id"]),
            kpi_id=row["kpi_id"],
            kpi_slug=row["kpi_slug"],
            kpi_version=int(row["kpi_version"]),
            usage_type=row["usage_type"],
            consumer_tool=row["consumer_tool"],
            reference_name=row["reference_name"],
            reference_url=row.get("reference_url"),
            source_system=row.get("source_system"),
            context_notes=row.get("context_notes"),
            default_chart_type=row.get("default_chart_type"),
            approved_visualizations=row.get("approved_visualizations"),
            preferred_dimensions=row.get("preferred_dimensions"),
            preferred_filters_json=row.get("preferred_filters_json"),
            row_level_security_notes=row.get("row_level_security_notes"),
            created_at=row.get("created_at"),
        )
