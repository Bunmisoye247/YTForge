"use client";

import { useQuery } from "@tanstack/react-query";
import * as settingsApi from "@/lib/api/endpoints/settings";
import { queryKeys } from "@/lib/api/query-keys";

export function useEffectiveSettings() {
  return useQuery({
    queryKey: queryKeys.settings.effective,
    queryFn: settingsApi.getEffectiveSettings,
  });
}
