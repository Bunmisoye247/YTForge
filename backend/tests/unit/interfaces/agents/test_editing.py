from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from uuid6 import uuid7

from fixtures.agent_context import PROMPTS_DIR, make_test_agent_context
from fixtures.fakes import FakeUnitOfWork
from ytforge.application.dto.editing import EditingRequest, EditingResult
from ytforge.application.use_cases.assets import RegisterAssetInput, register_asset
from ytforge.application.use_cases.channels import CreateChannelInput, create_channel
from ytforge.application.use_cases.projects import CreateProjectInput, create_project
from ytforge.application.use_cases.voice import AddVoiceoverInput, add_voiceover
from ytforge.domain.entities import Scene, Storyboard
from ytforge.domain.enums import AssetType, StoryboardStatus
from ytforge.infrastructure.prompts.jinja_store import FilesystemPromptStore
from ytforge.interfaces.agents.base import AgentTask
from ytforge.interfaces.agents.editing import EditingAgent


async def test_editing_agent_gathers_scene_assets_and_renders() -> None:
    """Real orchestration (gathering each scene's asset into an
    EditingRequest) is exercised here; `render()` runs against
    FakeEditingPipeline (Phase 7) — no ffmpeg binary needed for this test,
    only the fake's deterministic output."""
    uow = FakeUnitOfWork()
    channel = await create_channel(uow, CreateChannelInput(name="C", owner_user_id=uuid7()))
    project = await create_project(uow, CreateProjectInput(channel_id=channel.id, title="X"))

    now = datetime.now(UTC)
    storyboard = Storyboard(
        id=uuid7(), project_id=project.id, script_id=uuid7(), status=StoryboardStatus.READY,
        created_at=now, updated_at=now,
    )
    await uow.storyboards.add(storyboard)
    scene = Scene(
        id=uuid7(), storyboard_id=storyboard.id, sequence_index=0, description="Intro",
        duration_seconds=Decimal("8"), created_at=now, updated_at=now,
    )
    await uow.scenes.add(scene)
    await register_asset(
        uow,
        RegisterAssetInput(
            project_id=project.id, scene_id=scene.id, asset_type=AssetType.CLIP,
            bucket="raw-assets", object_key="clip.mp4",
        ),
    )

    ctx = make_test_agent_context(uow, FilesystemPromptStore(PROMPTS_DIR))
    result = await EditingAgent().run(
        AgentTask(project_id=project.id, payload={"storyboard_id": str(storyboard.id)}), ctx
    )

    assert result.ok, result.error
    assert result.output["render_object_key"].endswith(".mp4")
    assert result.output["render_asset_id"]


async def test_editing_agent_passes_transcript_and_word_timestamps_to_pipeline() -> None:
    """The DTO carries `caption_burn_in` and each scene's transcript/word
    timestamps so the renderer can actually burn captions in — this guards
    against those fields silently getting dropped between the `Voiceover`
    row and `EditingSceneInput` again."""

    class _RecordingEditingPipeline:
        def __init__(self) -> None:
            self.last_request: EditingRequest | None = None

        async def render(self, req: EditingRequest) -> EditingResult:
            self.last_request = req
            return EditingResult(render_object_key=f"{req.project_id}/fake.mp4", duration_seconds=8.0)

    uow = FakeUnitOfWork()
    channel = await create_channel(uow, CreateChannelInput(name="C", owner_user_id=uuid7()))
    project = await create_project(uow, CreateProjectInput(channel_id=channel.id, title="X"))

    now = datetime.now(UTC)
    storyboard = Storyboard(
        id=uuid7(), project_id=project.id, script_id=uuid7(), status=StoryboardStatus.READY,
        created_at=now, updated_at=now,
    )
    await uow.storyboards.add(storyboard)
    scene = Scene(
        id=uuid7(), storyboard_id=storyboard.id, sequence_index=0, description="Intro",
        duration_seconds=Decimal("8"), created_at=now, updated_at=now,
    )
    await uow.scenes.add(scene)
    await register_asset(
        uow,
        RegisterAssetInput(
            project_id=project.id, scene_id=scene.id, asset_type=AssetType.CLIP,
            bucket="raw-assets", object_key="clip.mp4",
        ),
    )
    voice_asset = await register_asset(
        uow,
        RegisterAssetInput(
            project_id=project.id, scene_id=scene.id, asset_type=AssetType.AUDIO,
            bucket="raw-assets", object_key="voice.wav",
        ),
    )
    await add_voiceover(
        uow,
        AddVoiceoverInput(
            project_id=project.id,
            scene_id=scene.id,
            asset_id=voice_asset.id,
            transcript="hello world",
            duration_seconds=Decimal("8"),
            word_timestamps=[{"word": "hello", "start": 0.0, "end": 0.4}],
        ),
    )

    ctx = make_test_agent_context(uow, FilesystemPromptStore(PROMPTS_DIR))
    recording_pipeline = _RecordingEditingPipeline()
    ctx.editing_pipeline = recording_pipeline

    result = await EditingAgent().run(
        AgentTask(project_id=project.id, payload={"storyboard_id": str(storyboard.id)}), ctx
    )

    assert result.ok, result.error
    assert recording_pipeline.last_request is not None
    scene_input = recording_pipeline.last_request.scenes[0]
    assert scene_input.transcript == "hello world"
    assert scene_input.word_timestamps == [{"word": "hello", "start": 0.0, "end": 0.4}]
