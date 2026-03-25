from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Report:
    report_name: str
    report_type: str
    consumer_tool: str
    report_id: Optional[int] = None
    report_slug: Optional[str] = None
    report_url: Optional[str] = None
    source_system: Optional[str] = None
    owner_person: Optional[str] = None
    owner_team: Optional[str] = None
    status: str = "active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
