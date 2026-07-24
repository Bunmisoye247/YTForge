import { z } from "zod";

export function pageResponseSchema<T extends z.ZodTypeAny>(item: T) {
  return z.object({
    items: z.array(item),
    total: z.number(),
    limit: z.number(),
    offset: z.number(),
  });
}

export type PageResponse<T> = {
  items: T[];
  total: number;
  limit: number;
  offset: number;
};

export type PageParams = {
  limit?: number;
  offset?: number;
};

export function pageParamsToSearch(params?: PageParams): URLSearchParams {
  const search = new URLSearchParams();
  if (params?.limit !== undefined) search.set("limit", String(params.limit));
  if (params?.offset !== undefined) search.set("offset", String(params.offset));
  return search;
}
