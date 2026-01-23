import json
import logging
from typing import Optional
import anthropic

from app.config import config

logger = logging.getLogger(__name__)

# Classification prompt
CLASSIFY_PROMPT = """Categorize this tweet mentioning a product/service.

Tweet: "{text}"
Author: @{username} ({followers} followers)

Return JSON only, no other text:
{{
  "category": "bug|complaint|feature_request|question|praise|noise",
  "sentiment": "frustrated|neutral|happy",
  "confidence": 0.0-1.0,
  "summary": "One sentence describing the feedback"
}}

Categories:
- bug: Something is broken, not working, error, crash
- complaint: Frustration about experience (slow, confusing, annoying) but not a specific bug
- feature_request: Wants something new, suggestion, "wish you had", "please add"
- question: Asking how to do something, needs help
- praise: Positive feedback, love, recommendation, thanks
- noise: Unrelated mention, spam, just tagging without substance, announcements

Be accurate. When uncertain, choose the more actionable category.
bug > complaint > feature_request > question > praise > noise"""

# Sentiment-only prompt (when category is known from $ tag)
SENTIMENT_PROMPT = """Analyze the sentiment of this tweet. Category is already known: {category}

Tweet: "{text}"

Return JSON only:
{{
  "sentiment": "frustrated|neutral|happy",
  "summary": "One sentence describing the feedback"
}}"""


def get_client() -> anthropic.Anthropic | None:
    """Get Anthropic client."""
    if not config.CLAUDE_API_KEY:
        logger.warning("CLAUDE_API_KEY not set, classification disabled")
        return None
    return anthropic.Anthropic(api_key=config.CLAUDE_API_KEY)


async def classify_feedback(
    text: str,
    username: str,
    followers: int,
    category_override: Optional[str] = None,
    use_ai: bool = True,
) -> dict:
    """Classify a feedback tweet using Claude Haiku.

    Args:
        text: Tweet text
        username: Author username
        followers: Author follower count
        category_override: If set, skip category detection and only get sentiment
        use_ai: If False, use keyword-based classification (for free tier)

    Returns:
        dict with category, sentiment, confidence, summary
    """
    # Free tier uses keyword fallback
    if not use_ai:
        return fallback_classify(text, category_override)

    client = get_client()

    if not client:
        # Fallback to keyword-based classification
        return fallback_classify(text, category_override)

    try:
        if category_override:
            prompt = SENTIMENT_PROMPT.format(
                category=category_override,
                text=text,
            )
        else:
            prompt = CLASSIFY_PROMPT.format(
                text=text,
                username=username,
                followers=followers,
            )

        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )

        # Parse response
        response_text = response.content[0].text.strip()

        # Try to extract JSON if wrapped in markdown
        if "```" in response_text:
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start != -1 and end > start:
                response_text = response_text[start:end]

        result = json.loads(response_text)

        # Add category override if provided
        if category_override:
            result["category"] = category_override
            result["confidence"] = 1.0

        # Validate fields
        valid_categories = ["bug", "complaint", "feature_request", "question", "praise", "noise"]
        valid_sentiments = ["frustrated", "neutral", "happy"]

        if result.get("category") not in valid_categories:
            result["category"] = "noise"
        if result.get("sentiment") not in valid_sentiments:
            result["sentiment"] = "neutral"
        if not isinstance(result.get("confidence"), (int, float)):
            result["confidence"] = 0.7
        if not result.get("summary"):
            result["summary"] = text[:100]

        logger.debug(f"Classified tweet: {result['category']} ({result['confidence']})")
        return result

    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse Claude response: {e}")
        return fallback_classify(text, category_override)
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        return fallback_classify(text, category_override)


def fallback_classify(text: str, category_override: Optional[str] = None) -> dict:
    """Fallback keyword-based classification when Claude is unavailable."""
    text_lower = text.lower()

    # Keyword lists
    bug_keywords = ["bug", "broken", "issue", "error", "crash", "fix", "doesn't work", "not working", "failed"]
    feature_keywords = ["feature", "request", "add", "wish", "would be nice", "please add", "suggestion", "could you"]
    praise_keywords = ["love", "amazing", "awesome", "great", "thank", "best", "incredible", "fantastic"]
    complaint_keywords = ["hate", "terrible", "awful", "worst", "frustrated", "annoying", "slow", "bad"]
    question_keywords = ["how do", "how can", "how to", "help", "?", "anyone know", "does anyone"]

    # Determine category
    if category_override:
        category = category_override
        confidence = 1.0
    elif any(kw in text_lower for kw in bug_keywords):
        category = "bug"
        confidence = 0.6
    elif any(kw in text_lower for kw in complaint_keywords):
        category = "complaint"
        confidence = 0.6
    elif any(kw in text_lower for kw in feature_keywords):
        category = "feature_request"
        confidence = 0.6
    elif any(kw in text_lower for kw in praise_keywords):
        category = "praise"
        confidence = 0.6
    elif any(kw in text_lower for kw in question_keywords):
        category = "question"
        confidence = 0.5
    else:
        category = "noise"
        confidence = 0.4

    # Determine sentiment
    positive_words = ["love", "great", "amazing", "awesome", "thanks", "thank", "best", "fantastic"]
    negative_words = ["hate", "broken", "bug", "issue", "terrible", "awful", "frustrated", "annoying"]

    if any(w in text_lower for w in negative_words):
        sentiment = "frustrated"
    elif any(w in text_lower for w in positive_words):
        sentiment = "happy"
    else:
        sentiment = "neutral"

    return {
        "category": category,
        "sentiment": sentiment,
        "confidence": confidence,
        "summary": text[:100] + ("..." if len(text) > 100 else ""),
    }


async def batch_classify(items: list[dict]) -> list[dict]:
    """Classify multiple items. Uses fallback for speed if Claude unavailable."""
    results = []

    for item in items:
        result = await classify_feedback(
            text=item["text"],
            username=item.get("username", "unknown"),
            followers=item.get("followers", 0),
            category_override=item.get("category_override"),
        )
        results.append(result)

    return results
