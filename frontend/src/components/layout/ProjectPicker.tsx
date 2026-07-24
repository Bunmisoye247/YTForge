"use client";

import { useProjects } from "@/lib/hooks/use-projects";
import { useSelectionStore } from "@/lib/stores/selection-store";
import { Select } from "@/components/ui/Select";

/** Shared project selector for the project-scoped pages (scripts,
 * storyboards, assets, videos, uploads) — reads/writes the same
 * selection-store slot so the choice persists across those pages. */
export function ProjectPicker() {
  const { channelId, projectId, setProjectId } = useSelectionStore();
  const { data: page, isLoading } = useProjects(channelId ?? "", { limit: 100 });

  if (!channelId) return null;
  if (isLoading) return null;

  const projects = page?.items ?? [];
  if (projects.length === 0) {
    return <p className="text-sm text-[--color-text-muted] dark:text-[--color-text-muted-dark]">No projects in this channel yet.</p>;
  }

  return (
    <Select
      value={projectId ?? ""}
      onChange={(e) => setProjectId(e.target.value || null)}
      aria-label="Select project"
      className="max-w-64"
    >
      <option value="">Select a project…</option>
      {projects.map((project) => (
        <option key={project.id} value={project.id}>
          {project.title}
        </option>
      ))}
    </Select>
  );
}
