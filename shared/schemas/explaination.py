from pydantic import BaseModel, Field


class ExplanationResult(BaseModel):
    headline: str

    summary: str

    key_evidence: list[str] = Field(
        default_factory=list
    )

    adversarial_context: list[str] = Field(
        default_factory=list
    )

    decision_reasoning: str

    recommended_action: str