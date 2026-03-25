from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Optional, URL


class ReportForm(FlaskForm):
    TOOL_CHOICES = [
        ("tableau", "tableau"),
        ("powerbi", "Power BI"),
        ("looker", "Looker"),
        ("internal_app", "internal app"),
        ("crm", "CRM"),
        ("ad_hoc", "ad hoc"),
        ("other", "other"),
    ]

    report_name = StringField("Report Name (Required)", validators=[DataRequired()])
    report_type = SelectField(
        "Report Type (Required)",
        choices=[
            ("dashboard", "dashboard"),
            ("report", "report"),
            ("workbook", "workbook"),
            ("app_page", "app page"),
        ],
        validators=[DataRequired()],
    )
    consumer_tool = SelectField("Consumer Tool (Required)", choices=TOOL_CHOICES, validators=[DataRequired()])
    report_url = StringField("Report URL", validators=[Optional(), URL(require_tld=False)])
    source_system = StringField("Source System", validators=[Optional()])
    owner_person = StringField("Owner Person", validators=[Optional()])
    owner_team = StringField("Owner Team", validators=[Optional()])
    status = SelectField(
        "Status (Required)",
        choices=[("active", "active"), ("inactive", "inactive"), ("draft", "draft")],
        validators=[DataRequired()],
    )

    submit = SubmitField("Save Report")
