import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from app import create_app

# Preserve explicitly provided runtime PORT (e.g., `PORT=5001 python3 run.py`)
preexisting_port = os.environ.get("PORT")
if load_dotenv is not None:
    load_dotenv(Path(__file__).resolve().parent / ".env", override=True)
if preexisting_port is not None:
    os.environ["PORT"] = preexisting_port

app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=app.config.get("DEBUG", False))
