import time
import logging
from datetime import date, datetime
from typing import Any


class RedshiftDataApiExecutor:
    NULL_SENTINEL = "__APP_NULL_SENTINEL__"

    def __init__(
        self,
        client,
        cluster_id: str,
        database: str,
        secret_arn: str,
        poll_interval_sec: float = 0.5,
        max_wait_sec: int = 120,
        timing_log_enabled: bool = True,
        timing_warn_ms: int = 500,
    ):
        self._client = client
        self._cluster_id = cluster_id
        self._database = database
        self._secret_arn = secret_arn
        self._poll_interval_sec = poll_interval_sec
        self._max_wait_sec = max_wait_sec
        self._timing_log_enabled = timing_log_enabled
        self._timing_warn_ms = timing_warn_ms
        self._logger = logging.getLogger(__name__)

    def execute(self, sql: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        started_at = time.perf_counter()
        statement_id = self._submit(sql, params)
        status = self._wait(statement_id)
        self._log_timing("execute", sql, params, started_at, statement_id, status.get("ResultRows"))
        return status

    def query(self, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        started_at = time.perf_counter()
        statement_id = self._submit(sql, params)
        status = self._wait(statement_id)
        if status["Status"] != "FINISHED":
            self._log_timing("query", sql, params, started_at, statement_id, 0)
            return []

        rows: list[dict[str, Any]] = []
        next_token = None
        col_names = []

        while True:
            req = {"Id": statement_id}
            if next_token:
                req["NextToken"] = next_token
            result = self._client.get_statement_result(**req)

            if not col_names:
                col_names = [meta["name"] for meta in result.get("ColumnMetadata", [])]

            for record in result.get("Records", []):
                row = {}
                for i, field in enumerate(record):
                    key = col_names[i] if i < len(col_names) else f"col_{i}"
                    row[key] = self._field_value(field)
                rows.append(row)

            next_token = result.get("NextToken")
            if not next_token:
                break

        self._log_timing("query", sql, params, started_at, statement_id, len(rows))
        return rows

    def _submit(self, sql: str, params: dict[str, Any] | None = None) -> str:
        request = {
            "ClusterIdentifier": self._cluster_id,
            "Database": self._database,
            "SecretArn": self._secret_arn,
            "Sql": sql,
        }
        if params:
            request["Parameters"] = [
                {"name": k, "value": self._to_param_value(v)} for k, v in params.items()
            ]

        response = self._client.execute_statement(**request)
        return response["Id"]

    def _wait(self, statement_id: str) -> dict[str, Any]:
        deadline = time.time() + self._max_wait_sec
        while time.time() < deadline:
            status = self._client.describe_statement(Id=statement_id)
            state = status.get("Status")
            if state in {"FINISHED", "FAILED", "ABORTED"}:
                if state != "FINISHED":
                    err = status.get("Error", "Unknown Redshift Data API error")
                    raise RuntimeError(f"Statement failed ({state}): {err}")
                return status
            time.sleep(self._poll_interval_sec)

        raise TimeoutError(f"Timed out waiting for statement {statement_id}")

    def _log_timing(
        self,
        operation: str,
        sql: str,
        params: dict[str, Any] | None,
        started_at: float,
        statement_id: str,
        row_count: int | None,
    ) -> None:
        if not self._timing_log_enabled:
            return

        elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
        sql_summary = " ".join(sql.strip().split())
        if len(sql_summary) > 180:
            sql_summary = f"{sql_summary[:177]}..."

        log_method = self._logger.warning if elapsed_ms >= self._timing_warn_ms else self._logger.info
        log_method(
            "data_api_timing operation=%s elapsed_ms=%s statement_id=%s row_count=%s params=%s sql=\"%s\"",
            operation,
            elapsed_ms,
            statement_id,
            row_count if row_count is not None else "na",
            len(params or {}),
            sql_summary,
        )

    @staticmethod
    def _to_param_value(value: Any) -> str:
        if value is None:
            return RedshiftDataApiExecutor.NULL_SENTINEL
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        text = str(value)
        if text == "":
            return RedshiftDataApiExecutor.NULL_SENTINEL
        return text

    @staticmethod
    def _field_value(field: dict[str, Any]) -> Any:
        if field.get("isNull"):
            return None
        if "stringValue" in field:
            return field["stringValue"]
        if "longValue" in field:
            return field["longValue"]
        if "doubleValue" in field:
            return field["doubleValue"]
        if "booleanValue" in field:
            return field["booleanValue"]
        if "blobValue" in field:
            return field["blobValue"]
        return None
