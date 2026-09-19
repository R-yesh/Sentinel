from enum import Enum

from pydantic import BaseModel, Field

class ChallengeType(str, Enum):
    FORECAST_LIMITATION = "FORECAST_LIMITATION"
    MODEL_UNCERTAINTY = "MODEL_UNCERTAINTY"
    EVIDENCE_CONFLICT = "EVIDENCE_CONFLICT"
    CORROBORATING_EVIDENCE = "CORROBORATING_EVIDENCE"
    ASSUMPTION_CHALLENGE = "ASSUMPTION_CHALLENGE"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"

class ChallengeDirection(str, Enum):
    LOWER_CONCERN = "LOWER_CONCERN"
    HIGHER_CONCERN = "HIGHER_CONCERN"
    REVIEW = "REVIEW"


class AdversarialChallenge(BaseModel):
    challenge_type: ChallengeType
    direction: ChallengeDirection
    summary: str


class AdversarialReview(BaseModel):
    challenged_assessment: str

    challenges: list[AdversarialChallenge] = Field(
        default_factory=list
    )

    unresolved_conflict: bool