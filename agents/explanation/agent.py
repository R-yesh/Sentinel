from agents.base import BaseAgent
from llm.client import generate_structured
from shared.schemas.explaination import ExplanationResult
from shared.schemas.findings import Finding, Severity
from shared.schemas.workflow import WorkflowState


class ExplanationAgent(BaseAgent):
    name = "explanation"

    async def run(self, state: WorkflowState) -> WorkflowState:
        latent_output = state.agent_outputs.get("latent_defect", {})
        adversarial_output = state.agent_outputs.get("adversarial_qa", {})
        judge_output = state.agent_outputs.get("reliability_judge", {})

        assessment = latent_output.get("assessment")
        signals = latent_output.get("signals", [])

        adversarial_review = adversarial_output.get("review")

        decision = judge_output.get("decision")
        reason_code = judge_output.get("reason_code")
        reasoning = judge_output.get("reasoning")

        supporting_evidence = judge_output.get(
            "supporting_evidence",
            [],
        )

        unresolved_concerns = judge_output.get(
            "unresolved_concerns",
            [],
        )

        if decision is None:
            finding = Finding(
                agent=self.name,
                component_id=state.component_id,
                finding_type="explanation_unavailable",
                severity=Severity.MEDIUM,
                score=0.0,
                confidence=1.0,
                summary=(
                    "Explanation could not be generated because "
                    "no Reliability Judge decision is available."
                ),
                evidence=[
                    "Reliability Judge decision is unavailable."
                ],
                metadata={
                    "reason": "missing_judge_decision",
                },
            )

            state.findings.append(finding)
            explanation = (
                "Sentinel could not generate a final explanation "
                "because no Reliability Judge decision is available."
            )

            state.explanation = explanation

            state.agent_outputs[self.name] = {
                "explanation": None,
                "reason": "missing_judge_decision",
            }

            return state

        prompt = f"""
        You are the Explanation Agent in Sentinel,
        a semiconductor burn-in reliability analysis system.

        Your job is to clearly explain Sentinel's completed
        reliability decision to a reliability engineer.

        You are NOT a decision-making agent.

        The Reliability Judge's decision is final for this
        workflow. You must explain it faithfully and must not
        change, override, weaken, or strengthen the decision.

        Component:
        {state.component_id}

        Final decision:
        {decision}

        Decision reason code:
        {reason_code}

        Judge reasoning:
        {reasoning}

        Judge supporting evidence:
        {supporting_evidence}

        Judge unresolved concerns:
        {unresolved_concerns}

        Provisional latent-defect assessment:
        {assessment}

        Activated Sentinel signals:
        {signals}

        Adversarial review:
        {adversarial_review}

        Instructions:

        1. Explain the final decision in clear engineering language.

        2. Clearly distinguish observed evidence from
        model-derived forecasts or uncertainty.

        3. Include the most decision-relevant numerical
        evidence when available.

        4. Summarize meaningful adversarial arguments or
        unresolved concerns without presenting them as
        new measurements.

        5. Do not introduce evidence, thresholds, failure
        mechanisms, or measurements that are not supplied.

        6. Do not reconsider the final decision.

        7. Do not claim that prediction uncertainty is a
        calibrated confidence interval or probability
        of failure.

        8. A lot anomaly score describes how unusual this
        component is relative to its lot. Do not interpret
        it as proof of a systemic lot-wide defect.

        9. The recommended action must be consistent with
        the final decision:
        - PASS: communicate acceptance based on the
            available evidence.
        - REVIEW: recommend human reliability review.
        - REJECT: communicate rejection based on the
            available reliability evidence.

        10. Do not propose hypothetical physical causes,
        measurement errors, transient noise, or failure mechanisms
        unless explicitly identified by an upstream Sentinel agent.

        11. Random Forest tree disagreement indicates variation
        among tree predictions. Do not describe the forecast as
        unstable, erroneous, or an artifact solely because tree
        disagreement is high.

        12. A high lot anomaly score means the component is unusual
        relative to its lot population. Never interpret this as
        systemic, lot-wide, batch-wide, or manufacturing-wide
        instability without separate supporting evidence.

        13. Include at most 3 adversarial_context items.
        Include only concerns that materially affect the final
        decision and avoid repetition.

        14. A lot anomaly score is an anomaly/deviation measure,
        not a direct risk score.

        Describe low values as weak lot-relative anomaly evidence
        or as the component being statistically consistent with
        its lot. Do not describe them as "low lot-level risk",
        "lot-level normalcy", or similar risk conclusions.

        Keep the explanation concise, traceable, and suitable
        for an engineering audit trail.
        """

        result = generate_structured(
            prompt=prompt,
            response_schema=ExplanationResult
        )

        finding = Finding(
            agent=self.name,
            component_id=state.component_id,
            finding_type="qa_explanation",
            severity=Severity.INFO,
            score=0.0,
            confidence=1.0,
            summary=result.headline,
            evidence=result.key_evidence,
            metadata={
                "decision": decision,
                "reason_code": reason_code,
                "adversarial_context": (
                    result.adversarial_context
                ),
                "decision_reasoning": (
                    result.decision_reasoning
                ),
                "recommended_action": (
                    result.recommended_action
                ),
            },
        )

        state.findings.append(finding)

        state.explanation = result.decision_reasoning

        state.agent_outputs[self.name] = {
            "headline": result.headline,
            "summary": result.summary,
            "key_evidence": result.key_evidence,
            "adversarial_context": (
                result.adversarial_context
            ),
            "decision_reasoning": (
                result.decision_reasoning
            ),
            "recommended_action": (
                result.recommended_action
            ),
        }

        return state