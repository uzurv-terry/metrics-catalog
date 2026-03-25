from flask_wtf import FlaskForm
from wtforms import HiddenField, IntegerField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Optional


class KpiUsageForm(FlaskForm):
    kpi_id = StringField("Metric ID (Required)", validators=[DataRequired()])
    kpi_slug = StringField("Metric Slug (Required)", validators=[DataRequired()])
    kpi_version = IntegerField("Metric Version (Required)", validators=[DataRequired(), NumberRange(min=1)])
    kpi_lookup = StringField("Find Metric by ID or Slug", validators=[Optional()])
    report_id = HiddenField("Report ID", validators=[DataRequired()])
    usage_type = SelectField(
        "How This Metric Is Used in the Report (Required)",
        choices=[("card", "card"), ("chart", "chart"), ("table", "table"), ("filter", "filter"), ("export", "export"), ("api_output", "api output")],
        validators=[DataRequired()],
    )
    default_chart_type = StringField("Default Chart Type", validators=[Optional()])
    approved_visualizations = TextAreaField("Approved Visualizations", validators=[Optional()])
    preferred_dimensions = TextAreaField("Preferred Dimensions", validators=[Optional()])
    preferred_filters_json = TextAreaField("Preferred Filters JSON", validators=[Optional()])
    row_level_security_notes = TextAreaField("Row-level Security Notes", validators=[Optional()])

    submit = SubmitField("Save Metric Usage")
