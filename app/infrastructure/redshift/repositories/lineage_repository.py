from app.application.ports.lineage_repository import LineageRepository


class RedshiftLineageRepository(LineageRepository):
    def __init__(self, executor):
        self._executor = executor

    def get_kpi_lineage_rows(self, kpi_slug: str, kpi_version: int, max_edges: int) -> list[dict]:
        sql = """
            select
                k.kpi_id,
                k.kpi_slug,
                k.kpi_version,
                k.kpi_name,
                k.status,
                k.certification_level,
                k.metric_query_reference,
                u.usage_id,
                u.consumer_tool,
                u.reference_name,
                u.reference_url,
                u.usage_type
            from kpi_catalog.kpi_definition k
            left join kpi_catalog.kpi_usage u
              on k.kpi_slug = u.kpi_slug
             and k.kpi_version = u.kpi_version
            where k.kpi_slug = :kpi_slug
              and k.kpi_version = cast(:kpi_version as integer)
            order by u.created_at desc
            limit cast(:max_edges as integer)
        """
        return self._executor.query(
            sql,
            {
                "kpi_slug": kpi_slug,
                "kpi_version": kpi_version,
                "max_edges": max_edges,
            },
        )

    def get_report_lineage_rows(
        self, consumer_tool: str, reference_name: str, max_edges: int
    ) -> list[dict]:
        sql = """
            select
                u.usage_id,
                u.consumer_tool,
                u.reference_name,
                u.reference_url,
                u.usage_type,
                k.kpi_id,
                k.kpi_slug,
                k.kpi_version,
                k.kpi_name,
                k.status,
                k.certification_level,
                k.metric_query_reference
            from kpi_catalog.kpi_usage u
            join kpi_catalog.kpi_definition k
              on u.kpi_slug = k.kpi_slug
             and u.kpi_version = k.kpi_version
            where lower(u.consumer_tool) = lower(:consumer_tool)
              and lower(u.reference_name) = lower(:reference_name)
            order by k.kpi_slug, k.kpi_version
            limit cast(:max_edges as integer)
        """
        return self._executor.query(
            sql,
            {
                "consumer_tool": consumer_tool,
                "reference_name": reference_name,
                "max_edges": max_edges,
            },
        )

    def search_kpis(self, query: str, limit: int) -> list[dict]:
        sql = """
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
            limit cast(:limit as integer)
        """
        return self._executor.query(
            sql,
            {
                "pattern": f"%{query}%",
                "prefix_pattern": f"{query}%",
                "exact_query": query,
                "limit": limit,
            },
        )

    def search_reports(self, query: str, limit: int) -> list[dict]:
        sql = """
            select
                consumer_tool,
                reference_name,
                max(reference_url) as reference_url,
                count(*) as usage_count
            from kpi_catalog.kpi_usage
            where lower(reference_name) like lower(:pattern)
            group by consumer_tool, reference_name
            order by
                case
                    when lower(reference_name) = lower(:exact_query) then 0
                    when lower(reference_name) like lower(:prefix_pattern) then 1
                    else 2
                end,
                usage_count desc,
                reference_name asc
            limit cast(:limit as integer)
        """
        return self._executor.query(
            sql,
            {
                "pattern": f"%{query}%",
                "prefix_pattern": f"{query}%",
                "exact_query": query,
                "limit": limit,
            },
        )
