from typing import List

from app.application.ports.catalog_note_repository import CatalogNoteRepository
from app.domain.models import CatalogNote
from app.infrastructure.redshift.repositories._sql import render_limit


class RedshiftCatalogNoteRepository(CatalogNoteRepository):
    def __init__(self, executor):
        self._executor = executor

    def list_recent(self, limit: int = 100) -> List[CatalogNote]:
        sql = f"""
            select n.note_id, n.note_scope, n.kpi_id, n.kpi_slug, n.kpi_version,
                   n.report_id, n.note_type, n.note_title, n.note_body,
                   n.author_name, n.author_email, n.is_active, n.created_at,
                   n.updated_at, r.report_name
            from kpi_catalog.catalog_note n
            left join kpi_catalog.report r
              on r.report_id = n.report_id
            order by n.created_at desc, n.note_id desc
            limit {render_limit(limit)}
        """
        rows = self._executor.query(sql)
        return [self._map(row) for row in rows]

    def list_recent_summary(self, limit: int = 100) -> list[dict]:
        sql = f"""
            select n.note_id, n.note_scope, n.note_type, n.note_title,
                   n.author_name, n.is_active, n.created_at,
                   n.kpi_slug, n.kpi_version, n.report_id, r.report_name
            from kpi_catalog.catalog_note n
            left join kpi_catalog.report r
              on r.report_id = n.report_id
            order by n.created_at desc, n.note_id desc
            limit {render_limit(limit)}
        """
        return self._executor.query(sql)

    def list_by_metric(self, kpi_slug: str, kpi_version: int) -> list[CatalogNote]:
        sql = """
            select n.note_id, n.note_scope, n.kpi_id, n.kpi_slug, n.kpi_version,
                   n.report_id, n.note_type, n.note_title, n.note_body,
                   n.author_name, n.author_email, n.is_active, n.created_at,
                   n.updated_at, r.report_name
            from kpi_catalog.catalog_note n
            left join kpi_catalog.report r
              on r.report_id = n.report_id
            where n.note_scope = 'metric_definition'
              and n.kpi_slug = :kpi_slug
              and n.kpi_version = cast(:kpi_version as integer)
              and n.is_active = true
            order by n.created_at desc, n.note_id desc
        """
        rows = self._executor.query(sql, {"kpi_slug": kpi_slug, "kpi_version": kpi_version})
        return [self._map(row) for row in rows]

    def list_by_report_ids(self, report_ids: list[int]) -> list[CatalogNote]:
        if not report_ids:
            return []
        placeholders = []
        params: dict[str, object] = {}
        for idx, report_id in enumerate(sorted(set(report_ids))):
            key = f"report_id_{idx}"
            placeholders.append(f"cast(:{key} as bigint)")
            params[key] = report_id
        sql = f"""
            select n.note_id, n.note_scope, n.kpi_id, n.kpi_slug, n.kpi_version,
                   n.report_id, n.note_type, n.note_title, n.note_body,
                   n.author_name, n.author_email, n.is_active, n.created_at,
                   n.updated_at, r.report_name
            from kpi_catalog.catalog_note n
            left join kpi_catalog.report r
              on r.report_id = n.report_id
            where n.note_scope = 'report'
              and n.report_id in ({", ".join(placeholders)})
              and n.is_active = true
            order by n.created_at desc, n.note_id desc
        """
        rows = self._executor.query(sql, params)
        return [self._map(row) for row in rows]

    def insert(self, note: CatalogNote) -> None:
        sql = """
            insert into kpi_catalog.catalog_note (
                note_scope, kpi_id, kpi_slug, kpi_version, report_id,
                note_type, note_title, note_body, author_name, author_email, is_active
            )
            values (
                :note_scope,
                nullif(:kpi_id, '__APP_NULL_SENTINEL__'),
                nullif(:kpi_slug, '__APP_NULL_SENTINEL__'),
                cast(nullif(:kpi_version, '__APP_NULL_SENTINEL__') as integer),
                cast(nullif(:report_id, '__APP_NULL_SENTINEL__') as bigint),
                :note_type,
                nullif(:note_title, '__APP_NULL_SENTINEL__'),
                :note_body,
                :author_name,
                nullif(:author_email, '__APP_NULL_SENTINEL__'),
                cast(:is_active as boolean)
            )
        """
        self._executor.execute(
            sql,
            {
                "note_scope": note.note_scope,
                "kpi_id": note.kpi_id,
                "kpi_slug": note.kpi_slug,
                "kpi_version": note.kpi_version,
                "report_id": note.report_id,
                "note_type": note.note_type,
                "note_title": note.note_title,
                "note_body": note.note_body,
                "author_name": note.author_name,
                "author_email": note.author_email,
                "is_active": note.is_active,
            },
        )

    @staticmethod
    def _map(row: dict) -> CatalogNote:
        return CatalogNote(
            note_id=int(row["note_id"]),
            note_scope=row["note_scope"],
            kpi_id=row.get("kpi_id"),
            kpi_slug=row.get("kpi_slug"),
            kpi_version=int(row["kpi_version"]) if row.get("kpi_version") is not None else None,
            report_id=int(row["report_id"]) if row.get("report_id") is not None else None,
            note_type=row["note_type"],
            note_title=row.get("note_title"),
            note_body=row["note_body"],
            author_name=row["author_name"],
            author_email=row.get("author_email"),
            is_active=bool(row.get("is_active")),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
            report_name=row.get("report_name"),
        )
