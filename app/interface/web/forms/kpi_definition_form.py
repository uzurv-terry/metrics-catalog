from flask_wtf import FlaskForm
from wtforms import BooleanField, HiddenField, IntegerField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Optional


class KpiDefinitionForm(FlaskForm):
    current_kpi_slug = HiddenField()
    current_kpi_version = HiddenField()
    kpi_name = StringField("Metric Name (Required)", validators=[DataRequired()])
    kpi_version = IntegerField("Metric Version", default=1, validators=[Optional(), NumberRange(min=1)])
    business_definition = TextAreaField("Business Definition (Required)", validators=[DataRequired()])
    owner_person = StringField("Owner Person (Required)", validators=[DataRequired()])
    owner_team = StringField("Owner Team (Required)", validators=[DataRequired()])
    status = SelectField(
        "Status (Required)",
        choices=[("draft", "draft"), ("active", "active"), ("deprecated", "deprecated"), ("retired", "retired")],
        validators=[DataRequired()],
    )
    certification_level = SelectField(
        "Certification (Required)",
        choices=[("experimental", "experimental"), ("certified", "certified"), ("local_only", "local_only")],
        validators=[DataRequired()],
    )
    formula = TextAreaField("Formula (Required)", validators=[DataRequired()])
    business_question = TextAreaField("Business Question", validators=[Optional()])
    effective_start_date = StringField(
        "Effective Start Date",
        validators=[Optional()],
        render_kw={"type": "date"},
    )
    effective_end_date = StringField(
        "Effective End Date",
        validators=[Optional()],
        render_kw={"type": "date"},
    )
    change_reason = TextAreaField("Change Reason", validators=[Optional()])
    breaking_change_flag = BooleanField("Breaking Change")
    metric_query_reference = StringField("Doc Location (Jira/Confluence)", validators=[Optional()])
    source_objects_json = TextAreaField("Source Objects JSON", validators=[Optional()])
    filter_conditions_json = TextAreaField("Filter Conditions JSON", validators=[Optional()])
    approval_1_by = StringField("Approval 1 (Approver Name)", validators=[Optional()])
    approval_2_by = StringField("Approval 2 (Approver Name)", validators=[Optional()])

    submit = SubmitField("Save Metric Definition")
