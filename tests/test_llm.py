from llm.client import generate_structured
from shared.schemas.adversarial import (
    AdversarialReview,
)


def main():
    prompt = """
    You are performing adversarial reliability review.

    A component has received the provisional assessment:
    ELEVATED_CONCERN

    Evidence:
    - Early leakage drift: 8.4%
    - Predicted 168h leakage: 13.7 uA
    - Prediction uncertainty: 1.9 uA
    - Lot anomaly score: 0.22
    - Significant early drift signal: active
    - High prediction uncertainty signal: active
    - Strong lot anomaly signal: inactive

    Challenge the provisional assessment.

    Look for:
    - contradictory evidence
    - unsupported assumptions
    - model limitations
    - reasons concern may be overstated
    - reasons concern may be understated

    Do not make the final PASS, REVIEW, or REJECT decision.
    """

    review = generate_structured(
        prompt=prompt,
        response_schema=AdversarialReview,
    )

    print(
        review.model_dump_json(
            indent=2
        )
    )


if __name__ == "__main__":
    main()