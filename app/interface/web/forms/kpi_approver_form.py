from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Optional


class KpiApproverForm(FlaskForm):
    kpi_lookup = StringField("Find Metric by ID or Slug", validators=[Optional()])
    kpi_id = StringField("Metric ID (Required)", validators=[DataRequired()])
    kpi_slug = StringField("Metric Slug (Required)", validators=[DataRequired()])
    kpi_version = IntegerField("Metric Version (Required)", validators=[DataRequired(), NumberRange(min=1)])
    approver_name = StringField("Approver Name (Required)", validators=[DataRequired()])
    approver_email = StringField("Approver Email", validators=[Optional()])
    approver_role = SelectField(
        "Approver Role (Required)",
        choices=[
            ("business_owner", "business_owner"),
            ("data_governance", "data_governance"),
            ("finance", "finance"),
            ("operations", "operations"),
            ("other", "other"),
        ],
        validators=[DataRequired()],
    )
    approval_notes = TextAreaField("Approval Notes", validators=[Optional()])

    submit = SubmitField("Save Metric Approver")
