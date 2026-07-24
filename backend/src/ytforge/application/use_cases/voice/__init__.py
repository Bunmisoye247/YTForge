from __future__ import annotations

from ytforge.application.use_cases.voice.add_voiceover import AddVoiceoverInput, add_voiceover
from ytforge.application.use_cases.voice.approve_voice_profile import approve_voice_profile
from ytforge.application.use_cases.voice.list_voice_profiles import (
    list_voice_profiles,
    list_voiceovers,
)
from ytforge.application.use_cases.voice.register_voice_profile import (
    RegisterVoiceProfileInput,
    register_voice_profile,
)
from ytforge.application.use_cases.voice.request_voice_clone import (
    RequestVoiceCloneInput,
    request_voice_clone,
)

__all__ = [
    "AddVoiceoverInput",
    "RegisterVoiceProfileInput",
    "RequestVoiceCloneInput",
    "add_voiceover",
    "approve_voice_profile",
    "list_voice_profiles",
    "list_voiceovers",
    "register_voice_profile",
    "request_voice_clone",
]
