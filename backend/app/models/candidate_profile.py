from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CleanModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("*", mode="before")
    @classmethod
    def clean_blanks(cls, value):
        if isinstance(value, str):
            return value.strip() or None
        if isinstance(value, list):
            return [
                v.strip() if isinstance(v, str) else v
                for v in value
                if not isinstance(v, str) or v.strip()
            ]
        return value


class WorkExperience(CleanModel):
    model_config = ConfigDict(extra="forbid")

    company: str | None = None
    role: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None


class Education(CleanModel):
    model_config = ConfigDict(extra="forbid")

    degree: str | None = None
    institution: str | None = None
    start_year: int | None = None
    end_year: int | None = None


class JobPreferences(CleanModel):
    model_config = ConfigDict(extra="forbid")

    desired_roles: list[str] = Field(default_factory=list)
    preferred_locations: list[str] = Field(default_factory=list)
    work_modes: list[str] = Field(default_factory=list)

    salary_min_cop: int | None = Field(default=None, ge=0)
    salary_max_cop: int | None = Field(default=None, ge=0)

    contract_type: str | None = None
    availability: str | None = None

    @model_validator(mode="after")
    def salary_order(self):
        if (
            self.salary_min_cop is not None
            and self.salary_max_cop is not None
            and self.salary_min_cop > self.salary_max_cop
        ):
            raise ValueError("El salario mínimo no puede superar el máximo")
        return self

    @field_validator(
        "desired_roles",
        "preferred_locations",
        "work_modes",
        mode="before",
    )
    @classmethod
    def normalize_empty_lists(cls, value):
        return [] if value is None else value


class CandidateProfile(CleanModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None

    professional_summary: str | None = None
    target_role: str | None = None

    years_experience: float | None = Field(default=None, ge=0)

    skills: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)

    work_experience: list[WorkExperience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)

    preferences: JobPreferences = Field(default_factory=JobPreferences)

    @field_validator(
        "skills",
        "languages",
        "work_experience",
        "education",
        mode="before",
    )
    @classmethod
    def normalize_empty_lists(cls, value):
        return [] if value is None else value

    @field_validator("preferences", mode="before")
    @classmethod
    def empty_preferences(cls, value):
        return {} if value is None else value
