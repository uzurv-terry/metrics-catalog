from dataclasses import dataclass
from typing import Optional


@dataclass
class CatalogNoteDTO:
    note_scope: str
    note_body: str
    author_name: str
    kpi_id: Optional[str] = None
    kpi_slug: Optional[str] = None
    kpi_version: Optional[int] = None
    report_id: Optional[int] = None
    note_type: str = "general"
    note_title: Optional[str] = None
    author_email: Optional[str] = None
    is_active: bool = True
