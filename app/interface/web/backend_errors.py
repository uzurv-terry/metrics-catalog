from botocore.exceptions import BotoCoreError, ClientError
from flask import current_app, flash, jsonify


def is_backend_error(exc: Exception) -> bool:
    return isinstance(exc, (BotoCoreError, ClientError))


def _client_error_code(exc: Exception) -> str | None:
    if not isinstance(exc, ClientError):
        return None
    return exc.response.get("Error", {}).get("Code")


def backend_error_message(action: str, exc: Exception) -> str:
    error_code = _client_error_code(exc)
    if error_code == "ExpiredTokenException":
        return (
            f"{action} failed because the AWS session token is expired. "
            "Refresh the AWS credentials for the configured profile and try again."
        )
    if error_code in {"InvalidClientTokenId", "UnrecognizedClientException"}:
        return (
            f"{action} failed because the AWS credentials were rejected. "
            "Check the configured AWS profile and try again."
        )
    return (
        f"{action} failed because the app could not reach the Redshift Data API. "
        "Check your AWS network or VPN connection and try again."
    )


def flash_backend_error(action: str, exc: Exception) -> None:
    current_app.logger.exception("Backend failure during %s", action, exc_info=exc)
    flash(backend_error_message(action, exc), "error")


def jsonify_backend_error(action: str, exc: Exception):
    current_app.logger.exception("Backend failure during %s", action, exc_info=exc)
    status_code = 401 if _client_error_code(exc) == "ExpiredTokenException" else 503
    return jsonify({"error": backend_error_message(action, exc)}), status_code
