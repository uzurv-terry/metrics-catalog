from flask import Blueprint, current_app, flash, redirect, render_template, url_for

from app.application.dto.catalog_note_dto import CatalogNoteDTO
from app.domain.exceptions import DomainError, ValidationError
from app.interface.web.forms.catalog_note_form import CatalogNoteForm

bp = Blueprint("catalog_notes", __name__, url_prefix="/notes")
NOTE_LIST_LIMIT = 100


def _dto_from_form(form: CatalogNoteForm) -> CatalogNoteDTO:
    report_id = (form.report_id.data or "").strip()
    return CatalogNoteDTO(
        note_scope=form.note_scope.data,
        kpi_id=(form.kpi_id.data or "").strip() or None,
        kpi_slug=(form.kpi_slug.data or "").strip() or None,
        kpi_version=form.kpi_version.data or None,
        report_id=int(report_id) if report_id else None,
        note_type=form.note_type.data,
        note_title=form.note_title.data,
        note_body=form.note_body.data,
        author_name=form.author_name.data,
        author_email=form.author_email.data,
        is_active=bool(form.is_active.data),
    )


@bp.route("/", methods=["GET", "POST"])
def list_notes():
    service = current_app.extensions["services"]["catalog_note"]
    form = CatalogNoteForm()

    if form.validate_on_submit():
        try:
            service.create(_dto_from_form(form))
            flash("Note created", "success")
            return redirect(url_for("catalog_notes.list_notes"))
        except ValidationError as exc:
            flash(str(exc), "error")
        except DomainError as exc:
            flash(f"Domain error: {exc}", "error")

    notes = service.list_recent_summary(limit=NOTE_LIST_LIMIT)
    return render_template("catalog_note_list.html", notes=notes, form=form)
