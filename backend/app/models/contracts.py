from datetime import datetime
from typing import Annotated, Literal
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    field_validator,
    model_validator,
)
from app.models.candidate_profile import CandidateProfile

Id = Annotated[str, Field(pattern=r"^[0-9a-f]{32}$")]
VacancyId = Annotated[str, Field(pattern=r"^(?:demo-[0-9]{2}|escenarios-v(?:0[1-9]|10))$")]
Status = Literal["postulado", "en_revision", "entrevista", "contratado", "descartado"]


class Gap(BaseModel):
    field: str
    label: str
    importance: str
    status: str
    missing: bool


class ProfileView(BaseModel):
    id: str
    candidate_id: str
    document_id: str | None
    source: str
    updated_at: datetime
    profile: CandidateProfile
    gaps: list[Gap]


class VacancyData(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    id: VacancyId
    company: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    location: str | None = None
    work_mode: Literal["remoto", "hibrido", "presencial"] | None = None
    contract_type: str | None = None
    salary_min_cop: int | None = Field(default=None, ge=0)
    salary_max_cop: int | None = Field(default=None, ge=0)
    years_experience: float | None = Field(default=None, ge=0)
    required_skills: list[str] = Field(default_factory=list)
    desired_skills: list[str] = Field(default_factory=list)
    published_at: str
    source: Literal["demo"] = "demo"

    @field_validator("work_mode", mode="before")
    @classmethod
    def normalize_mode(cls, value):
        from app.services.matching import normalize

        return normalize(value) if value else None

    @field_validator("required_skills", "desired_skills", mode="before")
    @classmethod
    def normalize_skills(cls, value):
        return list(dict.fromkeys(s.strip() for s in (value or []) if s.strip()))

    @model_validator(mode="after")
    def valid_salary(self):
        if (
            self.salary_min_cop is not None
            and self.salary_max_cop is not None
            and self.salary_min_cop > self.salary_max_cop
        ):
            raise ValueError("Rango salarial inválido")
        return self


class ApplicationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidate_id: Id
    vacancy_id: VacancyId
    confirmed: StrictBool = False
    simulation_id: Id | None = None


class SimulationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confirmed: StrictBool = False
    expected_current_id: Id


class StatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Status


class ApplicationView(BaseModel):
    id: str
    candidate_id: str
    vacancy_id: str
    status: Status
    simulation_id: str
    is_current: bool
    hired_at: datetime | None
    created_at: datetime
    evidence: dict
    vacancy: VacancyData
    next_step: str
    allowed_transitions: list[Status]


class LogView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    candidate_id: str | None
    application_id: str | None
    agent: str
    action: str
    status: str
    reason: str
    result_ref: str | None
    operation_id: str | None
    execution_context: dict | None
    created_at: datetime


class ReminderView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    application_id: str
    due_at: datetime
    message: str
    pending: bool


class ScoreComponent(BaseModel):
    criterion: str
    weight: int
    points: float
    known: bool
    reason: str


class RecommendationView(BaseModel):
    vacancy: VacancyData
    score: float = Field(ge=0, le=100)
    matched_skills: list[str]
    missing_skills: list[str]
    components: list[ScoreComponent]
    unknown: list[str]
