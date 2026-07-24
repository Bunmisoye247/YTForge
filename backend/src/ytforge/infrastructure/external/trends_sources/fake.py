from __future__ import annotations


class FakeTrendSource:
    """Deterministic canned topics — no network needed, used when
    `provider_set=fake`."""

    async def fetch_candidate_topics(self, limit: int = 10) -> list[str]:
        topics = [
            "On-device AI models are getting smaller and faster",
            "New open-source video generation model released",
            "AI agents automating software engineering tasks",
            "Robotics startups raise record funding",
            "Quantum computing reaches new milestone",
        ]
        return topics[:limit]
