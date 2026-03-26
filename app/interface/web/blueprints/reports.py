from flask import Blueprint, current_app, flash, redirect, render_template, url_for

from app.application.dto.catalog_note_dto import CatalogNoteDTO
from app.application.dto.report_dto import ReportDTO
from app.domain.exceptions import ConflictError, DomainError, ValidationError
from app.interface.web.backend_errors import flash_backend_error, is_backend_error
from app.interface.web.forms.catalog_note_form import CatalogNoteForm
from app.interface.web.forms.report_form import ReportForm

bp = Blueprint("reports", __name__, url_prefix="/reports")
REPORT_LIST_LIMIT = 100


def _dto_from_form(form: ReportForm) -> ReportDTO:
    return ReportDTO(
        report_name=form.report_name.data,
        report_type=form.report_type.data,
        consumer_tool=form.consumer_tool.data,
        report_url=form.report_url.data,
        source_system=form.source_system.data,
        owner_person=form.owner_person.data,
        owner_team=form.owner_team.data,
        status=form.status.data,
    )


def _note_dto_from_form(report_id: int, form: CatalogNoteForm) -> CatalogNoteDTO:
    return CatalogNoteDTO(
        note_scope="report",
        report_id=report_id,
        note_type=form.note_type.data,
        note_title=form.note_title.data,
        note_body=form.note_body.data,
        author_name=form.author_name.data,
        author_email=form.author_email.data,
        is_active=bool(form.is_active.data),
    )


@bp.route("/", methods=["GET", "POST"])
def list_reports():
    service = current_app.extensions["services"]["report"]
    form = ReportForm()

    if form.validate_on_submit():
        try:
            service.create(_dto_from_form(form))
            flash("Report created", "success")
            return redirect(url_for("reports.list_reports"))
        except (ValidationError, ConflictError) as exc:
            flash(str(exc), "error")
        except DomainError as exc:
            flash(f"Domain error: {exc}", "error")
        except Exception as exc:
            if not is_backend_error(exc):
                raise
            flash_backend_error("Saving the report", exc)

    try:
        reports = service.list_recent_summary(limit=REPORT_LIST_LIMIT)
    except Exception as exc:
        if not is_backend_error(exc):
            raise
        flash_backend_error("Loading reports", exc)
        reports = []
    return render_template("report_list.html", reports=reports, form=form)


@bp.route("/new", methods=["GET", "POST"])
def create_report():
    return redirect(url_for("reports.list_reports"))


@bp.route("/<int:report_id>/edit", methods=["GET", "POST"])
def edit_report(report_id: int):
    report_service = current_app.extensions["services"]["report"]
    note_service = current_app.extensions["services"]["catalog_note"]
    try:
        report = report_service.get_by_report_id(report_id)
    except Exception as exc:
        if not is_backend_error(exc):
            raise
        flash_backend_error("Loading the report", exc)
        return redirect(url_for("reports.list_reports"))
    if report is None:
        flash("Report not found", "error")
        return redirect(url_for("reports.list_reports"))

    form = ReportForm(obj=report)
    note_form = CatalogNoteForm(prefix="note")
    note_form.note_scope.data = "report"
    note_form.report_id.data = str(report.report_id)
    try:
        report_notes = note_service.list_by_report_id(report.report_id)
    except Exception as exc:
        if not is_backend_error(exc):
            raise
        flash_backend_error("Loading report notes", exc)
        report_notes = []

    if form.validate_on_submit():
        try:
            report_service.update(report_id, _dto_from_form(form))
            flash("Report updated", "success")
            return redirect(url_for("reports.list_reports"))
        except (ValidationError, ConflictError) as exc:
            flash(str(exc), "error")
        except DomainError as exc:
            flash(f"Domain error: {exc}", "error")
        except Exception as exc:
            if not is_backend_error(exc):
                raise
            flash_backend_error("Updating the report", exc)

    return render_template(
        "report_form.html",
        form=form,
        is_edit=True,
        report=report,
        note_form=note_form,
        report_notes=report_notes,
    )


@bp.post("/<int:report_id>/notes")
def create_report_note(report_id: int):
    report_service = current_app.extensions["services"]["report"]
    note_service = current_app.extensions["services"]["catalog_note"]
    try:
        report = report_service.get_by_report_id(report_id)
    except Exception as exc:
        if not is_backend_error(exc):
            raise
        flash_backend_error("Loading the report", exc)
        return redirect(url_for("reports.list_reports"))
    if report is None:
        flash("Report not found", "error")
        return redirect(url_for("reports.list_reports"))

    note_form = CatalogNoteForm(prefix="note")
    if note_form.validate_on_submit():
        try:
            note_service.create(_note_dto_from_form(report_id, note_form))
            flash("Report note created", "success")
            return redirect(url_for("reports.edit_report", report_id=report_id))
        except ValidationError as exc:
            flash(str(exc), "error")
        except DomainError as exc:
            flash(f"Domain error: {exc}", "error")
        except Exception as exc:
            if not is_backend_error(exc):
                raise
            flash_backend_error("Saving the report note", exc)

    form = ReportForm(obj=report)
    note_form.note_scope.data = "report"
    note_form.report_id.data = str(report.report_id)
    try:
        report_notes = note_service.list_by_report_id(report.report_id)
    except Exception as exc:
        if not is_backend_error(exc):
            raise
        flash_backend_error("Loading report notes", exc)
        report_notes = []
    return render_template(
        "report_form.html",
        form=form,
        is_edit=True,
        report=report,
        note_form=note_form,
        report_notes=report_notes,
    )
