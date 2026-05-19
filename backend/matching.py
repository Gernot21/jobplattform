"""AI Matching using Claude Sonnet 4.5 via emergentintegrations."""
import os
import json
import re
import uuid
import logging
from typing import Dict
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert HR matching engine for a part-time job portal (20%-80% workload).
You evaluate the fit between an employee profile and a job posting.

Compute a final match score (0-100) using a weighted combination of:
1. PRIMARY (50%): Overlap between candidate's "looking_for" wishes and the job description.
2. SECONDARY (30%): Overlap between candidate's "core_skills" and the job requirements/description.
3. TERTIARY (20%): Overlap between candidate's "key_experiences" and the job profile.

Return ONLY a strict JSON object with this schema (no markdown, no prose):
{
  "score": <integer 0-100>,
  "reason": "<one concise sentence in the same language as the inputs>",
  "highlights": ["<short bullet>", "<short bullet>"]
}
"""


def _extract_json(text: str) -> Dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)


async def compute_match(employee_profile: dict, job: dict) -> dict:
    """Return a match dict {score, reason, highlights}."""
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        return {"score": 0, "reason": "Missing LLM key", "highlights": []}

    user_text = f"""EMPLOYEE PROFILE:
- looking_for: {employee_profile.get('looking_for','')}
- core_skills: {employee_profile.get('core_skills','')}
- key_experiences: {employee_profile.get('key_experiences','')}
- why_consider: {employee_profile.get('why_consider','')}
- desired_percentage: {employee_profile.get('desired_percentage_min',20)}%-{employee_profile.get('desired_percentage_max',80)}%

JOB POSTING:
- title: {job.get('title','')}
- description: {job.get('description','')}
- percentage: {job.get('percentage_min',20)}%-{job.get('percentage_max',80)}%
- location: {job.get('location','')}

Compute the match according to the system instructions and return ONLY JSON.
"""
    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=f"match-{uuid.uuid4()}",
            system_message=SYSTEM_PROMPT,
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")
        response = await chat.send_message(UserMessage(text=user_text))
        data = _extract_json(response)
        score = int(data.get("score", 0))
        score = max(0, min(100, score))
        return {
            "score": score,
            "reason": str(data.get("reason", "")),
            "highlights": list(data.get("highlights", []))[:5],
        }
    except Exception as e:
        logger.exception("Match computation failed: %s", e)
        return {"score": 0, "reason": "Matching service temporarily unavailable", "highlights": []}
