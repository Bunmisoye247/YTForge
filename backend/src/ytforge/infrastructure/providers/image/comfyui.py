from __future__ import annotations

import asyncio
import hashlib
import uuid
from typing import Any

import httpx

from ytforge.application.dto.image import ImageAsset, ImageRequest
from ytforge.application.ports.providers.object_storage import ObjectStorage
from ytforge.infrastructure.providers.errors import ProviderRequestError
from ytforge.infrastructure.providers.http_base import ProviderHttpClient
from ytforge.infrastructure.telemetry.provider_metrics import record_provider_call

_POLL_INTERVAL_S = 2.0
_POLL_TIMEOUT_S = 180.0


def _minimal_txt2img_workflow(req: ImageRequest) -> dict[str, Any]:
    """A minimal KSampler/CheckpointLoader/CLIPTextEncode/SaveImage graph —
    ComfyUI's `/prompt` endpoint takes a full node graph, not a flat
    request; real deployments swap this for a saved workflow JSON export.
    # verify node field names against your ComfyUI version."""
    return {
        "3": {
            "class_type": "KSampler",
            "inputs": {"seed": 0, "steps": 20, "cfg": 7.0, "model": ["4", 0], "positive": ["6", 0],
                       "negative": ["7", 0], "latent_image": ["5", 0]},
        },
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": req.model}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": req.width, "height": req.height}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": req.prompt, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": req.negative_prompt or "", "clip": ["4", 1]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0]}},
    }


class ComfyUIProvider:
    """Local ComfyUI server. https://github.com/comfyanonymous/ComfyUI
    Free/local — cost is always 0. `/history` only returns output
    filenames (images saved to ComfyUI's own output directory) — fetched
    via ComfyUI's `/view` endpoint and re-uploaded into our object storage
    rather than left referencing ComfyUI's local filesystem."""

    def __init__(self, base_url: str, storage: ObjectStorage, bucket: str) -> None:
        self._base_url = base_url
        self._client = ProviderHttpClient("comfyui", base_url)
        self._storage = storage
        self._bucket = bucket

    async def generate(self, req: ImageRequest) -> list[ImageAsset]:
        async with record_provider_call("comfyui", "image.generate") as metric:
            client_id = str(uuid.uuid4())
            submit = await self._client.post_json(
                "/prompt", {"prompt": _minimal_txt2img_workflow(req), "client_id": client_id}
            )
            prompt_id = submit["prompt_id"]
            filenames = await self._poll(prompt_id)
            metric.cost_usd = 0.0
            assets = []
            for name in filenames:
                object_key = await self._download_and_store(name)
                assets.append(
                    ImageAsset(object_key=object_key, content_type="image/png", model=req.model, latency_ms=0, cost_usd=0.0)
                )
            return assets

    async def _download_and_store(self, filename: str) -> str:
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            response = await client.get("/view", params={"filename": filename, "type": "output"})
            response.raise_for_status()
            data = response.content
        digest = hashlib.sha256(data).hexdigest()[:16]
        key = f"comfyui/{digest}.png"
        await self._storage.put_object(self._bucket, key, data, "image/png")
        return key

    async def _poll(self, prompt_id: str) -> list[str]:
        elapsed = 0.0
        while elapsed < _POLL_TIMEOUT_S:
            history = await self._client.get_json(f"/history/{prompt_id}")
            entry = history.get(prompt_id)
            if entry and entry.get("outputs"):
                filenames = []
                for output in entry["outputs"].values():
                    for image in output.get("images", []):
                        filenames.append(image["filename"])
                if filenames:
                    return filenames
            await asyncio.sleep(_POLL_INTERVAL_S)
            elapsed += _POLL_INTERVAL_S
        raise ProviderRequestError("comfyui", f"timed out waiting for job {prompt_id}")
