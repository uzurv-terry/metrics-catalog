def render_limit(value: int, *, name: str = "limit", minimum: int = 1, maximum: int = 1000) -> str:
    """Return a validated integer literal for LIMIT clauses.

    Redshift/Data API parameter binding is unreliable inside LIMIT, so these
    values are validated in Python and rendered directly into the SQL string.
    """

    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc

    if parsed < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    if parsed > maximum:
        parsed = maximum
    return str(parsed)
