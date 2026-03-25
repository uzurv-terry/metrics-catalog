from flask_wtf import FlaskForm
from wtforms import BooleanField, HiddenField, IntegerField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Optional


class CatalogNoteForm(FlaskForm):
    note_scope = SelectField(
        "Note Scope (Required)",
        choices=[("metric_definition", "metric definition"), ("report", "report")],
        validators=[DataRequired()],
    )
    kpi_id = HiddenField(validators=[Optional()])
    kpi_slug = HiddenField(validators=[Optional()])
    kpi_version = IntegerField(validators=[Optional(), NumberRange(min=1)])
    report_id = HiddenField(validators=[Optional()])
    note_type = SelectField(
        "Note Type (Required)",
        choices=[
            ("general", "general"),
            ("warning", "warning"),
            ("migration", "migration"),
            ("governance", "governance"),
            ("caveat", "caveat"),
        ],
        validators=[DataRequired()],
    )
    note_title = StringField("Note Title", validators=[Optional()])
    note_body = TextAreaField("Note Body (Required)", validators=[DataRequired()])
    author_name = StringField("Author Name (Required)", validators=[DataRequired()])
    author_email = StringField("Author Email", validators=[Optional()])
    is_active = BooleanField("Active", default=True)

    submit = SubmitField("Save Note")
