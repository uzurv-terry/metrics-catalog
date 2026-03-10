from flask import Blueprint, current_app, flash, redirect, render_template, url_for

from app.application.dto.kpi_usage_dto import KpiUsageDTO
from app.domain.exceptions import DomainError, ValidationError
from app.interface.web.forms.kpi_usage_form import KpiUsageForm

bp = Blueprint("kpi_usage", __name__, url_prefix="/kpi-usage")
USAGE_LIST_LIMIT = 100


def _dto_from_form(form: KpiUsageForm, selected_tool: str | None = None) -> KpiUsageDTO:
    return KpiUsageDTO(
        kpi_id=form.kpi_id.data,
        kpi_slug=form.kpi_slug.data,
        kpi_version=form.kpi_version.data,
        usage_type=form.usage_type.data,
        consumer_tool=selected_tool or form.consumer_tool.data,
        reference_name=form.reference_name.data,
        reference_url=form.reference_url.data,
        source_system=form.source_system.data,
        context_notes=form.context_notes.data,
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
        selected_tools = list(dict.fromkeys(form.consumer_tools.data or []))
        if not selected_tools:
            flash("Select at least one Consumer Tool.", "error")
            usage_rows = service.list_recent_summary(limit=USAGE_LIST_LIMIT)
            return render_template(
                "kpi_usage_list.html",
                usage_rows=usage_rows,
                form=form,
            )

        try:
            service.create_many([_dto_from_form(form, selected_tool=tool) for tool in selected_tools])
            flash(f"Metric usage created for {len(selected_tools)} consumer tool(s)", "success")
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
    if form.validate_on_submit():
        if not form.consumer_tool.data:
            flash("Consumer Tool is required for editing.", "error")
            return render_template("kpi_usage_form.html", form=form, is_edit=True)
        dto = _dto_from_form(form)
        try:
            service.update(usage_id, dto)
            flash("Metric usage updated", "success")
            return redirect(url_for("kpi_usage.list_usage"))
        except ValidationError as exc:
            flash(str(exc), "error")
        except DomainError as exc:
            flash(f"Domain error: {exc}", "error")

    return render_template("kpi_usage_form.html", form=form, is_edit=True)
