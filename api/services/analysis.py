import json
import re
from collections import Counter
from typing import Tuple, List

try:
    from nltk.corpus import stopwords as nltk_stopwords
except Exception:  # nltk not installed or data missing
    nltk_stopwords = None

try:
    from sumy.nlp.tokenizers import Tokenizer
    from sumy.parsers.plaintext import PlaintextParser
    from sumy.summarizers.text_rank import TextRankSummarizer
except Exception:  # sumy not installed
    TextRankSummarizer = None

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

if nltk_stopwords:
    try:
        STOPWORDS.update(nltk_stopwords.words("english"))
    except Exception:
        pass


def _local_analyze(text: str) -> Tuple[str, List[str]]:
    """Fallback summarization and keyword extraction.

    Attempts to use ``sumy``'s TextRank summarizer when available. If ``sumy``
    is not installed, a simple frequency based ranking is used as a fallback.
    """

    sentences = re.split(r"(?<=[.!?]) +", text.strip())
    words = re.findall(r"\b\w+\b", text.lower())
    filtered_words = [w for w in words if w not in STOPWORDS]
    counts = Counter(filtered_words)

    if TextRankSummarizer is not None:
        try:
            parser = PlaintextParser.from_string(text, Tokenizer("english"))
            summarizer = TextRankSummarizer()
            sum_sents = summarizer(parser.document, min(3, len(sentences)))
            summary = " ".join(str(s) for s in sum_sents).strip()
        except Exception:
            summary = ""
    else:
        scores = []
        for s in sentences:
            s_words = re.findall(r"\b\w+\b", s.lower())
            score = sum(counts.get(w, 0) for w in s_words)
            scores.append((score, s))
        scores.sort(key=lambda x: x[0], reverse=True)
        summary = " ".join(s for _, s in scores[:3]).strip()

    if not summary:
        summary = " ".join(sentences[:3]).strip()

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
