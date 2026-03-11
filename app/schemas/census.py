from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class CensusBase(BaseModel):
    parish_id: str = Field(..., description="Unique ID for the parish")
    total_parishioners: int = Field(..., ge=0)
    baptisms: int = Field(..., ge=0)
    marriages: int = Field(..., ge=0)
    deaths: int = Field(..., ge=0)
    year: int = Field(..., ge=1900, le=2100)

class CensusCreate(CensusBase):
    pass

class CensusUpdate(BaseModel):
    total_parishioners: Optional[int] = Field(None, ge=0)
    baptisms: Optional[int] = Field(None, ge=0)
    marriages: Optional[int] = Field(None, ge=0)
    deaths: Optional[int] = Field(None, ge=0)
    year: Optional[int] = Field(None, ge=1900, le=2100)

class CensusResponse(CensusBase):
    id: int
    submitted_by_id: int
    version: int

    model_config = ConfigDict(from_attributes=True)
