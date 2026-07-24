"use client";

import { ApprovalInbox } from "@/components/approvals/ApprovalInbox";

export default function ApprovalsPage() {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold text-[--color-text] dark:text-[--color-text-dark]">Approvals</h1>
      <ApprovalInbox />
    </div>
  );
}
