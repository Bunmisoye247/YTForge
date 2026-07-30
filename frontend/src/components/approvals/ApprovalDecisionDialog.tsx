"use client";

import { useState } from "react";
import { Dialog } from "@/components/ui/Dialog";
import { Button } from "@/components/ui/Button";
import { Label, Textarea } from "@/components/ui/Input";
import { useDecideApproval } from "@/lib/hooks/use-approvals";
import { useToast } from "@/lib/stores/toast-store";
import { ApprovalStatus } from "@/types/enums";
import type { ApprovalRead } from "@/lib/api/schemas/approvals";

type Props = {
  approval: ApprovalRead | null;
  onClose: () => void;
};

export function ApprovalDecisionDialog({ approval, onClose }: Props) {
  const [note, setNote] = useState("");
  const decide = useDecideApproval();
  const toast = useToast();

  if (!approval) return null;

  const handleDecision = (status: typeof ApprovalStatus.APPROVED | typeof ApprovalStatus.REJECTED) => {
    decide.mutate(
      { approvalId: approval.id, data: { status, note: note || null } },
      {
        onSuccess: () => {
          toast.success(status === ApprovalStatus.APPROVED ? "Approval granted" : "Approval rejected");
          setNote("");
          onClose();
        },
        onError: () => toast.error("Failed to record decision"),
      },
    );
  };

  return (
    <Dialog open onClose={onClose} title={`Decide: ${approval.kind}`}>
      <div className="flex flex-col gap-3">
        <p className="text-sm text-(--color-text-muted) dark:text-(--color-text-muted-dark)">
          Requested {approval.requested_by_user_id ? `by user ${approval.requested_by_user_id}` : ""}
        </p>
        <div>
          <Label htmlFor="decision-note">Note (optional)</Label>
          <Textarea id="decision-note" value={note} onChange={(e) => setNote(e.target.value)} />
        </div>
        <div className="flex justify-end gap-2">
          <Button
            variant="danger"
            isLoading={decide.isPending}
            onClick={() => handleDecision(ApprovalStatus.REJECTED)}
          >
            Reject
          </Button>
          <Button isLoading={decide.isPending} onClick={() => handleDecision(ApprovalStatus.APPROVED)}>
            Approve
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
