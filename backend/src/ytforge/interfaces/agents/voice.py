from __future__ import annotations

import uuid
from decimal import Decimal

from ytforge.application.common.errors import NotFoundError
from ytforge.application.dto.tts import TTSRequest
from ytforge.application.use_cases.assets import (
    RegisterAssetInput,
    mark_asset_ready,
    register_asset,
)
from ytforge.application.use_cases.voice import AddVoiceoverInput, add_voiceover
from ytforge.domain.enums import AssetType, VoiceProfileStatus
from ytforge.interfaces.agents.base import AgentResult, AgentTask
from ytforge.interfaces.agents.context import AgentContext
from ytforge.interfaces.agents.support import run_llm_step


class VoiceAgent:
    """Consumes scenes with a `voice_line`, produces narration audio +
    word timestamps (ARCHITECTURE.md §3). `task.payload["scene_ids"]`
    selects which scenes; `task.payload["voice_profile_id"]` picks the
    voice, falling back to the project channel's first approved profile."""

    name = "voice"

    async def run(self, task: AgentTask, ctx: AgentContext) -> AgentResult:
        scene_ids: list[str] = task.payload.get("scene_ids", [])
        if not scene_ids:
            return AgentResult.failure("voice agent requires payload['scene_ids']")

        project = await ctx.uow.projects.get_by_id(task.project_id)
        if project is None:
            raise NotFoundError("Project", task.project_id)

        voice_profile_id = task.payload.get("voice_profile_id")
        if voice_profile_id:
            voice_profile = await ctx.uow.voice_profiles.get_by_id(uuid.UUID(voice_profile_id))
        else:
            profiles = await ctx.uow.voice_profiles.list_for_channel(project.channel_id)
            approved = [p for p in profiles if p.status == VoiceProfileStatus.APPROVED]
            voice_profile = approved[0] if approved else None
        if voice_profile is None:
            return AgentResult.failure("no approved voice profile available for this channel")

        voiceover_ids = []
        asset_ids = []
        for scene_id_raw in scene_ids:
            scene = await ctx.uow.scenes.get_by_id(uuid.UUID(scene_id_raw))
            if scene is None or not scene.voice_line:
                continue

            _rendered, direction = await run_llm_step(
                ctx,
                agent="voice",
                template_name="direction",
                route_name="voice_direction",
                variables={"voice_line": scene.voice_line, "scene_description": scene.description},
                project_id=task.project_id,
            )

            audio = await ctx.model_router.synthesize_speech(
                "voice_synthesis",
                TTSRequest(text=direction.content, model="", voice_id=voice_profile.provider_voice_id),
            )

            asset = await register_asset(
                ctx.uow,
                RegisterAssetInput(
                    project_id=task.project_id,
                    scene_id=scene.id,
                    asset_type=AssetType.AUDIO,
                    bucket="raw-assets",
                    object_key=audio.object_key,
                    provenance={"model": audio.model, "cost_usd": audio.cost_usd},
                ),
            )
            await mark_asset_ready(ctx.uow, asset.id)
            asset_ids.append(str(asset.id))

            voiceover = await add_voiceover(
                ctx.uow,
                AddVoiceoverInput(
                    project_id=task.project_id,
                    scene_id=scene.id,
                    voice_profile_id=voice_profile.id,
                    asset_id=asset.id,
                    transcript=direction.content,
                    duration_seconds=Decimal(str(audio.duration_seconds)),
                    word_timestamps=[
                        {"word": w.word, "start": w.start, "end": w.end} for w in audio.word_timestamps
                    ],
                ),
            )
            voiceover_ids.append(str(voiceover.id))

        return AgentResult.success(voiceover_ids=voiceover_ids, asset_ids=asset_ids)
