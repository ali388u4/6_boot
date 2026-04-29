import json
import uuid

from openai import AsyncOpenAI

from src.application.interfaces import SolvingStyleRepository
from src.domain.solution import SolutionPayload


class AISolverService:
    def __init__(self, solving_style_repo: SolvingStyleRepository, openai_client: AsyncOpenAI, model: str):
        self._solving_style_repo = solving_style_repo
        self._openai = openai_client
        self._model = model

    async def solve_question(self, subject_id: uuid.UUID, question_text: str) -> SolutionPayload:
        style = await self._solving_style_repo.get_for_subject(subject_id)
        style_json = style.style_json if style else {}

        system_prompt = style_json.get(
            "system_prompt",
            "You are a helpful tutor. Output JSON only in the required schema.",
        )

        schema_hint = {
            "final_answer": "string|null",
            "steps": [{"title": "string|null", "explanation": "string", "result": "string|null"}],
        }

        user_prompt = (
            "Solve the question and return JSON only.\n"
            f"Schema: {json.dumps(schema_hint, ensure_ascii=False)}\n"
            f"Question: {question_text}"
        )

        resp = await self._openai.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )

        content = resp.choices[0].message.content or "{}"
        payload = json.loads(content)
        return SolutionPayload.model_validate(payload)
