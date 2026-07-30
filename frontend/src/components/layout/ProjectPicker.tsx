"use client";

import { useProjects } from "@/lib/hooks/use-projects";
import { useSelectionStore } from "@/lib/stores/selection-store";
import { Select } from "@/components/ui/Select";
import { SwitcherShell } from "@/components/layout/SwitcherShell";

/** Global project selector, always visible in the topbar next to the
 * channel switcher — reads/writes the same selection-store slot so the
 * choice persists across every project-scoped page. */
export function ProjectPicker() {
  const { channelId, projectId, setProjectId } = useSelectionStore();
  const { data: page, isLoading } = useProjects(channelId ?? "", { limit: 100 });

  if (!channelId || isLoading) return null;

  const projects = page?.items ?? [];
  if (projects.length === 0) {
    return (
      <SwitcherShell label="Project">
        <span className="text-sm text-(--color-text-muted) dark:text-(--color-text-muted-dark)">No projects yet</span>
      </SwitcherShell>
    );
  }

  return (
    <SwitcherShell label="Project">
      <Select bare value={projectId ?? ""} onChange={(e) => setProjectId(e.target.value || null)} aria-label="Select project">
        <option value="">Select a project…</option>
        {projects.map((project) => (
          <option key={project.id} value={project.id}>
            {project.title}
          </option>
        ))}
      </Select>
    </SwitcherShell>
  );
}
