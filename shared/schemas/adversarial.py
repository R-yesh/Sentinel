from enum import Enum

from pydantic import BaseModel, Field


class ChallengeDirection(str, Enum):
    LOWER_CONCERN = "LOWER_CONCERN"
    HIGHER_CONCERN = "HIGHER_CONCERN"
    REVIEW = "REVIEW"


class AdversarialChallenge(BaseModel):
    challenge_type: str
    direction: ChallengeDirection
    summary: str


class AdversarialReview(BaseModel):
    challenged_assessment: str

    challenges: list[AdversarialChallenge] = Field(
        default_factory=list
    )

    unresolved_conflict: bool