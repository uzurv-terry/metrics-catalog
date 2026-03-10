from pathlib import Path
import logging
import time

from flask import Flask, g, render_template, request

from app.application.services import KpiApproverService, KpiDefinitionService, KpiUsageService, LineageService
from app.config import Settings
from app.infrastructure.redshift.connection_factory import RedshiftConnectionFactory
from app.infrastructure.redshift.unit_of_work import RedshiftUnitOfWork
from app.interface.web.blueprints import kpi_approvers_bp, kpi_definitions_bp, kpi_usage_bp, lineage_bp


def create_app() -> Flask:
    root_dir = Path(__file__).resolve().parent
    template_dir = root_dir / "interface" / "web" / "templates"
    app = Flask(__name__, template_folder=str(template_dir))
    settings = Settings()
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
    app.config["SECRET_KEY"] = settings.flask_secret_key
    app.config["DEBUG"] = settings.flask_debug

    connection_factory = RedshiftConnectionFactory(settings)
    uow_factory = lambda: RedshiftUnitOfWork(connection_factory)

    app.extensions["services"] = {
        "kpi_definition": KpiDefinitionService(uow_factory),
        "kpi_usage": KpiUsageService(uow_factory),
        "kpi_approver": KpiApproverService(uow_factory),
        "lineage": LineageService(
            uow_factory,
            max_nodes=settings.lineage_max_nodes,
            max_edges=settings.lineage_max_edges,
            search_limit=settings.lineage_search_limit,
            cache_ttl_sec=settings.lineage_cache_ttl_sec,
        ),
    }

    app.register_blueprint(kpi_definitions_bp)
    app.register_blueprint(kpi_usage_bp)
    app.register_blueprint(kpi_approvers_bp)
    app.register_blueprint(lineage_bp)

    @app.before_request
    def start_request_timer():
        if settings.request_timing_log_enabled:
            g._request_started_at = time.perf_counter()

    @app.after_request
    def log_request_timing(response):
        if not settings.request_timing_log_enabled:
            return response

        started_at = getattr(g, "_request_started_at", None)
        if started_at is None:
            return response

        elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
        endpoint = request.endpoint or "unknown"
        route_type = "write" if request.method in {"POST", "PUT", "PATCH", "DELETE"} else "read"
        if endpoint.startswith("lineage."):
            route_group = "lineage"
        elif endpoint == "health":
            route_group = "health"
        else:
            route_group = "catalog"

        log_method = app.logger.warning if elapsed_ms >= settings.request_timing_warn_ms else app.logger.info
        log_method(
            "request_timing route_group=%s endpoint=%s method=%s status=%s elapsed_ms=%s route_type=%s path=%s",
            route_group,
            endpoint,
            request.method,
            response.status_code,
            elapsed_ms,
            route_type,
            request.path,
        )
        return response

    @app.get("/")
    def home():
        return render_template("home.html")

    @app.get("/health")
    def health():
        executor = connection_factory.create()
        rows = executor.query("select 1 as ok")
        if not rows:
            raise RuntimeError("Health check query returned no rows")
        return {"status": "ok"}

    return app
