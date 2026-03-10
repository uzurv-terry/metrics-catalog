import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv is not None:
    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env", override=False)


@dataclass
class Settings:
    cluster_id: str = os.environ.get("CLUSTER_ID", "")
    database: str = os.environ.get("DATABASE", "")
    secret_arn: str = os.environ.get("SECRET_ARN", "")
    aws_profile: str = os.environ.get("AWS_PROFILE", "")
    aws_default_region: str = os.environ.get("AWS_DEFAULT_REGION", "")
    log_level: str = os.environ.get("LOG_LEVEL", "INFO")
    data_api_poll_interval_sec: float = float(os.environ.get("DATA_API_POLL_INTERVAL_SEC", "0.2"))
    data_api_max_wait_sec: int = int(os.environ.get("DATA_API_MAX_WAIT_SEC", "120"))
    lineage_max_nodes: int = int(os.environ.get("LINEAGE_MAX_NODES", "60"))
    lineage_max_edges: int = int(os.environ.get("LINEAGE_MAX_EDGES", "120"))
    lineage_search_limit: int = int(os.environ.get("LINEAGE_SEARCH_LIMIT", "20"))
    lineage_cache_ttl_sec: int = int(os.environ.get("LINEAGE_CACHE_TTL_SEC", "300"))
    request_timing_log_enabled: bool = os.environ.get("REQUEST_TIMING_LOG_ENABLED", "true").lower() == "true"
    request_timing_warn_ms: int = int(os.environ.get("REQUEST_TIMING_WARN_MS", "800"))
    data_api_timing_log_enabled: bool = os.environ.get("DATA_API_TIMING_LOG_ENABLED", "true").lower() == "true"
    data_api_timing_warn_ms: int = int(os.environ.get("DATA_API_TIMING_WARN_MS", "500"))

    redshift_host: str = os.environ.get("REDSHIFT_HOST", "")
    redshift_port: int = int(os.environ.get("REDSHIFT_PORT", "5439"))
    redshift_db: str = os.environ.get("REDSHIFT_DB", os.environ.get("DATABASE", ""))
    redshift_user: str = os.environ.get("REDSHIFT_USER", "")
    redshift_password: str = os.environ.get("REDSHIFT_PASSWORD", "")
    redshift_sslmode: str = os.environ.get("REDSHIFT_SSLMODE", "verify-full")
    redshift_connect_timeout_sec: int = int(os.environ.get("REDSHIFT_CONNECT_TIMEOUT_SEC", "10"))
    redshift_statement_timeout_ms: int = int(os.environ.get("REDSHIFT_STATEMENT_TIMEOUT_MS", "900000"))
    flask_secret_key: str = os.environ.get("FLASK_SECRET_KEY", "dev")
    flask_debug: bool = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
