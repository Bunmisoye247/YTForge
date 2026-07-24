from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from uuid6 import uuid7

from fixtures.agent_context import PROMPTS_DIR, make_test_agent_context
from fixtures.fakes import FakeUnitOfWork
from ytforge.application.use_cases.channels import CreateChannelInput, create_channel
from ytforge.application.use_cases.projects import CreateProjectInput, create_project
from ytforge.domain.entities import Scene, Storyboard, VoiceProfile
from ytforge.domain.enums import StoryboardStatus, VoiceProfileStatus
from ytforge.infrastructure.prompts.jinja_store import FilesystemPromptStore
from ytforge.interfaces.agents.base import AgentTask
from ytforge.interfaces.agents.voice import VoiceAgent


async def test_voice_agent_synthesizes_and_records_voiceover() -> None:
    uow = FakeUnitOfWork()
    channel = await create_channel(uow, CreateChannelInput(name="C", owner_user_id=uuid7()))
    project = await create_project(uow, CreateProjectInput(channel_id=channel.id, title="X"))

    now = datetime.now(UTC)
    voice_profile = VoiceProfile(
        id=uuid7(), channel_id=channel.id, name="Narrator", provider="elevenlabs",
        provider_voice_id="seed-voice", status=VoiceProfileStatus.APPROVED,
        consent_artifact_object_key="consent.pdf", consent_recorded_at=now,
        created_at=now, updated_at=now,
    )
    await uow.voice_profiles.add(voice_profile)

    storyboard = Storyboard(
        id=uuid7(), project_id=project.id, script_id=uuid7(), status=StoryboardStatus.READY,
        created_at=now, updated_at=now,
    )
    await uow.storyboards.add(storyboard)
    scene = Scene(
        id=uuid7(), storyboard_id=storyboard.id, sequence_index=0, description="Intro",
        duration_seconds=Decimal("8"), voice_line="Hello world", created_at=now, updated_at=now,
    )
    await uow.scenes.add(scene)

    ctx = make_test_agent_context(uow, FilesystemPromptStore(PROMPTS_DIR))
    result = await VoiceAgent().run(
        AgentTask(project_id=project.id, payload={"scene_ids": [str(scene.id)]}), ctx
    )

    assert result.ok, result.error
    voiceovers = await uow.voiceovers.list_for_project(project.id)
    assert len(voiceovers) == 1
    assert voiceovers[0].voice_profile_id == voice_profile.id
    assert len(voiceovers[0].word_timestamps) > 0
