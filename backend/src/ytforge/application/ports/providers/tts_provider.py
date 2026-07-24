from __future__ import annotations

from typing import Protocol

from ytforge.application.dto.tts import AudioAsset, ClonedVoice, TTSRequest, VoiceCloneRequest


class TTSProvider(Protocol):
    async def synthesize(self, req: TTSRequest) -> AudioAsset: ...
    async def clone_voice(self, req: VoiceCloneRequest) -> ClonedVoice: ...
