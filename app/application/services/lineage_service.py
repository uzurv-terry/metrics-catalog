import time
from typing import Callable

from app.application.dto.lineage_graph_dto import LineageEdgeDTO, LineageGraphDTO, LineageNodeDTO
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.exceptions import ValidationError


class LineageService:
    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        max_nodes: int = 60,
        max_edges: int = 120,
        search_limit: int = 20,
        cache_ttl_sec: int = 300,
    ):
        self._uow_factory = uow_factory
        self._max_nodes = max_nodes
        self._max_edges = max_edges
        self._search_limit = search_limit
        self._cache_ttl_sec = cache_ttl_sec
        self._cache: dict[str, tuple[float, object]] = {}

    def get_kpi_lineage(self, kpi_slug: str, kpi_version: int) -> LineageGraphDTO:
        if not kpi_slug.strip():
            raise ValidationError("kpi_slug is required")
        if kpi_version < 1:
            raise ValidationError("kpi_version must be >= 1")

        cache_key = f"kpi:{kpi_slug.lower()}:{kpi_version}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        with self._uow_factory() as uow:
            rows = uow.lineage.get_kpi_lineage_rows(kpi_slug, kpi_version, self._max_edges)

        graph = self._build_kpi_graph(rows, kpi_slug, kpi_version)
        self._cache[cache_key] = (time.time(), graph)
        return graph

    def get_report_lineage(self, consumer_tool: str, reference_name: str) -> LineageGraphDTO:
        if not consumer_tool.strip():
            raise ValidationError("consumer_tool is required")
        if not reference_name.strip():
            raise ValidationError("reference_name is required")

        cache_key = f"report:{consumer_tool.lower()}:{reference_name.lower()}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        with self._uow_factory() as uow:
            rows = uow.lineage.get_report_lineage_rows(consumer_tool, reference_name, self._max_edges)

        graph = self._build_report_graph(rows, consumer_tool, reference_name)
        self._cache[cache_key] = (time.time(), graph)
        return graph

    def search_kpis(self, query: str) -> list[dict]:
        query = query.strip()
        if len(query) < 2:
            return []
        cache_key = f"search:kpi:{query.lower()}:{self._search_limit}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]
        with self._uow_factory() as uow:
            rows = uow.lineage.search_kpis(query, self._search_limit)
        self._cache[cache_key] = (time.time(), rows)
        return rows

    def search_reports(self, query: str) -> list[dict]:
        query = query.strip()
        if len(query) < 2:
            return []
        cache_key = f"search:report:{query.lower()}:{self._search_limit}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]
        with self._uow_factory() as uow:
            rows = uow.lineage.search_reports(query, self._search_limit)
        self._cache[cache_key] = (time.time(), rows)
        return rows

    def _get_cached(self, key: str) -> LineageGraphDTO | None:
        payload = self._cache.get(key)
        if payload is None:
            return None
        created_at, value = payload
        if time.time() - created_at > self._cache_ttl_sec:
            self._cache.pop(key, None)
            return None
        return value  # type: ignore[return-value]

    def _build_kpi_graph(self, rows: list[dict], kpi_slug: str, kpi_version: int) -> LineageGraphDTO:
        if not rows:
            return LineageGraphDTO(
                nodes=[],
                edges=[],
                meta={
                    "focus_type": "kpi",
                    "focus_key": f"{kpi_slug}:{kpi_version}",
                    "node_count": 0,
                    "edge_count": 0,
                    "truncated": False,
                },
            )

        nodes: dict[str, LineageNodeDTO] = {}
        edges: list[LineageEdgeDTO] = []

        first = rows[0]
        kpi_node_id = f"kpi:{first['kpi_slug']}:v{first['kpi_version']}"
        nodes[kpi_node_id] = LineageNodeDTO(
            id=kpi_node_id,
            type="kpi",
            label=first["kpi_name"],
            data={
                "kpi_id": first["kpi_id"],
                "kpi_slug": first["kpi_slug"],
                "kpi_version": int(first["kpi_version"]),
                "status": first["status"],
                "certification_level": first["certification_level"],
                "documentation_location": first.get("metric_query_reference"),
            },
        )

        for row in rows:
            if row.get("usage_id") is None or row.get("consumer_tool") is None or row.get("reference_name") is None:
                continue
            report_node_id = f"asset:{row['consumer_tool']}:{row['reference_name'].strip().lower()}"
            if report_node_id not in nodes and len(nodes) < self._max_nodes:
                nodes[report_node_id] = LineageNodeDTO(
                    id=report_node_id,
                    type="report",
                    label=row["reference_name"],
                    data={
                        "consumer_tool": row["consumer_tool"],
                        "reference_name": row["reference_name"],
                        "reference_url": row.get("reference_url"),
                        "usage_type": row["usage_type"],
                    },
                )
            if report_node_id in nodes and len(edges) < self._max_edges:
                edges.append(
                    LineageEdgeDTO(
                        id=f"usage:{row['usage_id']}",
                        source=kpi_node_id,
                        target=report_node_id,
                        data={
                            "usage_id": int(row["usage_id"]),
                            "usage_type": row["usage_type"],
                            "consumer_tool": row["consumer_tool"],
                            "reference_url": row.get("reference_url"),
                        },
                    )
                )

        return LineageGraphDTO(
            nodes=list(nodes.values()),
            edges=edges,
            meta={
                "focus_type": "kpi",
                "focus_key": f"{kpi_slug}:{kpi_version}",
                "node_count": len(nodes),
                "edge_count": len(edges),
                "truncated": len(rows) >= self._max_edges or len(nodes) >= self._max_nodes,
            },
        )

    def _build_report_graph(
        self, rows: list[dict], consumer_tool: str, reference_name: str
    ) -> LineageGraphDTO:
        if not rows:
            return LineageGraphDTO(
                nodes=[],
                edges=[],
                meta={
                    "focus_type": "report",
                    "focus_key": f"{consumer_tool}:{reference_name}",
                    "node_count": 0,
                    "edge_count": 0,
                    "truncated": False,
                },
            )

        nodes: dict[str, LineageNodeDTO] = {}
        edges: list[LineageEdgeDTO] = []

        first = rows[0]
        report_node_id = f"asset:{first['consumer_tool']}:{first['reference_name'].strip().lower()}"
        nodes[report_node_id] = LineageNodeDTO(
            id=report_node_id,
            type="report",
            label=first["reference_name"],
            data={
                "consumer_tool": first["consumer_tool"],
                "reference_name": first["reference_name"],
                "reference_url": first.get("reference_url"),
                "usage_type": first["usage_type"],
            },
        )

        for row in rows:
            kpi_node_id = f"kpi:{row['kpi_slug']}:v{row['kpi_version']}"
            if kpi_node_id not in nodes and len(nodes) < self._max_nodes:
                nodes[kpi_node_id] = LineageNodeDTO(
                    id=kpi_node_id,
                    type="kpi",
                    label=row["kpi_name"],
                    data={
                        "kpi_id": row["kpi_id"],
                        "kpi_slug": row["kpi_slug"],
                        "kpi_version": int(row["kpi_version"]),
                        "status": row["status"],
                        "certification_level": row["certification_level"],
                        "documentation_location": row.get("metric_query_reference"),
                    },
                )
            if kpi_node_id in nodes and len(edges) < self._max_edges:
                edges.append(
                    LineageEdgeDTO(
                        id=f"usage:{row['usage_id']}",
                        source=kpi_node_id,
                        target=report_node_id,
                        data={
                            "usage_id": int(row["usage_id"]),
                            "usage_type": row["usage_type"],
                            "consumer_tool": row["consumer_tool"],
                            "reference_url": row.get("reference_url"),
                        },
                    )
                )

        return LineageGraphDTO(
            nodes=list(nodes.values()),
            edges=edges,
            meta={
                "focus_type": "report",
                "focus_key": f"{consumer_tool}:{reference_name}",
                "node_count": len(nodes),
                "edge_count": len(edges),
                "truncated": len(rows) >= self._max_edges or len(nodes) >= self._max_nodes,
            },
        )
