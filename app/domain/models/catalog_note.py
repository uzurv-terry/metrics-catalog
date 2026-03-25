from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class CatalogNote:
    note_scope: str
    note_body: str
    author_name: str
    note_id: Optional[int] = None
    kpi_id: Optional[str] = None
    kpi_slug: Optional[str] = None
    kpi_version: Optional[int] = None
    report_id: Optional[int] = None
    note_type: str = "general"
    note_title: Optional[str] = None
    author_email: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    report_name: Optional[str] = None
