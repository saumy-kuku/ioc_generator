from pydantic import BaseModel, Field
from typing import List, Optional

class UserInput(BaseModel):
    episode_summary: str = Field(..., description="Raw episodic summary of the show")
    peak_moments: List[str] = Field(..., description="List of peak moments or cliffhangers")

class StructuredInput(BaseModel):
    primary_characters: List[str]
    core_conflict: str
    romance_intensity: int = Field(ge=0, le=5)
    betrayal_level: int = Field(ge=0, le=5)
    comedy_score: int = Field(ge=0, le=5)
    darkness_score: int = Field(ge=0, le=5)
    shock_moments: List[str]

class GenreDecision(BaseModel):
    selected_agent: str

class SpeakerDecision(BaseModel):
    format: str  # single_narrator | dual_speaker

class ScriptResult(BaseModel):
    script: str
    genre: str
    format: str

class ValidationResult(BaseModel):
    valid: bool
    issues: List[str] = []
    corrected_script: Optional[str] = None

class FinalResponse(BaseModel):
    task_id: str
    input: UserInput
    structured_metrics: StructuredInput
    genre: str
    speaker_format: str
    script: str
    metadata: dict = {}
