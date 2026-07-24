"use client";

import { useState } from "react";
import { useApprovals } from "@/lib/hooks/use-approvals";
import { Table, TablePagination, type Column } from "@/components/ui/Table";
import { StatusBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Select";
import { ApprovalDecisionDialog } from "@/components/approvals/ApprovalDecisionDialog";
import { formatDateTime } from "@/lib/utils/format";
import { ApprovalStatus } from "@/types/enums";
import type { ApprovalRead } from "@/lib/api/schemas/approvals";

export function ApprovalInbox() {
  const [statusFilter, setStatusFilter] = useState<ApprovalStatus | undefined>(ApprovalStatus.PENDING);
  const [offset, setOffset] = useState(0);
  const [selected, setSelected] = useState<ApprovalRead | null>(null);

  const { data: page, isLoading } = useApprovals(statusFilter, { limit: 20, offset });

  const columns: Column<ApprovalRead>[] = [
    { header: "Kind", cell: (a) => a.kind },
    { header: "Status", cell: (a) => <StatusBadge status={a.status} /> },
    { header: "Decided", cell: (a) => formatDateTime(a.decided_at) },
    {
      header: "",
      cell: (a) =>
        a.status === ApprovalStatus.PENDING ? (
          <Button size="sm" onClick={() => setSelected(a)}>
            Decide
          </Button>
        ) : null,
    },
  ];

  return (
    <div className="flex flex-col gap-3">
      <Select
        value={statusFilter ?? ""}
        onChange={(e) => {
          setStatusFilter((e.target.value || undefined) as ApprovalStatus | undefined);
          setOffset(0);
        }}
        className="max-w-48"
        aria-label="Filter by status"
      >
        <option value="">All statuses</option>
        <option value={ApprovalStatus.PENDING}>Pending</option>
        <option value={ApprovalStatus.APPROVED}>Approved</option>
        <option value={ApprovalStatus.REJECTED}>Rejected</option>
      </Select>

      <Table columns={columns} rows={page?.items ?? []} rowKey={(a) => a.id} isLoading={isLoading} />
      <TablePagination page={page} onOffsetChange={setOffset} />

      <ApprovalDecisionDialog approval={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
