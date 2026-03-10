from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class KpiApprover:
    kpi_id: str
    kpi_slug: str
    kpi_version: int
    approver_name: str
    approver_role: str
    approver_id: Optional[int] = None
    approver_email: Optional[str] = None
    approval_notes: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
