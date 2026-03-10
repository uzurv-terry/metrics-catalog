from dataclasses import dataclass
from typing import Optional


@dataclass
class KpiDefinitionDTO:
    kpi_name: str
    kpi_version: int
    business_definition: str
    owner_person: str
    owner_team: str
    status: str
    certification_level: str
    formula: str
    business_question: Optional[str] = None
    effective_start_date: Optional[str] = None
    effective_end_date: Optional[str] = None
    change_reason: Optional[str] = None
    breaking_change_flag: bool = False
    metric_query_reference: Optional[str] = None
    source_objects_json: Optional[str] = None
    filter_conditions_json: Optional[str] = None
    approval_1_by: Optional[str] = None
    approval_2_by: Optional[str] = None
