from dataclasses import dataclass
from typing import Optional


@dataclass
class KpiUsageDTO:
    kpi_id: str
    kpi_slug: str
    kpi_version: int
    report_id: int
    usage_type: str
    default_chart_type: Optional[str] = None
    approved_visualizations: Optional[str] = None
    preferred_dimensions: Optional[str] = None
    preferred_filters_json: Optional[str] = None
    row_level_security_notes: Optional[str] = None
