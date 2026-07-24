from __future__ import annotations

from ytforge.interfaces.agents.analytics import AnalyticsAgent
from ytforge.interfaces.agents.base import Agent, AgentResult, AgentTask
from ytforge.interfaces.agents.context import AgentContext
from ytforge.interfaces.agents.editing import EditingAgent
from ytforge.interfaces.agents.fact_checker import FactCheckerAgent
from ytforge.interfaces.agents.image import ImageAgent
from ytforge.interfaces.agents.publisher import PublisherAgent
from ytforge.interfaces.agents.research import ResearchAgent
from ytforge.interfaces.agents.seo import SEOAgent
from ytforge.interfaces.agents.storyboard import StoryboardAgent
from ytforge.interfaces.agents.trend import TrendAgent
from ytforge.interfaces.agents.video import VideoAgent
from ytforge.interfaces.agents.voice import VoiceAgent
from ytforge.interfaces.agents.writer import WriterAgent

AGENTS: dict[str, Agent] = {
    "analytics": AnalyticsAgent(),
    "editing": EditingAgent(),
    "fact_checker": FactCheckerAgent(),
    "image": ImageAgent(),
    "publisher": PublisherAgent(),
    "research": ResearchAgent(),
    "seo": SEOAgent(),
    "storyboard": StoryboardAgent(),
    "trend": TrendAgent(),
    "video": VideoAgent(),
    "voice": VoiceAgent(),
    "writer": WriterAgent(),
}

__all__ = [
    "AGENTS",
    "Agent",
    "AgentContext",
    "AgentResult",
    "AgentTask",
    "AnalyticsAgent",
    "EditingAgent",
    "FactCheckerAgent",
    "ImageAgent",
    "PublisherAgent",
    "ResearchAgent",
    "SEOAgent",
    "StoryboardAgent",
    "TrendAgent",
    "VideoAgent",
    "VoiceAgent",
    "WriterAgent",
]
