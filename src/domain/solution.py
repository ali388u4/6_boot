from pydantic import BaseModel, Field


class SolutionStep(BaseModel):
    title: str | None = None
    explanation: str
    result: str | None = None


class SolutionPayload(BaseModel):
    final_answer: str | None = None
    steps: list[SolutionStep] = Field(default_factory=list)
