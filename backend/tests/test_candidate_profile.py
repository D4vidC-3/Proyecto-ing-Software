
import pytest
from pydantic import ValidationError

from app.models.candidate_profile import CandidateProfile


def test_create_valid_candidate_profile():
    profile = CandidateProfile(
        name="Sofia Rios",
        location="Medellin",
        target_role="Backend Developer",
        years_experience=3,
        skills=["Python", "FastAPI", "PostgreSQL"],
        preferences={
            "work_modes": ["remoto", "hibrido"],
            "salary_min_cop": 4500000,
            "salary_max_cop": 5500000,
        },
    )

    assert profile.name == "Sofia Rios"
    assert profile.years_experience == 3
    assert "Python" in profile.skills
    assert profile.preferences.salary_min_cop == 4500000


def test_candidate_with_missing_information():
    profile = CandidateProfile(name="Sofia Rios")

    assert profile.email is None
    assert profile.skills == []
    assert profile.work_experience == []
    assert profile.preferences.salary_min_cop is None


def test_reject_negative_experience():
    with pytest.raises(ValidationError):
        CandidateProfile(
            name="Sofia Rios",
            years_experience=-5,
        )


def test_reject_unexpected_fields():
    with pytest.raises(ValidationError):
        CandidateProfile(
            name="Sofia Rios",
            invented_field="invalid",
        )
def test_normalize_null_lists():
    profile = CandidateProfile.model_validate({
        "name": "Sofia Rios",
        "skills": None,
        "languages": None,
        "work_experience": None,
        "education": None,
        "preferences": {
            "desired_roles": None,
            "preferred_locations": None,
            "work_modes": None,
        },
    })

    assert profile.skills == []
    assert profile.languages == []
    assert profile.work_experience == []
    assert profile.education == []
    assert profile.preferences.desired_roles == []
    assert profile.preferences.preferred_locations == []
    assert profile.preferences.work_modes == []