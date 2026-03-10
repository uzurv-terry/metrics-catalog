from typing import Any

import boto3

from app.config import Settings
from app.infrastructure.redshift.data_api_executor import RedshiftDataApiExecutor


class RedshiftConnectionFactory:
    def __init__(self, settings: Settings):
        self._settings = settings

    def create(self) -> RedshiftDataApiExecutor:
        self._validate_required_settings()

        session_kwargs: dict[str, Any] = {}
        if self._settings.aws_profile:
            session_kwargs["profile_name"] = self._settings.aws_profile
        if self._settings.aws_default_region:
            session_kwargs["region_name"] = self._settings.aws_default_region

        session = boto3.session.Session(**session_kwargs)
        client = session.client("redshift-data")

        return RedshiftDataApiExecutor(
            client=client,
            cluster_id=self._settings.cluster_id,
            database=self._settings.database,
            secret_arn=self._settings.secret_arn,
            poll_interval_sec=self._settings.data_api_poll_interval_sec,
            max_wait_sec=self._settings.data_api_max_wait_sec,
            timing_log_enabled=self._settings.data_api_timing_log_enabled,
            timing_warn_ms=self._settings.data_api_timing_warn_ms,
        )

    def _validate_required_settings(self) -> None:
        missing = []
        if not self._settings.cluster_id:
            missing.append("CLUSTER_ID")
        if not self._settings.database:
            missing.append("DATABASE")
        if not self._settings.secret_arn:
            missing.append("SECRET_ARN")

        if missing:
            raise RuntimeError(
                "Missing required Data API settings: "
                + ", ".join(missing)
                + ". Set env vars for Redshift Data API connection."
            )
