"use client";

import { useState } from "react";
import { useSelectionStore } from "@/lib/stores/selection-store";
import { useCreateProject, useProjects, useUpdateProjectStatus } from "@/lib/hooks/use-projects";
import { useToast } from "@/lib/stores/toast-store";
import { Table, TablePagination, type Column } from "@/components/ui/Table";
import { StatusBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { Input, Label } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { formatMoney } from "@/lib/utils/format";
import { ProjectStatus } from "@/types/enums";
import type { ProjectRead } from "@/lib/api/schemas/projects";

const NEXT_STATUSES: Record<string, ProjectStatus[]> = {
  [ProjectStatus.IDEA]: [ProjectStatus.IN_PROGRESS, ProjectStatus.ARCHIVED],
  [ProjectStatus.IN_PROGRESS]: [ProjectStatus.IN_REVIEW, ProjectStatus.ARCHIVED],
  [ProjectStatus.IN_REVIEW]: [ProjectStatus.IN_PROGRESS, ProjectStatus.COMPLETED, ProjectStatus.ARCHIVED],
  [ProjectStatus.COMPLETED]: [ProjectStatus.ARCHIVED],
  [ProjectStatus.ARCHIVED]: [],
};

export default function ProjectsPage() {
  const { channelId } = useSelectionStore();
  const [offset, setOffset] = useState(0);
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");

  const { data: page, isLoading } = useProjects(channelId ?? "", { limit: 20, offset });
  const createProject = useCreateProject(channelId ?? "");
  const updateStatus = useUpdateProjectStatus(channelId ?? "");
  const toast = useToast();

  if (!channelId) {
    return <p className="text-sm text-(--color-text-muted) dark:text-(--color-text-muted-dark)">Select a channel to see its projects.</p>;
  }

  const handleCreate = () => {
    createProject.mutate(
      { title },
      {
        onSuccess: () => {
          toast.success("Project created");
          setTitle("");
          setOpen(false);
        },
        onError: () => toast.error("Failed to create project"),
      },
    );
  };

  const columns: Column<ProjectRead>[] = [
    { header: "Title", cell: (p) => p.title },
    { header: "Status", cell: (p) => <StatusBadge status={p.status} /> },
    { header: "Budget", cell: (p) => formatMoney(p.budget_usd) },
    {
      header: "",
      cell: (p) => {
        const options = NEXT_STATUSES[p.status] ?? [];
        if (options.length === 0) return null;
        return (
          <Select
            defaultValue=""
            className="max-w-48"
            onChange={(e) => {
              if (!e.target.value) return;
              updateStatus.mutate(
                { projectId: p.id, data: { status: e.target.value as ProjectStatus } },
                { onError: () => toast.error("Status transition failed") },
              );
              e.target.value = "";
            }}
          >
            <option value="">Move to…</option>
            {options.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </Select>
        );
      },
    },
  ];

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-(--color-text) dark:text-(--color-text-dark)">Projects</h1>
        <Button onClick={() => setOpen(true)}>New project</Button>
      </div>

      <Table columns={columns} rows={page?.items ?? []} rowKey={(p) => p.id} isLoading={isLoading} />
      <TablePagination page={page} onOffsetChange={setOffset} />

      <Dialog open={open} onClose={() => setOpen(false)} title="New project">
        <div className="flex flex-col gap-3">
          <div>
            <Label htmlFor="project-title">Title</Label>
            <Input id="project-title" value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>
          <div className="flex justify-end">
            <Button isLoading={createProject.isPending} disabled={!title} onClick={handleCreate}>
              Create
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
