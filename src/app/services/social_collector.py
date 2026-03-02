"""Social data collector - orchestrates Reddit (+ future Twitter) fetching,
classification, scoring, and in-memory storage for the demo API."""

import logging
import threading
from datetime import datetime, timezone
from typing import Optional

from app.services.classifier import classify_feedback, fallback_classify
from app.services.reddit import get_reddit_client, fetch_project_signals

logger = logging.getLogger(__name__)

MONITORED_PROJECTS = ["chainlink", "aave", "base", "uniswap", "arbitrum"]


class SocialStore:
    """Thread-safe in-memory store for social signals and computed scores."""

    def __init__(self):
        self._lock = threading.Lock()
        self.signals: dict[str, list[dict]] = {}
        self.scores: dict[str, int] = {}
        self.summaries: dict[str, str] = {}
        self.trends: dict[str, list[int]] = {}
        self.last_updated: Optional[datetime] = None
        self.collection_count: int = 0
        self.is_live: bool = False

    def update(
        self,
        project: str,
        signals: list[dict],
        score: int,
        summary: str,
    ):
        with self._lock:
            self.signals[project] = signals
            self.scores[project] = score
            self.summaries[project] = summary

            # Track score trends (keep last 7)
            if project not in self.trends:
                self.trends[project] = []
            self.trends[project].append(score)
            if len(self.trends[project]) > 7:
                self.trends[project] = self.trends[project][-7:]

            self.last_updated = datetime.now(timezone.utc)
            self.is_live = True

    def get_signals(self, project: str) -> list[dict]:
        with self._lock:
            return self.signals.get(project, [])

    def get_score(self, project: str) -> Optional[int]:
        with self._lock:
            return self.scores.get(project)

    def get_summary(self, project: str) -> Optional[str]:
        with self._lock:
            return self.summaries.get(project)

    def get_trend(self, project: str) -> list[int]:
        with self._lock:
            return self.trends.get(project, [])

    def is_fresh(self, max_age_minutes: int = 10) -> bool:
        with self._lock:
            if not self.last_updated:
                return False
            age = (datetime.now(timezone.utc) - self.last_updated).total_seconds()
            return age < max_age_minutes * 60

    def increment_collection(self):
        with self._lock:
            self.collection_count += 1


# Singleton store
social_store = SocialStore()


def compute_score(signals: list[dict]) -> int:
    """Compute sentiment score 0-100 from classified signals.

    Same formula as sentiment.py: weighted positive/neutral/negative.
    """
    if not signals:
        return 50  # neutral default

    pos = 0
    neg = 0
    neu = 0
    total = 0

    for s in signals:
        cat = s.get("category", "noise")
        if cat in ("praise", "feature_request"):
            pos += 1
        elif cat in ("bug", "complaint"):
            neg += 1
        elif cat == "question":
            neu += 1
        else:
            continue
        total += 1

    if total == 0:
        return 50

    score = round(((pos * 1.0 + neu * 0.5) / total) * 100)
    return max(0, min(100, score))


def generate_summary(project: str, signals: list[dict], score: int) -> str:
    """Generate a summary from classified signals.

    Uses Claude if available, otherwise builds a simple template.
    """
    if not signals:
        return f"No recent community signals for {project}."

    # Try Claude for a real summary
    try:
        import anthropic
        from app.config import config

        if config.CLAUDE_API_KEY:
            client = anthropic.Anthropic(api_key=config.CLAUDE_API_KEY)

            # Build context from top signals
            top_signals = signals[:15]
            signal_text = "\n".join(
                f"- [{s['category']}] {s['text'][:150]}" for s in top_signals
            )

            prompt = f"""Summarize community sentiment for the crypto project "{project}" based on these recent social media signals. Score: {score}/100.

Signals:
{signal_text}

Write 2-3 sentences. Be specific about what people are saying. No marketing language. No emojis."""

            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
    except Exception as e:
        logger.warning(f"Claude summary failed for {project}: {e}")

    # Fallback: template-based summary
    cats = {}
    for s in signals:
        cat = s.get("category", "noise")
        cats[cat] = cats.get(cat, 0) + 1

    top_cat = max(cats, key=cats.get) if cats else "noise"
    label = "positive" if score >= 70 else "mixed" if score >= 40 else "negative"

    return (
        f"Community sentiment for {project.title()} is {label} at {score}/100 "
        f"based on {len(signals)} recent signals. "
        f"Most common category: {top_cat.replace('_', ' ')}."
    )


async def classify_signal(signal: dict) -> dict:
    """Classify a single signal using existing classifier."""
    result = await classify_feedback(
        text=signal["text"],
        username=signal.get("author", "unknown"),
        followers=signal.get("followers", 0),
        use_ai=True,
    )
    signal["category"] = result["category"]
    signal["priority"] = _compute_priority(result["category"], signal.get("engagement", 0))
    signal["sentiment"] = result.get("sentiment", "neutral")
    signal["confidence"] = result.get("confidence", 0.5)
    signal["summary"] = result.get("summary", signal["text"][:100])
    return signal


def _compute_priority(category: str, engagement: int) -> str:
    """Compute priority from category and engagement."""
    if engagement >= 100:
        return "high"
    if category in ("bug", "complaint") and engagement >= 20:
        return "high"
    if category in ("bug", "complaint", "feature_request"):
        return "medium"
    return "low"


async def collect_all_projects():
    """Main collection loop: fetch, classify, score, store for all projects."""
    reddit = get_reddit_client()
    if not reddit:
        logger.info("No Reddit client available, skipping collection")
        return

    logger.info("Starting social collection for all projects...")
    social_store.increment_collection()

    for project in MONITORED_PROJECTS:
        try:
            # Fetch from Reddit
            raw_signals = fetch_project_signals(reddit, project, limit_per_sub=10)

            if not raw_signals:
                logger.info(f"No Reddit signals for {project}")
                continue

            # Classify each signal
            classified = []
            for signal in raw_signals:
                try:
                    classified_signal = await classify_signal(signal)
                    # Skip noise
                    if classified_signal["category"] != "noise" or classified_signal.get("confidence", 0) < 0.7:
                        classified.append(classified_signal)
                except Exception as e:
                    logger.warning(f"Classification failed for signal: {e}")
                    # Use fallback classification
                    fb = fallback_classify(signal["text"])
                    signal.update(fb)
                    if signal["category"] != "noise":
                        classified.append(signal)

            # Compute score
            score = compute_score(classified)

            # Generate summary
            summary = generate_summary(project, classified, score)

            # Clean up signals for API output (remove internal fields)
            api_signals = []
            for s in classified:
                api_signals.append({
                    "text": s["text"],
                    "category": s["category"],
                    "priority": s["priority"],
                    "engagement": s.get("engagement", 0),
                    "author": s.get("author", "unknown"),
                    "followers": s.get("followers", 0),
                    "timestamp": s.get("timestamp", ""),
                    "source": s.get("source", "reddit"),
                })

            # Store
            social_store.update(project, api_signals, score, summary)

            logger.info(
                f"Collected {project}: {len(api_signals)} signals, score={score}"
            )

        except Exception as e:
            logger.error(f"Collection failed for {project}: {e}")
            continue

    logger.info("Social collection complete")
