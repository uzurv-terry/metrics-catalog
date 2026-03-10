from dataclasses import dataclass
from typing import Optional


@dataclass
class KpiApproverDTO:
    kpi_id: str
    kpi_slug: str
    kpi_version: int
    approver_name: str
    approver_role: str
    approver_email: Optional[str] = None
    approval_notes: Optional[str] = None
