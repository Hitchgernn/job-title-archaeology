from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class BrightDataConfig(BaseModel):
    base_url: HttpUrl = "https://api.brightdata.com"
    dataset_id: str = Field(min_length=1)


class CollectionSettings(BaseModel):
    output_dir: Path
    target_records: int = Field(ge=1, le=10000)
    poll_delay_seconds: int = Field(ge=1, le=120)
    max_poll_attempts: int = Field(ge=1, le=1000)
    keywords: list[str] = Field(min_length=1)
    locations: list[str] = Field(min_length=1)
    industries: list[str] = Field(min_length=1)


class CollectionConfig(BaseModel):
    brightdata: BrightDataConfig
    collection: CollectionSettings


class EnvSettings(BaseSettings):
    brightdata_api_token: str = Field(alias="BRIGHTDATA_API_TOKEN")
    brightdata_web_scraper_id: str | None = Field(default=None, alias="BRIGHTDATA_WEB_SCRAPER_ID")
    brightdata_web_scraper_id_indeed: str | None = Field(default=None, alias="BRIGHTDATA_WEB_SCRAPER_ID_INDEED")
    brightdata_web_scraper_id_linkedin: str | None = Field(default=None, alias="BRIGHTDATA_WEB_SCRAPER_ID_LINKEDIN")
    database_url: str | None = Field(default=None, alias="DATABASE_URL")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def dataset_id_for(self, source: str) -> str | None:
        match source:
            case "indeed":
                return self.brightdata_web_scraper_id_indeed
            case "linkedin":
                return self.brightdata_web_scraper_id_linkedin
            case _:
                return self.brightdata_web_scraper_id


def load_collection_config(path: Path) -> CollectionConfig:
    with path.open("r", encoding="utf-8") as config_file:
        data: Any = yaml.safe_load(config_file) or {}

    output_dir = Path(data["collection"]["output_dir"])
    if not output_dir.is_absolute():
        project_root = path.parent.parent.parent
        data["collection"]["output_dir"] = project_root / output_dir

    return CollectionConfig.model_validate(data)
