from abc import ABC, abstractmethod

from shared.schemas.workflow import WorkflowState


class BaseAgent(ABC):
    name: str

    @abstractmethod
    async def run(self, state: WorkflowState) -> WorkflowState:
        """
        Execute the agent against the current workflow state
        and return the updated state.
        """
        raise NotImplementedError