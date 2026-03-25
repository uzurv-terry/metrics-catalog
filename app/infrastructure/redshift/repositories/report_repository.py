from typing import List, Optional

from app.application.ports.report_repository import ReportRepository
from app.domain.models import Report
from app.infrastructure.redshift.repositories._sql import render_limit


class RedshiftReportRepository(ReportRepository):
    def __init__(self, executor):
        self._executor = executor

    def list_recent(self, limit: int = 100) -> List[Report]:
        sql = f"""
            select report_id, report_slug, report_name, report_type, consumer_tool,
                   report_url, source_system, owner_person, owner_team, status,
                   created_at, updated_at
            from kpi_catalog.report
            order by created_at desc, report_id desc
            limit {render_limit(limit)}
        """
        rows = self._executor.query(sql)
        return [self._map(row) for row in rows]

    def list_recent_summary(self, limit: int = 100) -> list[dict]:
        sql = f"""
            select report_id, report_name, report_slug, report_type, consumer_tool,
                   status, created_at
            from kpi_catalog.report
            order by created_at desc, report_id desc
            limit {render_limit(limit)}
        """
        return self._executor.query(sql)

    def get_by_report_id(self, report_id: int) -> Optional[Report]:
        sql = """
            select report_id, report_slug, report_name, report_type, consumer_tool,
                   report_url, source_system, owner_person, owner_team, status,
                   created_at, updated_at
            from kpi_catalog.report
            where report_id = cast(:report_id as bigint)
            limit 1
        """
        rows = self._executor.query(sql, {"report_id": report_id})
        return self._map(rows[0]) if rows else None

    def get_by_tool_and_slug(self, consumer_tool: str, report_slug: str) -> Optional[Report]:
        sql = """
            select report_id, report_slug, report_name, report_type, consumer_tool,
                   report_url, source_system, owner_person, owner_team, status,
                   created_at, updated_at
            from kpi_catalog.report
            where lower(consumer_tool) = lower(:consumer_tool)
              and lower(report_slug) = lower(:report_slug)
            limit 1
        """
        rows = self._executor.query(sql, {"consumer_tool": consumer_tool, "report_slug": report_slug})
        return self._map(rows[0]) if rows else None

    def search(self, query: str, limit: int = 20) -> list[dict]:
        sql = f"""
            select
                report_id,
                report_name,
                report_slug,
                report_type,
                consumer_tool,
                report_url,
                source_system,
                status
            from kpi_catalog.report
            where lower(report_name) like lower(:pattern)
               or lower(report_slug) like lower(:pattern)
               or lower(consumer_tool) like lower(:pattern)
            order by
                case
                    when lower(report_name) = lower(:exact_query) then 0
                    when lower(report_slug) = lower(:exact_query) then 1
                    when lower(report_name) like lower(:prefix_pattern) then 2
                    when lower(report_slug) like lower(:prefix_pattern) then 3
                    else 4
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

    def insert(self, report: Report) -> None:
        sql = """
            insert into kpi_catalog.report (
                report_slug, report_name, report_type, consumer_tool,
                report_url, source_system, owner_person, owner_team, status
            )
            values (
                :report_slug, :report_name, :report_type, :consumer_tool,
                nullif(:report_url, '__APP_NULL_SENTINEL__'),
                nullif(:source_system, '__APP_NULL_SENTINEL__'),
                nullif(:owner_person, '__APP_NULL_SENTINEL__'),
                nullif(:owner_team, '__APP_NULL_SENTINEL__'),
                :status
            )
        """
        self._executor.execute(
            sql,
            {
                "report_slug": report.report_slug,
                "report_name": report.report_name,
                "report_type": report.report_type,
                "consumer_tool": report.consumer_tool,
                "report_url": report.report_url,
                "source_system": report.source_system,
                "owner_person": report.owner_person,
                "owner_team": report.owner_team,
                "status": report.status,
            },
        )

    def update(self, report: Report) -> None:
        sql = """
            update kpi_catalog.report
            set
                report_slug = :report_slug,
                report_name = :report_name,
                report_type = :report_type,
                consumer_tool = :consumer_tool,
                report_url = nullif(:report_url, '__APP_NULL_SENTINEL__'),
                source_system = nullif(:source_system, '__APP_NULL_SENTINEL__'),
                owner_person = nullif(:owner_person, '__APP_NULL_SENTINEL__'),
                owner_team = nullif(:owner_team, '__APP_NULL_SENTINEL__'),
                status = :status,
                updated_at = getdate()
            where report_id = cast(:report_id as bigint)
        """
        self._executor.execute(
            sql,
            {
                "report_id": report.report_id,
                "report_slug": report.report_slug,
                "report_name": report.report_name,
                "report_type": report.report_type,
                "consumer_tool": report.consumer_tool,
                "report_url": report.report_url,
                "source_system": report.source_system,
                "owner_person": report.owner_person,
                "owner_team": report.owner_team,
                "status": report.status,
            },
        )

    @staticmethod
    def _map(row: dict) -> Report:
        return Report(
            report_id=int(row["report_id"]),
            report_slug=row["report_slug"],
            report_name=row["report_name"],
            report_type=row["report_type"],
            consumer_tool=row["consumer_tool"],
            report_url=row.get("report_url"),
            source_system=row.get("source_system"),
            owner_person=row.get("owner_person"),
            owner_team=row.get("owner_team"),
            status=row["status"],
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )
