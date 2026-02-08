"""
Reasoning chain tracking and storage
Captures how the model arrived at each answer for future improvement

"""
from datetime import datetime
import uuid

from pydantic import BaseModel, Field


class ReasoningStep(BaseModel):
    """
    Individual reasoning step in the chain
    
    """
    step_number: int
    thought: str  # What the model thought
    action: str  # What action was taken (search, retrieve, synthesize, etc.)
    source: str  # Which source was consulted (memory, web, history, etc.)
    information_gathered: str | None = None  # What was found
    confidence: float  # 0-1 confidence in this step
    alternatives_considered: list[str] = Field(default_factory=list)  # Other options that were rejected
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ReasoningChain(BaseModel):
    """
    Complete reasoning chain for one message response

    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    message_id: str  # Reference to the user's message
    reasoning_steps: list[ReasoningStep] = Field(default_factory=list)
    
    # Final outcome
    final_answer: str | None = None
    final_confidence: float | None = None  # 0-1 overall confidence
    sources_used: list[str] = Field(default_factory=list)  # Which sources contributed
    sources_considered: dict[str, float] = Field(default_factory=dict)  # All sources evaluated: {source: confidence}
    uncertainty_flags: list[str] = Field(default_factory=list)  # Aspects the model was unsure about
    
    # Metadata
    model_used: str | None = None  # Which LLM model
    total_duration_ms: float | None = None  # How long reasoning took
    tokens_used: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # User feedback (if provided later)
    user_rating: int | None = None  # 1-5 star rating
    user_feedback: str | None = None  # User's comment
    was_helpful: bool | None = None  # True/False feedback
    corrections: list[dict] = Field(default_factory=list)  # [{step: 3, issue: "...", correction: "..."}]

    def add_step(
        self,
        thought: str,
        action: str,
        source: str,
        confidence: float,
        information_gathered: str = None,
        alternatives: list[str] = None,
    ) -> ReasoningStep:
        
        # Add a step to the reasoning chain
        step_num = len(self.reasoning_steps) + 1
        step = ReasoningStep(
            step_number=step_num,
            thought=thought,
            action=action,
            source=source,
            information_gathered=information_gathered,
            confidence=confidence,
            alternatives_considered=alternatives or [],
        )
        self.reasoning_steps.append(step)
        return step

    def complete(
        self,
        final_answer: str,
        final_confidence: float,
        model_used: str,
        duration_ms: float,
    ):
        # Mark reasoning as complete
        self.final_answer = final_answer
        self.final_confidence = final_confidence
        self.model_used = model_used
        self.total_duration_ms = duration_ms
        self.sources_used = list(set(s.source for s in self.reasoning_steps))


class ReasoningTracker:
    """Helper to build reasoning chains in services"""

    def __init__(self, session_id: str, message_id: str):
        self.chain = ReasoningChain(
            session_id=session_id,
            message_id=message_id,
        )

    def log_step(
        self,
        thought: str,
        action: str,
        source: str,
        confidence: float,
        information: str = None,
        alternatives: list[str] = None,
    ):
        # Log a reasoning step
        self.chain.add_step(
            thought=thought,
            action=action,
            source=source,
            confidence=confidence,
            information_gathered=information,
            alternatives=alternatives,
        )

    def log_source_evaluation(
        self,
        source_name: str,
        confidence: float,
        reason: str = None,
    ):
        # Log evaluation of a source
        if not self.chain.sources_considered:
            self.chain.sources_considered = {}
        self.chain.sources_considered[source_name] = confidence

    def log_uncertainty(self, flag: str):
        # Log an uncertainty flag
        if flag not in self.chain.uncertainty_flags:
            self.chain.uncertainty_flags.append(flag)

    def finalize(
        self,
        final_answer: str,
        final_confidence: float,
        model_used: str,
        duration_ms: float,
    ) -> ReasoningChain:
        # Finalize the reasoning chain
        self.chain.complete(
            final_answer=final_answer,
            final_confidence=final_confidence,
            model_used=model_used,
            duration_ms=duration_ms,
        )
        return self.chain

    def get_summary(self) -> dict:
        """
        Get human-readable summary of reasoning
        """
        return {
            'steps_count': len(self.chain.reasoning_steps),
            'sources_used': self.chain.sources_used,
            'final_confidence': self.chain.final_confidence,
            'uncertainty_flags': self.chain.uncertainty_flags,
            'duration_ms': self.chain.total_duration_ms,
            'step_details': [
                {
                    'step': s.step_number,
                    'action': s.action,
                    'source': s.source,
                    'confidence': s.confidence,
                }
                for s in self.chain.reasoning_steps
            ]
        }
    