from typing import List

from app.application.ports.kpi_usage_repository import KpiUsageRepository
from app.domain.models import KpiUsage
from app.infrastructure.redshift.repositories._sql import render_limit


class RedshiftKpiUsageRepository(KpiUsageRepository):
    def __init__(self, executor):
        self._executor = executor

    def list_recent(self, limit: int = 100) -> List[KpiUsage]:
        sql = f"""
            select u.usage_id, u.kpi_id, u.kpi_slug, u.kpi_version, u.report_id,
                   u.usage_type,
                   default_chart_type, approved_visualizations,
                   preferred_dimensions, json_serialize(preferred_filters) as preferred_filters_json,
                   row_level_security_notes, u.created_at, u.updated_at,
                   r.report_name, r.report_slug, r.report_type, r.consumer_tool,
                   r.report_url, r.source_system
            from kpi_catalog.kpi_usage u
            join kpi_catalog.report r
              on r.report_id = u.report_id
            order by u.created_at desc
            limit {render_limit(limit)}
        """
        rows = self._executor.query(sql)
        return [self._map(row) for row in rows]

    def list_recent_summary(self, limit: int = 100) -> list[dict]:
        sql = f"""
            select u.usage_id, u.kpi_id, u.kpi_slug, u.kpi_version,
                   u.report_id, r.consumer_tool, u.usage_type, r.report_name, r.report_type,
                   u.created_at
            from kpi_catalog.kpi_usage u
            join kpi_catalog.report r
              on r.report_id = u.report_id
            order by u.created_at desc
            limit {render_limit(limit)}
        """
        return self._executor.query(sql)

    def get_by_usage_id(self, usage_id: int):
        sql = """
            select u.usage_id, u.kpi_id, u.kpi_slug, u.kpi_version, u.report_id,
                   u.usage_type,
                   default_chart_type, approved_visualizations,
                   preferred_dimensions, json_serialize(preferred_filters) as preferred_filters_json,
                   row_level_security_notes, u.created_at, u.updated_at,
                   r.report_name, r.report_slug, r.report_type, r.consumer_tool,
                   r.report_url, r.source_system
            from kpi_catalog.kpi_usage u
            join kpi_catalog.report r
              on r.report_id = u.report_id
            where u.usage_id = cast(:usage_id as bigint)
            limit 1
        """
        rows = self._executor.query(sql, {"usage_id": usage_id})
        return self._map(rows[0]) if rows else None

    def list_by_metric(self, kpi_slug: str, kpi_version: int) -> list[KpiUsage]:
        sql = """
            select u.usage_id, u.kpi_id, u.kpi_slug, u.kpi_version, u.report_id,
                   u.usage_type,
                   default_chart_type, approved_visualizations,
                   preferred_dimensions, json_serialize(preferred_filters) as preferred_filters_json,
                   row_level_security_notes, u.created_at, u.updated_at,
                   r.report_name, r.report_slug, r.report_type, r.consumer_tool,
                   r.report_url, r.source_system
            from kpi_catalog.kpi_usage u
            join kpi_catalog.report r
              on r.report_id = u.report_id
            where u.kpi_slug = :kpi_slug
              and u.kpi_version = cast(:kpi_version as integer)
            order by u.created_at desc, u.usage_id desc
        """
        rows = self._executor.query(sql, {"kpi_slug": kpi_slug, "kpi_version": kpi_version})
        return [self._map(row) for row in rows]

    def insert(self, usage: KpiUsage) -> None:
        sql = """
            insert into kpi_catalog.kpi_usage (
                kpi_id, kpi_slug, kpi_version, report_id,
                usage_type,
                default_chart_type, approved_visualizations,
                preferred_dimensions, preferred_filters,
                row_level_security_notes
            )
            values (
                :kpi_id, :kpi_slug, cast(:kpi_version as integer), cast(:report_id as bigint),
                :usage_type,
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
                "report_id": usage.report_id,
                "usage_type": usage.usage_type,
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
                    :kpi_id_{idx}, :kpi_slug_{idx}, cast(:kpi_version_{idx} as integer), cast(:report_id_{idx} as bigint),
                    :usage_type_{idx},
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
                    f"report_id_{idx}": usage.report_id,
                    f"usage_type_{idx}": usage.usage_type,
                    f"default_chart_type_{idx}": usage.default_chart_type,
                    f"approved_visualizations_{idx}": usage.approved_visualizations,
                    f"preferred_dimensions_{idx}": usage.preferred_dimensions,
                    f"preferred_filters_json_{idx}": usage.preferred_filters_json,
                    f"row_level_security_notes_{idx}": usage.row_level_security_notes,
                }
            )

        sql = f"""
            insert into kpi_catalog.kpi_usage (
                kpi_id, kpi_slug, kpi_version, report_id,
                usage_type,
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
                report_id = cast(:report_id as bigint),
                usage_type = :usage_type,
                default_chart_type = nullif(:default_chart_type, '__APP_NULL_SENTINEL__'),
                approved_visualizations = nullif(:approved_visualizations, '__APP_NULL_SENTINEL__'),
                preferred_dimensions = nullif(:preferred_dimensions, '__APP_NULL_SENTINEL__'),
                preferred_filters = case when nullif(:preferred_filters_json, '__APP_NULL_SENTINEL__') is null then null else json_parse(:preferred_filters_json) end,
                row_level_security_notes = nullif(:row_level_security_notes, '__APP_NULL_SENTINEL__'),
                updated_at = getdate()
            where usage_id = cast(:usage_id as bigint)
        """
        self._executor.execute(
            sql,
            {
                "kpi_id": usage.kpi_id,
                "kpi_slug": usage.kpi_slug,
                "kpi_version": usage.kpi_version,
                "report_id": usage.report_id,
                "usage_type": usage.usage_type,
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
            report_id=int(row["report_id"]),
            usage_type=row["usage_type"],
            default_chart_type=row.get("default_chart_type"),
            approved_visualizations=row.get("approved_visualizations"),
            preferred_dimensions=row.get("preferred_dimensions"),
            preferred_filters_json=row.get("preferred_filters_json"),
            row_level_security_notes=row.get("row_level_security_notes"),
            report_name=row.get("report_name"),
            report_slug=row.get("report_slug"),
            report_type=row.get("report_type"),
            consumer_tool=row.get("consumer_tool"),
            report_url=row.get("report_url"),
            source_system=row.get("source_system"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )
