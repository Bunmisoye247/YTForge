import { z } from "zod";
import { ApprovalKind, ApprovalStatus } from "@/types/enums";

const approvalKindSchema = z.enum([
  ApprovalKind.PUBLISH,
  ApprovalKind.SCHEDULE,
  ApprovalKind.VOICE_CLONING,
  ApprovalKind.ASSET_DELETION,
]);

const approvalStatusSchema = z.enum([
  ApprovalStatus.PENDING,
  ApprovalStatus.APPROVED,
  ApprovalStatus.REJECTED,
]);

export const approvalReadSchema = z.object({
  id: z.string().uuid(),
  kind: approvalKindSchema,
  status: approvalStatusSchema,
  payload: z.record(z.string(), z.unknown()),
  workflow_id: z.string().nullable(),
  requested_by_user_id: z.string().uuid().nullable(),
  decided_by_user_id: z.string().uuid().nullable(),
  decided_at: z.string().nullable(),
  note: z.string().nullable(),
});
export type ApprovalRead = z.infer<typeof approvalReadSchema>;

export type ApprovalRequestRequest = {
  kind: ApprovalKind;
  payload?: Record<string, unknown>;
  workflow_id?: string | null;
};

export type ApprovalDecisionRequest = {
  status: typeof ApprovalStatus.APPROVED | typeof ApprovalStatus.REJECTED;
  note?: string | null;
};
