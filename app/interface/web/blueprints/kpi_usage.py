from flask import Blueprint, current_app, flash, redirect, render_template, url_for

from app.application.dto.kpi_usage_dto import KpiUsageDTO
from app.domain.exceptions import DomainError, ValidationError
from app.interface.web.forms.kpi_usage_form import KpiUsageForm

bp = Blueprint("kpi_usage", __name__, url_prefix="/kpi-usage")
USAGE_LIST_LIMIT = 100


def _dto_from_form(form: KpiUsageForm) -> KpiUsageDTO:
    report_id = (form.report_id.data or "").strip()
    return KpiUsageDTO(
        kpi_id=form.kpi_id.data,
        kpi_slug=form.kpi_slug.data,
        kpi_version=form.kpi_version.data,
        report_id=int(report_id),
        usage_type=form.usage_type.data,
        default_chart_type=form.default_chart_type.data,
        approved_visualizations=form.approved_visualizations.data,
        preferred_dimensions=form.preferred_dimensions.data,
        preferred_filters_json=form.preferred_filters_json.data,
        row_level_security_notes=form.row_level_security_notes.data,
    )


@bp.route("/", methods=["GET", "POST"])
def list_usage():
    service = current_app.extensions["services"]["kpi_usage"]
    form = KpiUsageForm()

    if form.validate_on_submit():
        try:
            service.create(_dto_from_form(form))
            flash("Metric usage created", "success")
            return redirect(url_for("kpi_usage.list_usage"))
        except ValidationError as exc:
            flash(str(exc), "error")
        except DomainError as exc:
            flash(f"Domain error: {exc}", "error")

    usage_rows = service.list_recent_summary(limit=USAGE_LIST_LIMIT)
    return render_template("kpi_usage_list.html", usage_rows=usage_rows, form=form)


@bp.route("/new", methods=["GET", "POST"])
def create_usage():
    return redirect(url_for("kpi_usage.list_usage"))


@bp.route("/<int:usage_id>/edit", methods=["GET", "POST"])
def edit_usage(usage_id: int):
    service = current_app.extensions["services"]["kpi_usage"]
    usage = service.get_by_usage_id(usage_id)
    if usage is None:
        flash("Usage row not found", "error")
        return redirect(url_for("kpi_usage.list_usage"))

    form = KpiUsageForm(obj=usage)
    form.report_id.data = str(usage.report_id)
    if form.validate_on_submit():
        dto = _dto_from_form(form)
        try:
            service.update(usage_id, dto)
            flash("Metric usage updated", "success")
            return redirect(url_for("kpi_usage.list_usage"))
        except ValidationError as exc:
            flash(str(exc), "error")
        except DomainError as exc:
            flash(f"Domain error: {exc}", "error")

    report_label = f"{usage.report_name} ({usage.consumer_tool})" if usage.report_name and usage.consumer_tool else ""
    return render_template("kpi_usage_form.html", form=form, is_edit=True, report_label=report_label)
