from typing import List

from app.application.ports.kpi_approver_repository import KpiApproverRepository
from app.domain.models import KpiApprover
from app.infrastructure.redshift.repositories._sql import render_limit


class RedshiftKpiApproverRepository(KpiApproverRepository):
    def __init__(self, executor):
        self._executor = executor

    def list_recent(self, limit: int = 100) -> List[KpiApprover]:
        sql = f"""
            select approver_id, kpi_id, kpi_slug, kpi_version,
                   approver_name, approver_email, approver_role,
                   approval_notes, approved_at, created_at
            from kpi_catalog.kpi_approver
            order by created_at desc
            limit {render_limit(limit)}
        """
        rows = self._executor.query(sql)
        return [self._map(row) for row in rows]

    def list_recent_summary(self, limit: int = 100) -> list[dict]:
        sql = f"""
            select approver_id, kpi_id, kpi_slug, kpi_version,
                   approver_name, approver_role, approved_at
            from kpi_catalog.kpi_approver
            order by created_at desc
            limit {render_limit(limit)}
        """
        return self._executor.query(sql)

    def insert(self, approver: KpiApprover) -> None:
        sql = """
            insert into kpi_catalog.kpi_approver (
                kpi_id, kpi_slug, kpi_version,
                approver_name, approver_email, approver_role,
                approval_notes
            )
            values (
                :kpi_id, :kpi_slug, cast(:kpi_version as integer),
                :approver_name, nullif(:approver_email, '__APP_NULL_SENTINEL__'), :approver_role,
                nullif(:approval_notes, '__APP_NULL_SENTINEL__')
            )
        """
        self._executor.execute(
            sql,
            {
                "kpi_id": approver.kpi_id,
                "kpi_slug": approver.kpi_slug,
                "kpi_version": approver.kpi_version,
                "approver_name": approver.approver_name,
                "approver_email": approver.approver_email,
                "approver_role": approver.approver_role,
                "approval_notes": approver.approval_notes,
            },
        )

    def exists_for_kpi(self, kpi_id: str, kpi_slug: str, kpi_version: int, approver_name: str) -> bool:
        sql = """
            select 1 as found
            from kpi_catalog.kpi_approver
            where kpi_id = :kpi_id
              and kpi_slug = :kpi_slug
              and kpi_version = cast(:kpi_version as integer)
              and lower(approver_name) = lower(:approver_name)
            limit 1
        """
        rows = self._executor.query(
            sql,
            {
                "kpi_id": kpi_id,
                "kpi_slug": kpi_slug,
                "kpi_version": kpi_version,
                "approver_name": approver_name,
            },
        )
        return bool(rows)

    @staticmethod
    def _map(row: dict) -> KpiApprover:
        return KpiApprover(
            approver_id=int(row["approver_id"]),
            kpi_id=row["kpi_id"],
            kpi_slug=row["kpi_slug"],
            kpi_version=int(row["kpi_version"]),
            approver_name=row["approver_name"],
            approver_email=row.get("approver_email"),
            approver_role=row["approver_role"],
            approval_notes=row.get("approval_notes"),
            approved_at=row.get("approved_at"),
            created_at=row.get("created_at"),
        )
