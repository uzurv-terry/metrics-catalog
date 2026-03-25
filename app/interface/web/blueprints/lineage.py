from dataclasses import asdict

from flask import Blueprint, current_app, jsonify, redirect, request, url_for

from app.domain.exceptions import ValidationError

bp = Blueprint("lineage", __name__, url_prefix="/lineage")


@bp.get("/")
def index():
    return redirect(url_for("kpi_definitions.metric_overview"))


@bp.get("/api/kpi/<kpi_slug>/<int:kpi_version>")
def kpi_lineage(kpi_slug: str, kpi_version: int):
    service = current_app.extensions["services"]["lineage"]
    try:
        graph = service.get_kpi_lineage(kpi_slug, kpi_version)
        return jsonify(asdict(graph))
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400


@bp.get("/api/report")
def report_lineage():
    service = current_app.extensions["services"]["lineage"]
    report_id_raw = request.args.get("report_id", "").strip()
    try:
        if not report_id_raw:
            raise ValidationError("report_id is required")
        graph = service.get_report_lineage(int(report_id_raw))
        return jsonify(asdict(graph))
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400


@bp.get("/api/search/kpi")
def search_kpis():
    service = current_app.extensions["services"]["lineage"]
    return jsonify({"results": service.search_kpis(request.args.get("q", ""))})


@bp.get("/api/search/report")
def search_reports():
    service = current_app.extensions["services"]["lineage"]
    return jsonify({"results": service.search_reports(request.args.get("q", ""))})
