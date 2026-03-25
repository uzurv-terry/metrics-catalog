from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class KpiUsage:
    kpi_id: str
    kpi_slug: str
    kpi_version: int
    report_id: int
    usage_type: str
    usage_id: Optional[int] = None
    default_chart_type: Optional[str] = None
    approved_visualizations: Optional[str] = None
    preferred_dimensions: Optional[str] = None
    preferred_filters_json: Optional[str] = None
    row_level_security_notes: Optional[str] = None
    report_name: Optional[str] = None
    report_slug: Optional[str] = None
    report_type: Optional[str] = None
    consumer_tool: Optional[str] = None
    report_url: Optional[str] = None
    source_system: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
