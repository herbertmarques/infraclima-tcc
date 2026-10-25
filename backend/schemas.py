from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    dataset_id: int
    eps: float = Field(gt=0, le=10)
    min_pts: int = Field(ge=2, le=800)
    radius_km: float = Field(gt=0, le=100)
    features: list[str] = Field(min_length=1)


class DatasetMetadata(BaseModel):
    source: str = ""
    period: str = ""
    license: str = ""
    variable_type: str = "other"
    resolution: str = ""
