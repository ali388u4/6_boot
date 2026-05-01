import json
import io
import uuid
from base64 import b64encode

from pypdf import PdfReader
from docx import Document

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


    async def build_chapter_context(self, *, bot, files) -> str:
        parts: list[str] = []
        for f in files:
            file_text = ""

            if f.file_type == "photo":
                try:
                    file = await bot.get_file(f.telegram_file_id)
                    buf = io.BytesIO()
                    await bot.download_file(file.file_path, destination=buf)
                    b64 = b64encode(buf.getvalue()).decode("ascii")

                    resp = await self._openai.chat.completions.create(
                        model=self._model,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": "Extract the Arabic/English text content from this image."},
                                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                                ],
                            }
                        ],
                    )
                    file_text = (resp.choices[0].message.content or "").strip()
                except Exception:
                    file_text = ""
            else:
                try:
                    file = await bot.get_file(f.telegram_file_id)
                    buf = io.BytesIO()
                    await bot.download_file(file.file_path, destination=buf)
                    raw = buf.getvalue()

                    name = (f.file_name or "").lower()
                    if name.endswith(".pdf"):
                        reader = PdfReader(io.BytesIO(raw))
                        file_text = "\n".join((page.extract_text() or "") for page in reader.pages)
                    elif name.endswith(".docx"):
                        doc = Document(io.BytesIO(raw))
                        file_text = "\n".join(p.text for p in doc.paragraphs)
                    elif name.endswith(".txt"):
                        file_text = raw.decode("utf-8", errors="ignore")
                    else:
                        file_text = ""
                except Exception:
                    file_text = ""

            if file_text.strip():
                label = f.file_name or "file"
                parts.append(f"### {label}\n{file_text.strip()}")

        return "\n\n".join(parts)


    async def generate_from_chapter(self, *, intent: str, chapter_text: str) -> str:
        intent = intent.strip()

        mode = "question"
        if intent in {"اختبرني", "اختبار"}:
            mode = "quiz"
        elif intent in {"اشرح"}:
            mode = "explain"

        system_prompt = (
            "You are an Arabic tutor. Use ONLY the provided chapter content. "
            "If the answer is not in the chapter content, say you cannot find it in the files."
        )

        if mode == "quiz":
            user_prompt = (
                "Create a short quiz from the chapter content. "
                "Return in Arabic. Include 5 questions: mix MCQ and True/False. "
                "After the quiz, provide the answers.\n\n"
                f"CHAPTER CONTENT:\n{chapter_text}"
            )
        elif mode == "explain":
            user_prompt = (
                "Explain the main ideas of the chapter content in Arabic, in a structured way with headings.\n\n"
                f"CHAPTER CONTENT:\n{chapter_text}"
            )
        else:
            user_prompt = (
                "Create ONE high-quality exam-style question from the chapter content in Arabic. "
                "Then provide the correct answer and a brief explanation.\n\n"
                f"CHAPTER CONTENT:\n{chapter_text}"
            )

        resp = await self._openai.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return (resp.choices[0].message.content or "").strip() or "تعذر إنشاء محتوى الآن"
