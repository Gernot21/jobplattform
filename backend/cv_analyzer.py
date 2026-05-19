"""Extract structured fields from a CV PDF using Claude Sonnet 4.5."""
import io
import os
import json
import re
import uuid
import logging
from typing import Dict
from pypdf import PdfReader
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

MAX_TEXT_CHARS = 25_000  # cap text sent to LLM

SYSTEM_PROMPT = """You are a CV (Lebenslauf) parser for a job portal.
Read the raw text of a CV and extract structured fields about the candidate.

Return ONLY a strict JSON object with this schema (no markdown, no prose):
{
  "first_name": "<Vorname>",
  "last_name": "<Nachname>",
  "core_skills": "<eine oder zwei Sätze mit den wichtigsten Kernkompetenzen, kommagetrennt>",
  "key_experiences": "<2-4 Sätze, die die wichtigsten beruflichen Erfahrungen zusammenfassen>"
}

Rules:
- Antworte in der Sprache des CVs (meist Deutsch).
- Falls ein Feld nicht aus dem CV ablesbar ist, gib einen leeren String "" zurück.
- Bei "core_skills" liste reale Hard- & Soft-Skills (z. B. "Python, Projektleitung, Excel, Englisch C1").
- Bei "key_experiences" fasse Rollen, Branchen und Jahre kurz zusammen.
"""


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
    except Exception as e:
        logger.warning("PDF parse failed: %s", e)
        return ""
    parts = []
    for page in reader.pages[:30]:  # cap pages
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            continue
    text = "\n".join(parts).strip()
    if len(text) > MAX_TEXT_CHARS:
        text = text[:MAX_TEXT_CHARS]
    return text


def _extract_json(text: str) -> Dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        text = m.group(0)
    return json.loads(text)


async def analyze_cv(pdf_bytes: bytes) -> dict:
    """Return {first_name, last_name, core_skills, key_experiences}."""
    text = _extract_pdf_text(pdf_bytes)
    if not text:
        return {"first_name": "", "last_name": "", "core_skills": "", "key_experiences": "", "_warning": "no_text"}

    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        return {"first_name": "", "last_name": "", "core_skills": "", "key_experiences": "", "_warning": "no_key"}

    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=f"cv-{uuid.uuid4()}",
            system_message=SYSTEM_PROMPT,
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")
        response = await chat.send_message(UserMessage(text=f"RAW CV TEXT:\n\n{text}"))
        data = _extract_json(response)
        return {
            "first_name": str(data.get("first_name", "") or "").strip(),
            "last_name": str(data.get("last_name", "") or "").strip(),
            "core_skills": str(data.get("core_skills", "") or "").strip(),
            "key_experiences": str(data.get("key_experiences", "") or "").strip(),
        }
    except Exception as e:
        logger.exception("CV analysis failed: %s", e)
        return {"first_name": "", "last_name": "", "core_skills": "", "key_experiences": "", "_warning": "analysis_failed"}
