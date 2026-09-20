from enum import Enum

from pydantic import BaseModel, Field


class ReliabilityDecision(str, Enum):
    PASS = "PASS"
    REVIEW = "REVIEW"
    REJECT = "REJECT"


class JudgeReasonCode(str, Enum):
    EVIDENCE_SUPPORTS_PASS = "EVIDENCE_SUPPORTS_PASS"
    EVIDENCE_SUPPORTS_REJECT = "EVIDENCE_SUPPORTS_REJECT"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class JudgeDecision(BaseModel):
    decision: ReliabilityDecision

    reason_code: JudgeReasonCode

    reasoning: str

    supporting_evidence: list[str] = Field(
        default_factory=list
    )

    unresolved_concerns: list[str] = Field(
        default_factory=list
    )