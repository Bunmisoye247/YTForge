from __future__ import annotations

import hashlib
import json
from collections.abc import AsyncIterator

from ytforge.application.dto.image import ImageAsset, ImageRequest
from ytforge.application.dto.llm import LLMChunk, LLMRequest, LLMResponse
from ytforge.application.dto.music import MusicAsset, MusicRequest
from ytforge.application.dto.search import SearchQuery, SearchResult
from ytforge.application.dto.tts import (
    AudioAsset,
    ClonedVoice,
    TTSRequest,
    VoiceCloneRequest,
    WordTimestamp,
)
from ytforge.application.dto.vector import Vector
from ytforge.application.dto.video import VideoJob, VideoJobState, VideoJobStatus, VideoRequest

# Each entry: a set of lowercase keywords that must ALL appear in the
# rendered prompt, and the canned JSON/text to return when they do — lets
# every agent's happy path be exercised end-to-end against the fake
# provider, not just WriterAgent's. Matched against the OUTPUT SPEC section
# of each prompts/*.v1.md.j2 template (the field names it asks for), not
# generic prompt content, so it stays specific to each agent's actual
# template rather than pattern-matching too broadly.
_FAKE_RESPONSES: list[tuple[frozenset[str], str | None]] = [
    (
        frozenset({"hook", "cta"}),
        json.dumps(
            {
                "hook": "You won't believe what happens when AI meets everyday life.",
                "body": ["Section 1: the setup", "Section 2: the twist", "Section 3: the payoff"],
                "cta": "Subscribe for more deep dives.",
            }
        ),
    ),
    (
        frozenset({"verdict", "flags"}),
        json.dumps({"verdict": "passed", "flags": []}),
    ),
    (
        frozenset({"image_prompt", "video_prompt", "voice_line"}),
        json.dumps(
            [
                {
                    "description": "Opening establishing shot.",
                    "duration_seconds": 8,
                    "image_prompt": "wide shot, cinematic lighting",
                    "video_prompt": "slow push-in, cinematic",
                    "voice_line": "Here's what changed.",
                },
                {
                    "description": "Close-up detail shot.",
                    "duration_seconds": 6,
                    "image_prompt": "macro shot, soft focus background",
                    "video_prompt": "static close-up",
                    "voice_line": "And here's why it matters.",
                },
            ]
        ),
    ),
    (
        frozenset({"chapters", "keywords"}),
        json.dumps(
            {
                "title": "Optimized Title",
                "description": "Optimized description.",
                "tags": ["ai", "tech"],
                "chapters": [{"title": "Intro", "start_seconds": 0}],
                "keywords": ["ai", "on-device"],
            }
        ),
    ),
    (
        frozenset({"rationale"}),
        None,  # filled in dynamically below (echoes the candidate topics back)
    ),
]


def _deterministic_digest(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]


_OUTPUT_SPEC_MARKER = "respond with **only**"


def _fake_completion_for(prompt: str) -> str:
    # Every template embeds request DATA (e.g. a script's sections as JSON,
    # which may itself contain keys like "hook"/"cta") ahead of its own
    # "Respond with **only** ..." output-spec section. Matching keywords
    # against the whole prompt lets one agent's embedded data spuriously
    # trigger another agent's canned response (e.g. a fact-check prompt
    # embedding {"hook": ..., "cta": ...} from the script under review) —
    # so keyword matching is scoped to the output-spec section only, and
    # bullet-list extraction (trend scoring) is scoped to the context
    # section that precedes it.
    lowered = prompt.lower()
    marker_index = lowered.find(_OUTPUT_SPEC_MARKER)
    context_section = prompt if marker_index == -1 else prompt[:marker_index]
    instruction_section = lowered if marker_index == -1 else lowered[marker_index:]

    for keywords, canned in _FAKE_RESPONSES:
        if not all(kw in instruction_section for kw in keywords):
            continue
        if canned is not None:
            return canned
        # trend-scoring: echo each "- <topic>" bullet from the context
        # section back as a scored entry.
        topics = [
            line.removeprefix("- ").strip()
            for line in context_section.splitlines()
            if line.strip().startswith("- ")
        ]
        return json.dumps([{"topic": t, "score": 75.0, "rationale": "fake rationale"} for t in topics])

    return f"[fake] {prompt[:80]}"


class FakeLLMProvider:
    """Deterministic canned output — no network calls. Selected via
    `YTFORGE__MODELS__PROVIDER_SET=fake`, matching ARCHITECTURE.md §10's
    "fakeprovider service" for e2e testing without real credentials."""

    async def complete(self, req: LLMRequest) -> LLMResponse:
        last_user = next((m.content for m in reversed(req.messages) if m.role == "user"), "")
        content = _fake_completion_for(last_user)
        return LLMResponse(
            content=content,
            model=req.model,
            input_tokens=len(last_user.split()),
            output_tokens=len(content.split()),
            latency_ms=1,
            cost_usd=0.0,
        )

    async def stream(self, req: LLMRequest) -> AsyncIterator[LLMChunk]:
        response = await self.complete(req)
        for word in response.content.split(" "):
            yield LLMChunk(delta=word + " ")
        yield LLMChunk(delta="", is_final=True)

    async def embed(self, texts: list[str], model: str) -> list[Vector]:
        return [[float(b) / 255 for b in hashlib.sha256(t.encode()).digest()[:8]] for t in texts]

    async def health_check(self) -> None:
        return None


class FakeImageProvider:
    async def generate(self, req: ImageRequest) -> list[ImageAsset]:
        return [
            ImageAsset(
                object_key=f"fake/image/{_deterministic_digest(req.prompt, str(i))}.png",
                content_type="image/png",
                model=req.model,
                latency_ms=1,
                cost_usd=0.0,
            )
            for i in range(req.count)
        ]

    async def health_check(self) -> None:
        return None


class FakeVideoProvider:
    async def generate(self, req: VideoRequest) -> VideoJob:
        return VideoJob(provider_job_id=_deterministic_digest(req.prompt), model=req.model)

    async def poll(self, job: VideoJob) -> VideoJobStatus:
        return VideoJobStatus(
            state=VideoJobState.COMPLETED,
            object_key=f"fake/video/{job.provider_job_id}.mp4",
            latency_ms=1,
            cost_usd=0.0,
        )

    async def health_check(self) -> None:
        return None


class FakeTTSProvider:
    async def synthesize(self, req: TTSRequest) -> AudioAsset:
        words = req.text.split()
        timestamps: list[WordTimestamp] = []
        t = 0.0
        for word in words:
            duration = max(0.2, len(word) * 0.05)
            timestamps.append(WordTimestamp(word=word, start=t, end=t + duration))
            t += duration
        return AudioAsset(
            object_key=f"fake/audio/{_deterministic_digest(req.text, req.voice_id)}.wav",
            content_type="audio/wav",
            duration_seconds=t,
            model=req.model,
            latency_ms=1,
            word_timestamps=timestamps,
            cost_usd=0.0,
        )

    async def clone_voice(self, req: VoiceCloneRequest) -> ClonedVoice:
        return ClonedVoice(provider_voice_id=f"fake-voice-{_deterministic_digest(req.name)}", model="fake")

    async def health_check(self) -> None:
        return None


class FakeSearchProvider:
    """No real `SearchProvider` adapter exists yet — ARCHITECTURE.md §4.2's
    adapter list covers LLM/image/video/TTS/music only, not web search, so
    `WebSearchTool` is fake-backed unconditionally for now rather than
    half-built against an unspecified vendor. A real adapter (Brave
    Search, Serper, …) is a small follow-up, not a Phase-6 gap in the
    documented provider set."""

    async def search(self, query: SearchQuery) -> list[SearchResult]:
        return [
            SearchResult(
                title=f"[fake result {i + 1}] {query.query}",
                url=f"https://example.com/search?q={query.query.replace(' ', '+')}&r={i}",
                snippet=f"Placeholder snippet about {query.query}.",
            )
            for i in range(min(query.max_results, 3))
        ]


class FakeMusicProvider:
    async def generate(self, req: MusicRequest) -> MusicAsset:
        return MusicAsset(
            object_key=f"fake/music/{_deterministic_digest(req.prompt)}.mp3",
            content_type="audio/mpeg",
            duration_seconds=req.duration_seconds,
            model=req.model,
            latency_ms=1,
            cost_usd=0.0,
        )

    async def health_check(self) -> None:
        return None
