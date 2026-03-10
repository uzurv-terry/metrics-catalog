from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, SelectMultipleField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Optional
from wtforms.widgets import CheckboxInput, ListWidget


class KpiUsageForm(FlaskForm):
    TOOL_CHOICES = [
        ("tableau", "tableau"),
        ("crm", "CRM"),
        ("ad_hoc", "ad hoc"),
        ("internal_app_other", "internal app (other)"),
    ]

    kpi_id = StringField("Metric ID (Required)", validators=[DataRequired()])
    kpi_slug = StringField("Metric Slug (Required)", validators=[DataRequired()])
    kpi_version = IntegerField("Metric Version (Required)", validators=[DataRequired(), NumberRange(min=1)])
    kpi_lookup = StringField("Find Metric by ID or Slug", validators=[Optional()])
    usage_type = SelectField(
        "How This Metric Is Used (Required)",
        choices=[("dashboard", "dashboard"), ("report", "report"), ("extract", "extract"), ("api", "api"), ("notebook", "notebook")],
        validators=[DataRequired()],
    )
    consumer_tool = SelectField(
        "Tool Using This Metric (Required for edit)",
        choices=TOOL_CHOICES,
        validators=[Optional()],
    )
    consumer_tools = SelectMultipleField(
        "Tools Using This Metric (Required for create)",
        choices=TOOL_CHOICES,
        validators=[Optional()],
        option_widget=CheckboxInput(),
        widget=ListWidget(prefix_label=False),
    )
    reference_name = StringField("Dashboard or Report Name (Required)", validators=[DataRequired()])
    reference_url = StringField("Link to Dashboard or Report", validators=[Optional()])
    source_system = StringField("Platform or System Name", validators=[Optional()])
    context_notes = TextAreaField("Additional Notes", validators=[Optional()])
    default_chart_type = StringField("Default Chart Type", validators=[Optional()])
    approved_visualizations = TextAreaField("Approved Visualizations", validators=[Optional()])
    preferred_dimensions = TextAreaField("Preferred Dimensions", validators=[Optional()])
    preferred_filters_json = TextAreaField("Preferred Filters JSON", validators=[Optional()])
    row_level_security_notes = TextAreaField("Row-level Security Notes", validators=[Optional()])

    submit = SubmitField("Save Metric Usage")
