from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gcp_project_id: str = ""
    gcp_region: str = "us-central1"

    bq_dataset: str = "whaletrip"
    bq_location: str = "US"

    agents_url: str = "http://localhost:8001"

    api_secret_key: str = "dev-secret"
    allowed_origins: str = "http://localhost:3000"

    rate_limit_requests: int = 100
    rate_limit_window: int = 60

    maps_provider: str = "maplibre"

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    @property
    def bq_sightings_table(self) -> str:
        return f"{self.gcp_project_id}.{self.bq_dataset}.whale_sightings"

    @property
    def bq_heatmap_table(self) -> str:
        return f"{self.gcp_project_id}.{self.bq_dataset}.seasonal_heatmap"

    @property
    def bq_species_table(self) -> str:
        return f"{self.gcp_project_id}.{self.bq_dataset}.species_summary"


@lru_cache
def get_settings() -> Settings:
    return Settings()
