from dataclasses import dataclass
from typing import Optional


@dataclass
class ReportDTO:
    report_name: str
    report_type: str
    consumer_tool: str
    report_url: Optional[str] = None
    source_system: Optional[str] = None
    owner_person: Optional[str] = None
    owner_team: Optional[str] = None
    status: str = "active"
