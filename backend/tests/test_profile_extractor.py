
import pytest
from pydantic import ValidationError

from app.models.candidate_profile import CandidateProfile
from app.services.profile_extractor import extract_candidate_profile


class FakeModel:
    def __init__(self, response):
        self.response = response

    def with_structured_output(self, schema, method):
        assert schema is CandidateProfile
        assert method == "json_schema"
        return self

    def invoke(self, messages):
        return self.response


def test_extract_candidate_profile():
    fake_llm = FakeModel({
        "name": "Sofia Rios",
        "skills": ["Python", "FastAPI"],
        "years_experience": 3,
    })

    profile = extract_candidate_profile(
        "Sofia Rios tiene 3 años de experiencia en Python y FastAPI.",
        llm=fake_llm,
    )

    assert profile.name == "Sofia Rios"
    assert profile.years_experience == 3
    assert "FastAPI" in profile.skills


def test_reject_empty_cv():
    with pytest.raises(ValueError):
        extract_candidate_profile(
            "   ",
            llm=FakeModel({}),
        )


def test_reject_invalid_ai_output():
    fake_llm = FakeModel({
        "name": "Sofia Rios",
        "years_experience": -3,
    })

    with pytest.raises(ValidationError):
        extract_candidate_profile(
            "CV ficticio de Sofia Rios",
            llm=fake_llm,
        )
