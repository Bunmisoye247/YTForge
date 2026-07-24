import { apiClient } from "@/lib/api/client";
import { effectiveSettingsReadSchema, type EffectiveSettingsRead } from "@/lib/api/schemas/settings";

export function getEffectiveSettings(): Promise<EffectiveSettingsRead> {
  return apiClient.get("/settings", effectiveSettingsReadSchema);
}
