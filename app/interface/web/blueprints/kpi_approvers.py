from flask import Blueprint, current_app, flash, redirect, render_template, url_for

from app.application.dto.kpi_approver_dto import KpiApproverDTO
from app.domain.exceptions import ConflictError, DomainError, ValidationError
from app.interface.web.forms.kpi_approver_form import KpiApproverForm

bp = Blueprint("kpi_approvers", __name__, url_prefix="/kpi-approvers")
APPROVER_LIST_LIMIT = 200


def _dto_from_form(form: KpiApproverForm) -> KpiApproverDTO:
    return KpiApproverDTO(
        kpi_id=form.kpi_id.data,
        kpi_slug=form.kpi_slug.data,
        kpi_version=form.kpi_version.data,
        approver_name=form.approver_name.data,
        approver_email=form.approver_email.data,
        approver_role=form.approver_role.data,
        approval_notes=form.approval_notes.data,
    )


@bp.route("/", methods=["GET", "POST"])
def list_approvers():
    service = current_app.extensions["services"]["kpi_approver"]
    form = KpiApproverForm()

    if form.validate_on_submit():
        dto = _dto_from_form(form)
        try:
            service.create(dto)
            flash("Metric approver added", "success")
            return redirect(url_for("kpi_approvers.list_approvers"))
        except (ValidationError, ConflictError) as exc:
            flash(str(exc), "error")
        except DomainError as exc:
            flash(f"Domain error: {exc}", "error")

    approvers = service.list_recent_summary(limit=APPROVER_LIST_LIMIT)
    return render_template(
        "kpi_approver_list.html",
        approvers=approvers,
        form=form,
    )


@bp.route("/new", methods=["GET", "POST"])
def create_approver():
    return redirect(url_for("kpi_approvers.list_approvers"))
