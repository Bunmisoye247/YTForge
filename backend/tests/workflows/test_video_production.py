from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime

import pytest
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from uuid6 import uuid7

from ytforge.application.use_cases.approvals import DecideApprovalInput, decide_approval
from ytforge.application.use_cases.channels import CreateChannelInput, create_channel
from ytforge.application.use_cases.projects import CreateProjectInput, create_project
from ytforge.domain.entities import User, VoiceProfile
from ytforge.domain.enums import ApprovalStatus, VoiceProfileStatus
from ytforge.infrastructure.config.settings import get_settings
from ytforge.infrastructure.db.session import get_engine, get_session_factory
from ytforge.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from ytforge.interfaces.activities import ALL_ACTIVITIES
from ytforge.interfaces.workflows import VideoProductionWorkflow, VideoProductionWorkflowInput

pytestmark = pytest.mark.workflow

_TASK_QUEUE = "test-video-production"
# Matches VideoProductionWorkflow's hardcoded _RENDERER_TASK_QUEUE — the
# editing step routes there specifically, so a second worker needs to be
# listening on it or that activity call never gets picked up.
_RENDERER_TASK_QUEUE = "ytforge-renderer"
_QUERY_POLL_TIMEOUT_S = 90.0


@pytest.fixture(autouse=True)
def _use_fake_providers(monkeypatch: pytest.MonkeyPatch):  # type: ignore[no-untyped-def]
    """Activities each call `get_settings()` independently — forcing the
    fake provider set here means the whole pipeline (LLM, image, video,
    tts, object storage, editing) runs deterministically with no real
    credentials or external servers, while still writing to (and reading
    from) a real local Postgres, same as the Phase 6 CLI smoke test."""
    monkeypatch.setenv("YTFORGE__MODELS__PROVIDER_SET", "fake")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
async def _fresh_engine_per_test():
    """`get_engine()`/`get_session_factory()` are `@lru_cache`'d, so the
    same asyncpg connection pool would otherwise be reused across test
    functions — but each pytest-asyncio test function gets its own event
    loop, and asyncpg connections are bound to the loop they were opened
    on. Reusing a pool from a prior (now-closed) loop fails with
    "'NoneType' object has no attribute 'send'". Dispose and clear the
    cache before and after every test so each gets its own engine bound to
    its own loop."""
    get_engine.cache_clear()
    get_session_factory.cache_clear()
    yield
    await get_engine().dispose()
    get_engine.cache_clear()
    get_session_factory.cache_clear()


async def _seed_project() -> tuple[str, str]:
    uow = SqlAlchemyUnitOfWork(get_session_factory())
    async with uow:
        now = datetime.now(UTC)
        user = User(
            id=uuid7(),
            email=f"{uuid.uuid4().hex}@workflow-test.local",
            hashed_password="x",
            full_name="Workflow Test User",
            is_active=True,
            is_superuser=False,
            token_version=0,
            created_at=now,
            updated_at=now,
        )
        await uow.users.add(user)
        await uow.commit()

        channel = await create_channel(uow, CreateChannelInput(name="Workflow Test Channel", owner_user_id=user.id))
        project = await create_project(uow, CreateProjectInput(channel_id=channel.id, title="Workflow Test Project"))

        await uow.voice_profiles.add(
            VoiceProfile(
                id=uuid7(),
                channel_id=channel.id,
                name="Test Voice",
                provider="elevenlabs",
                provider_voice_id="voice-1",
                status=VoiceProfileStatus.APPROVED,
                consent_artifact_object_key="consent.pdf",
                consent_recorded_at=now,
                created_at=now,
                updated_at=now,
            )
        )
        await uow.commit()
    return str(project.id), str(user.id)


async def _wait_for_pending_approval(handle) -> str:  # type: ignore[no-untyped-def]
    elapsed = 0.0
    while elapsed < _QUERY_POLL_TIMEOUT_S:
        desc = await handle.describe()
        if desc.status is not None and desc.status.name != "RUNNING":
            try:
                result = await handle.result()
            except Exception as exc:
                raise AssertionError(f"workflow ended early with status {desc.status.name}: {exc!r}") from exc
            raise AssertionError(f"workflow ended early with status {desc.status.name}: result={result!r}")
        approval_id = await handle.query(VideoProductionWorkflow.pending_approval_id)
        if approval_id is not None:
            return approval_id  # type: ignore[no-any-return]
        await asyncio.sleep(0.2)
        elapsed += 0.2
    raise TimeoutError("workflow never reached the publish approval gate")


async def _decide_and_signal(handle, approval_id: str, approved: bool, user_id: str) -> None:  # type: ignore[no-untyped-def]
    """Mirrors what `POST /approvals/{id}/decision` will do once the
    router is wired to Temporal: update the DB row (what `PublisherAgent`'s
    own approval check reads) AND signal the waiting workflow — the two
    are separate actions in production, so the test does both explicitly
    rather than relying on the signal alone."""
    uow = SqlAlchemyUnitOfWork(get_session_factory())
    async with uow:
        await decide_approval(
            uow,
            uuid.UUID(approval_id),
            DecideApprovalInput(
                status=ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED,
                decided_by_user_id=uuid.UUID(user_id),
            ),
        )
    await handle.signal(
        VideoProductionWorkflow.approval_decided, args=[approval_id, "approved" if approved else "rejected"]
    )


async def test_video_production_workflow_completes_end_to_end() -> None:
    """Exercises the ENTIRE pipeline for real: research through storyboard,
    parallel image/video/voice generation, editing (FakeEditingPipeline),
    video creation, SEO, the publish approval gate (real DB row + real
    signal), and — now that Phase 8 exists — a real (fake-provider) upload
    via `PublisherAgent`, which transitions the video to UPLOADED and
    records quota usage. This used to stop at an honest Phase-8
    NotImplementedError; now it runs all the way through."""
    try:
        project_id, user_id = await _seed_project()
    except Exception as exc:
        pytest.skip(f"no reachable Postgres for workflow test: {exc}")

    async with (
        await WorkflowEnvironment.start_time_skipping() as env,
        Worker(env.client, task_queue=_TASK_QUEUE, workflows=[VideoProductionWorkflow], activities=ALL_ACTIVITIES),
        Worker(env.client, task_queue=_RENDERER_TASK_QUEUE, activities=ALL_ACTIVITIES),
    ):
        handle = await env.client.start_workflow(
            VideoProductionWorkflow.run,
            VideoProductionWorkflowInput(project_id=project_id, topic="on-device AI", requested_by_user_id=user_id),
            id=f"test-video-production-{uuid.uuid4().hex}",
            task_queue=_TASK_QUEUE,
        )

        approval_id = await _wait_for_pending_approval(handle)
        await _decide_and_signal(handle, approval_id, approved=True, user_id=user_id)

        result = await handle.result()

    assert result.ok, result.error
    assert result.video_id is not None


async def test_video_production_workflow_stops_when_publish_rejected() -> None:
    try:
        project_id, user_id = await _seed_project()
    except Exception as exc:
        pytest.skip(f"no reachable Postgres for workflow test: {exc}")

    async with (
        await WorkflowEnvironment.start_time_skipping() as env,
        Worker(env.client, task_queue=_TASK_QUEUE, workflows=[VideoProductionWorkflow], activities=ALL_ACTIVITIES),
        Worker(env.client, task_queue=_RENDERER_TASK_QUEUE, activities=ALL_ACTIVITIES),
    ):
        handle = await env.client.start_workflow(
            VideoProductionWorkflow.run,
            VideoProductionWorkflowInput(project_id=project_id, topic="on-device AI", requested_by_user_id=user_id),
            id=f"test-video-production-{uuid.uuid4().hex}",
            task_queue=_TASK_QUEUE,
        )

        approval_id = await _wait_for_pending_approval(handle)
        await _decide_and_signal(handle, approval_id, approved=False, user_id=user_id)

        result = await handle.result()

    assert not result.ok
    assert result.error == "publish rejected"
