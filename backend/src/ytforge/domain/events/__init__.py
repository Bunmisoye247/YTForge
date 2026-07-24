from __future__ import annotations

from ytforge.domain.events.approvals import ApprovalGranted, ApprovalRejected
from ytforge.domain.events.assets import AssetOrphaned
from ytforge.domain.events.projects import ProjectStatusChanged
from ytforge.domain.events.scripts import ScriptStatusChanged
from ytforge.domain.events.voice import VoiceProfileApproved

__all__ = [
    "ApprovalGranted",
    "ApprovalRejected",
    "AssetOrphaned",
    "ProjectStatusChanged",
    "ScriptStatusChanged",
    "VoiceProfileApproved",
]
