from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


class AppSettings(BaseSettings):
    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    timezone: str = Field(default="America/Bogota", alias="TIMEZONE")
    data_dir: str = Field(default="data", alias="DATA_DIR")
    raw_data_dir: str = Field(default="data/raw", alias="RAW_DATA_DIR")
    processed_data_dir: str = Field(default="data/processed", alias="PROCESSED_DATA_DIR")
    exports_dir: str = Field(default="data/exports", alias="EXPORTS_DIR")
    database_url: str = Field(default="sqlite:///data/processed/garmin_insights.db", alias="DATABASE_URL")
    garmin_username: str | None = Field(default=None, alias="GARMIN_USERNAME")
    garmin_password: str | None = Field(default=None, alias="GARMIN_PASSWORD")
    garmin_source: str = Field(default="mock", alias="GARMIN_SOURCE")
    garmin_import_dir: str = Field(default="data/imports", alias="GARMIN_IMPORT_DIR")
    garmin_cli_command: str = Field(default="garmin-connect", alias="GARMIN_CLI_COMMAND")
    garmin_node_command: str = Field(default="node", alias="GARMIN_NODE_COMMAND")
    save_raw_responses: bool = Field(default=True, alias="SAVE_RAW_RESPONSES")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    @property
    def root_dir(self) -> Path:
        return ROOT_DIR

    @property
    def data_path(self) -> Path:
        return self.root_dir / self.data_dir

    @property
    def raw_path(self) -> Path:
        return self.root_dir / self.raw_data_dir

    @property
    def processed_path(self) -> Path:
        return self.root_dir / self.processed_data_dir

    @property
    def exports_path(self) -> Path:
        return self.root_dir / self.exports_dir

    @property
    def imports_path(self) -> Path:
        return self.root_dir / self.garmin_import_dir


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()
