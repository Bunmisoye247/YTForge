from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ytforge.domain.entities import Voiceover, VoiceProfile
from ytforge.infrastructure.db.models import Voiceover as VoiceoverOrm
from ytforge.infrastructure.db.models import VoiceProfile as VoiceProfileOrm


def _profile_to_domain(row: VoiceProfileOrm) -> VoiceProfile:
    return VoiceProfile(
        id=row.id,
        channel_id=row.channel_id,
        name=row.name,
        provider=row.provider,
        provider_voice_id=row.provider_voice_id,
        status=row.status,
        consent_artifact_object_key=row.consent_artifact_object_key,
        consent_recorded_at=row.consent_recorded_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _voiceover_to_domain(row: VoiceoverOrm) -> Voiceover:
    return Voiceover(
        id=row.id,
        project_id=row.project_id,
        scene_id=row.scene_id,
        voice_profile_id=row.voice_profile_id,
        asset_id=row.asset_id,
        transcript=row.transcript,
        duration_seconds=row.duration_seconds,
        word_timestamps=row.word_timestamps,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyVoiceProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, voice_profile_id: uuid.UUID) -> VoiceProfile | None:
        row = await self._session.get(VoiceProfileOrm, voice_profile_id)
        return _profile_to_domain(row) if row is not None else None

    async def add(self, voice_profile: VoiceProfile) -> None:
        row = VoiceProfileOrm(
            id=voice_profile.id,
            channel_id=voice_profile.channel_id,
            name=voice_profile.name,
            provider=voice_profile.provider,
            provider_voice_id=voice_profile.provider_voice_id,
            status=voice_profile.status,
            consent_artifact_object_key=voice_profile.consent_artifact_object_key,
            consent_recorded_at=voice_profile.consent_recorded_at,
            created_at=voice_profile.created_at,
            updated_at=voice_profile.updated_at,
        )
        self._session.add(row)
        await self._session.flush()

    async def update(self, voice_profile: VoiceProfile) -> None:
        row = await self._session.get(VoiceProfileOrm, voice_profile.id)
        assert row is not None
        row.status = voice_profile.status
        row.updated_at = voice_profile.updated_at
        await self._session.flush()

    async def list_for_channel(self, channel_id: uuid.UUID) -> list[VoiceProfile]:
        stmt = select(VoiceProfileOrm).where(VoiceProfileOrm.channel_id == channel_id)
        rows = await self._session.scalars(stmt)
        return [_profile_to_domain(row) for row in rows]


class SqlAlchemyVoiceoverRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, voiceover: Voiceover) -> None:
        row = VoiceoverOrm(
            id=voiceover.id,
            project_id=voiceover.project_id,
            scene_id=voiceover.scene_id,
            voice_profile_id=voiceover.voice_profile_id,
            asset_id=voiceover.asset_id,
            transcript=voiceover.transcript,
            duration_seconds=voiceover.duration_seconds,
            word_timestamps=voiceover.word_timestamps,
            created_at=voiceover.created_at,
            updated_at=voiceover.updated_at,
        )
        self._session.add(row)
        await self._session.flush()

    async def list_for_project(self, project_id: uuid.UUID) -> list[Voiceover]:
        stmt = select(VoiceoverOrm).where(VoiceoverOrm.project_id == project_id)
        rows = await self._session.scalars(stmt)
        return [_voiceover_to_domain(row) for row in rows]
