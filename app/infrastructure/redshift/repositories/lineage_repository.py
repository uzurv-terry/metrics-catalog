from app.application.ports.lineage_repository import LineageRepository
from app.infrastructure.redshift.repositories._sql import render_limit


class RedshiftLineageRepository(LineageRepository):
    def __init__(self, executor):
        self._executor = executor

    def get_kpi_lineage_rows(self, kpi_slug: str, kpi_version: int, max_edges: int) -> list[dict]:
        sql = f"""
            select
                k.kpi_id,
                k.kpi_slug,
                k.kpi_version,
                k.kpi_name,
                k.status,
                k.certification_level,
                k.metric_query_reference,
                u.usage_id,
                u.report_id,
                u.usage_type,
                r.consumer_tool,
                r.report_name,
                r.report_slug,
                r.report_url,
                r.report_type
            from kpi_catalog.kpi_definition k
            left join kpi_catalog.kpi_usage u
              on k.kpi_slug = u.kpi_slug
             and k.kpi_version = u.kpi_version
            left join kpi_catalog.report r
              on r.report_id = u.report_id
            where k.kpi_slug = :kpi_slug
              and k.kpi_version = cast(:kpi_version as integer)
            order by u.created_at desc
            limit {render_limit(max_edges, name='max_edges')}
        """
        return self._executor.query(
            sql,
            {
                "kpi_slug": kpi_slug,
                "kpi_version": kpi_version,
            },
        )

    def get_report_lineage_rows(self, report_id: int, max_edges: int) -> list[dict]:
        sql = f"""
            select
                u.usage_id,
                u.report_id,
                u.usage_type,
                r.consumer_tool,
                r.report_name,
                r.report_slug,
                r.report_url,
                r.report_type,
                k.kpi_id,
                k.kpi_slug,
                k.kpi_version,
                k.kpi_name,
                k.status,
                k.certification_level,
                k.metric_query_reference
            from kpi_catalog.kpi_usage u
            join kpi_catalog.report r
              on r.report_id = u.report_id
            join kpi_catalog.kpi_definition k
              on u.kpi_slug = k.kpi_slug
             and u.kpi_version = k.kpi_version
            where u.report_id = cast(:report_id as bigint)
            order by k.kpi_slug, k.kpi_version
            limit {render_limit(max_edges, name='max_edges')}
        """
        return self._executor.query(
            sql,
            {
                "report_id": report_id,
            },
        )

    def search_kpis(self, query: str, limit: int) -> list[dict]:
        sql = f"""
            select
                kpi_id,
                kpi_slug,
                kpi_version,
                kpi_name,
                status,
                certification_level
            from kpi_catalog.kpi_definition
            where lower(kpi_name) like lower(:pattern)
               or lower(kpi_slug) like lower(:pattern)
               or lower(kpi_id) like lower(:pattern)
            order by
                case
                    when lower(kpi_slug) = lower(:exact_query) then 0
                    when lower(kpi_id) = lower(:exact_query) then 1
                    when lower(kpi_name) = lower(:exact_query) then 2
                    when lower(kpi_slug) like lower(:prefix_pattern) then 3
                    when lower(kpi_id) like lower(:prefix_pattern) then 4
                    when lower(kpi_name) like lower(:prefix_pattern) then 5
                    else 6
                end,
                updated_at desc,
                created_at desc
            limit {render_limit(limit)}
        """
        return self._executor.query(
            sql,
            {
                "pattern": f"%{query}%",
                "prefix_pattern": f"{query}%",
                "exact_query": query,
            },
        )

    def search_reports(self, query: str, limit: int) -> list[dict]:
        sql = f"""
            select
                r.report_id,
                r.consumer_tool,
                r.report_name,
                r.report_slug,
                r.report_type,
                r.report_url,
                count(u.usage_id) as usage_count
            from kpi_catalog.report r
            left join kpi_catalog.kpi_usage u
              on u.report_id = r.report_id
            where lower(r.report_name) like lower(:pattern)
               or lower(r.report_slug) like lower(:pattern)
               or lower(r.consumer_tool) like lower(:pattern)
            group by r.report_id, r.consumer_tool, r.report_name, r.report_slug, r.report_type, r.report_url
            order by
                case
                    when lower(r.report_name) = lower(:exact_query) then 0
                    when lower(r.report_slug) = lower(:exact_query) then 1
                    when lower(r.report_name) like lower(:prefix_pattern) then 2
                    when lower(r.report_slug) like lower(:prefix_pattern) then 3
                    else 4
                end,
                usage_count desc,
                r.report_name asc
            limit {render_limit(limit)}
        """
        return self._executor.query(
            sql,
            {
                "pattern": f"%{query}%",
                "prefix_pattern": f"{query}%",
                "exact_query": query,
            },
        )
