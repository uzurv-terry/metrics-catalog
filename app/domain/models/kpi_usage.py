from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class KpiUsage:
    kpi_id: str
    kpi_slug: str
    kpi_version: int
    usage_type: str
    consumer_tool: str
    reference_name: str
    usage_id: Optional[int] = None
    reference_url: Optional[str] = None
    source_system: Optional[str] = None
    context_notes: Optional[str] = None
    default_chart_type: Optional[str] = None
    approved_visualizations: Optional[str] = None
    preferred_dimensions: Optional[str] = None
    preferred_filters_json: Optional[str] = None
    row_level_security_notes: Optional[str] = None
    created_at: Optional[datetime] = None
