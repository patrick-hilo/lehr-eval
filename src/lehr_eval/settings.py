from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    database_path: Path = Path("data/lehr-eval.db")
    base_url: str = "http://localhost:8000"
    admin_password: str = ""


def load_settings() -> Settings:
    return Settings(
        database_path=Path(
            os.environ.get("LEHR_EVAL_DATABASE_PATH", "data/lehr-eval.db")
        ),
        base_url=os.environ.get("LEHR_EVAL_BASE_URL", "http://localhost:8000"),
        admin_password=os.environ.get(
            "LEHR_EVAL_ADMIN_PASSWORD",
            os.environ.get("LEHR_EVAL_ADMIN_PASSWORD_HASH", ""),
        ),
    )
