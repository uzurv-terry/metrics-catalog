from dataclasses import dataclass
from typing import Any


@dataclass
class LineageNodeDTO:
    id: str
    type: str
    label: str
    data: dict[str, Any]


@dataclass
class LineageEdgeDTO:
    id: str
    source: str
    target: str
    data: dict[str, Any]


@dataclass
class LineageGraphDTO:
    nodes: list[LineageNodeDTO]
    edges: list[LineageEdgeDTO]
    meta: dict[str, Any]

