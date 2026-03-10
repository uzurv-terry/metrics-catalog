from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from app.application.dto.kpi_definition_dto import KpiDefinitionDTO
from app.domain.exceptions import ConflictError, DomainError, ValidationError
from app.interface.web.forms.kpi_definition_form import KpiDefinitionForm

bp = Blueprint("kpi_definitions", __name__, url_prefix="/kpi-definitions")
DEFINITION_LIST_LIMIT = 50


def _dto_from_form(form: KpiDefinitionForm, kpi_version: int) -> KpiDefinitionDTO:
    return KpiDefinitionDTO(
        kpi_name=form.kpi_name.data,
        kpi_version=kpi_version,
        business_definition=form.business_definition.data,
        owner_person=form.owner_person.data,
        owner_team=form.owner_team.data,
        status=form.status.data,
        certification_level=form.certification_level.data,
        formula=form.formula.data,
        business_question=form.business_question.data,
        effective_start_date=form.effective_start_date.data,
        effective_end_date=form.effective_end_date.data,
        change_reason=form.change_reason.data,
        breaking_change_flag=form.breaking_change_flag.data,
        metric_query_reference=form.metric_query_reference.data,
        source_objects_json=form.source_objects_json.data,
        filter_conditions_json=form.filter_conditions_json.data,
        approval_1_by=form.approval_1_by.data,
        approval_2_by=form.approval_2_by.data,
    )


def _edit_context_from_request() -> tuple[str | None, int | None]:
    slug = (request.form.get("current_kpi_slug") or request.args.get("edit_slug") or "").strip() or None
    version_raw = (request.form.get("current_kpi_version") or request.args.get("edit_version") or "").strip()
    if not version_raw:
        return slug, None
    try:
        return slug, int(version_raw)
    except ValueError:
        return slug, None


@bp.route("/", methods=["GET", "POST"])
def list_definitions():
    service = current_app.extensions["services"]["kpi_definition"]
    edit_slug, edit_version = _edit_context_from_request()
    edit_definition = None

    if request.method == "GET" and edit_slug and edit_version is not None:
        edit_definition = service.get_by_key(edit_slug, edit_version)
        if edit_definition is None:
            flash("Metric definition not found", "error")
            return redirect(url_for("kpi_definitions.list_definitions"))
        form = KpiDefinitionForm(obj=edit_definition)
        form.current_kpi_slug.data = edit_definition.kpi_slug
        form.current_kpi_version.data = str(edit_definition.kpi_version)
    else:
        form = KpiDefinitionForm()

    if form.validate_on_submit():
        current_kpi_slug = (form.current_kpi_slug.data or "").strip()
        current_kpi_version_raw = (form.current_kpi_version.data or "").strip()
        is_update = bool(current_kpi_slug and current_kpi_version_raw)
        kpi_version = int(current_kpi_version_raw) if is_update else 1
        dto = _dto_from_form(form, kpi_version=kpi_version)
        try:
            if is_update:
                service.update(current_kpi_slug, kpi_version, dto)
                flash("Metric definition updated", "success")
            else:
                service.create(dto)
                flash("Metric definition created", "success")
            return redirect(url_for("kpi_definitions.list_definitions"))
        except (ValidationError, ConflictError) as exc:
            flash(str(exc), "error")
        except DomainError as exc:
            flash(f"Domain error: {exc}", "error")

    definitions = service.list_recent_summary(limit=DEFINITION_LIST_LIMIT)
    return render_template(
        "kpi_definition_list.html",
        definitions=definitions,
        form=form,
        is_edit=bool(form.current_kpi_slug.data and form.current_kpi_version.data),
    )


@bp.get("/overview")
def metric_overview():
    definition_service = current_app.extensions["services"]["kpi_definition"]
    usage_service = current_app.extensions["services"]["kpi_usage"]
    kpi_slug = (request.args.get("kpi_slug") or "").strip()
    kpi_version_raw = (request.args.get("kpi_version") or "").strip()

    definition = None
    usage_rows = []
    selected_metric = None

    if kpi_slug or kpi_version_raw:
        try:
            kpi_version = int(kpi_version_raw)
        except ValueError:
            flash("Metric version must be a valid number", "error")
            return redirect(url_for("kpi_definitions.metric_overview"))

        definition = definition_service.get_by_key(kpi_slug, kpi_version)
        if definition is None:
            flash("Metric definition not found", "error")
            return redirect(url_for("kpi_definitions.metric_overview"))

        usage_rows = usage_service.list_by_metric(kpi_slug, kpi_version)
        selected_metric = {"kpi_slug": kpi_slug, "kpi_version": kpi_version}

    return render_template(
        "metric_overview.html",
        definition=definition,
        usage_rows=usage_rows,
        selected_metric=selected_metric,
    )


@bp.route("/new", methods=["GET", "POST"])
def create_definition():
    return redirect(url_for("kpi_definitions.list_definitions"))


@bp.route("/<kpi_slug>/<int:kpi_version>/edit", methods=["GET", "POST"])
def edit_definition(kpi_slug: str, kpi_version: int):
    return redirect(
        url_for("kpi_definitions.list_definitions", edit_slug=kpi_slug, edit_version=kpi_version)
    )


@bp.get("/<kpi_slug>/<int:kpi_version>")
def metric_overview_legacy(kpi_slug: str, kpi_version: int):
    return redirect(
        url_for("kpi_definitions.metric_overview", kpi_slug=kpi_slug, kpi_version=kpi_version)
    )
