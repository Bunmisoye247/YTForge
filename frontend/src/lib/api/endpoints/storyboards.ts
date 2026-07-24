import { apiClient } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import {
  sceneReadSchema,
  storyboardReadSchema,
  type SceneCreateRequest,
  type SceneRead,
  type StoryboardCreateRequest,
  type StoryboardRead,
  type StoryboardStatusUpdateRequest,
} from "@/lib/api/schemas/storyboards";
import { z } from "zod";

export function createStoryboard(
  projectId: string,
  data: StoryboardCreateRequest,
): Promise<StoryboardRead> {
  return apiClient.post(`/projects/${projectId}/storyboards`, storyboardReadSchema, data);
}

/** Returns null if the project has no storyboard yet, rather than throwing. */
export async function getStoryboardForProject(projectId: string): Promise<StoryboardRead | null> {
  try {
    return await apiClient.get(`/projects/${projectId}/storyboard`, storyboardReadSchema);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

export function listScenes(storyboardId: string): Promise<SceneRead[]> {
  return apiClient.get(`/storyboards/${storyboardId}/scenes`, z.array(sceneReadSchema));
}

export function updateStoryboardStatus(
  storyboardId: string,
  data: StoryboardStatusUpdateRequest,
): Promise<StoryboardRead> {
  return apiClient.post(`/storyboards/${storyboardId}/status`, storyboardReadSchema, data);
}

export function addScene(storyboardId: string, data: SceneCreateRequest): Promise<SceneRead> {
  return apiClient.post(`/storyboards/${storyboardId}/scenes`, sceneReadSchema, data);
}

export function reorderScenes(storyboardId: string, orderedSceneIds: string[]): Promise<SceneRead[]> {
  return apiClient.post(`/storyboards/${storyboardId}/scenes/reorder`, z.array(sceneReadSchema), {
    ordered_scene_ids: orderedSceneIds,
  });
}
