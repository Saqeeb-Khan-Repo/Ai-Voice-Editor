from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class ReciterProfileCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    vocal_type: str = Field("custom", max_length=50)
    settings: Dict[str, Any]

class ReciterProfileResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    is_builtin: bool = False
    vocal_type: str = "custom"
    settings: Dict[str, Any]
    created_at: Optional[str] = None

class ProfileListResponse(BaseModel):
    total: int
    profiles: List[ReciterProfileResponse]
