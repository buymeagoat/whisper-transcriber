import json
import re
from collections import Counter
from typing import Tuple, List

try:
    import openai
except Exception:  # openai not installed
    openai = None

from api.settings import settings
from api.utils.logger import get_system_logger

system_log = get_system_logger()


STOPWORDS = {
    "the",
    "and",
    "to",
    "a",
    "of",
    "in",
    "is",
    "it",
    "for",
    "on",
    "with",
    "as",
    "at",
    "this",
    "that",
    "an",
}


def _local_analyze(text: str) -> Tuple[str, List[str]]:
    """Fallback summarization and keyword extraction."""
    sentences = re.split(r"(?<=[.!?]) +", text.strip())
    summary = " ".join(sentences[:3]).strip()
    words = re.findall(r"\b\w+\b", text.lower())
    counts = Counter(w for w in words if w not in STOPWORDS)
    keywords = [w for w, _ in counts.most_common(5)]
    return summary, keywords


def analyze_text(text: str) -> Tuple[str, List[str]]:
    """Return summary and keywords using OpenAI when configured."""
    if settings.openai_api_key and openai is not None:
        openai.api_key = settings.openai_api_key
        try:
            prompt = (
                "Summarize the following transcript in a few sentences and list five key keywords as a comma separated list.\n"  # noqa: E501
                "Transcript:\n" + text
            )
            response = openai.ChatCompletion.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            content = response.choices[0].message.content.strip()
            try:
                data = json.loads(content)
                summary = data.get("summary", "")
                keywords = data.get("keywords", [])
                if isinstance(keywords, str):
                    keywords = [k.strip() for k in keywords.split(",") if k.strip()]
            except json.JSONDecodeError:
                summary, kw_text = content, ""
                if "Keywords:" in content:
                    parts = content.split("Keywords:", 1)
                    summary = parts[0].strip()
                    kw_text = parts[1].strip()
                keywords = [k.strip() for k in kw_text.split(",") if k.strip()]
            return summary, keywords
        except Exception as e:
            system_log.error(f"OpenAI analysis failed: {e}")
    return _local_analyze(text)
