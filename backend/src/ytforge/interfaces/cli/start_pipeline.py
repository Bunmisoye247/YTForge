from __future__ import annotations

import uuid

from ytforge.infrastructure.config.settings import get_settings
from ytforge.infrastructure.temporal.client import build_temporal_client
from ytforge.interfaces.workflows import VideoProductionWorkflow, VideoProductionWorkflowInput


async def start_pipeline(project_id: str, topic: str, requested_by_user_id: str) -> None:
    settings = get_settings()
    client = await build_temporal_client(settings.temporal)

    workflow_id = f"video-production-{project_id}-{uuid.uuid4().hex[:8]}"
    handle = await client.start_workflow(
        VideoProductionWorkflow.run,
        VideoProductionWorkflowInput(
            project_id=project_id, topic=topic, requested_by_user_id=requested_by_user_id
        ),
        id=workflow_id,
        task_queue=settings.temporal.task_queue,
    )
    print(f"started workflow {handle.id} (run {handle.result_run_id})")
