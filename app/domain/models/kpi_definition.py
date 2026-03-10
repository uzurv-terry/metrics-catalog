from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class KpiDefinition:
    kpi_id: str
    kpi_name: str
    kpi_slug: str
    kpi_version: int
    business_definition: str
    owner_person: str
    owner_team: str
    status: str
    certification_level: str
    formula: str
    business_question: Optional[str] = None
    effective_start_date: Optional[date] = None
    effective_end_date: Optional[date] = None
    change_reason: Optional[str] = None
    breaking_change_flag: bool = False
    metric_query_reference: Optional[str] = None
    source_objects_json: Optional[str] = None
    filter_conditions_json: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
