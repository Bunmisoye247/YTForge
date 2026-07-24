import { z } from "zod";
import { TrendSource } from "@/types/enums";

const trendSourceSchema = z.enum([
  TrendSource.GOOGLE_TRENDS,
  TrendSource.YOUTUBE_TRENDING,
  TrendSource.REDDIT,
  TrendSource.HACKER_NEWS,
  TrendSource.X,
  TrendSource.RSS,
  TrendSource.NEWS_API,
]);

export const trendReadSchema = z.object({
  id: z.string().uuid(),
  channel_id: z.string().uuid().nullable(),
  source: trendSourceSchema,
  topic: z.string(),
  url: z.string().nullable(),
  score: z.number(),
  raw_payload: z.record(z.string(), z.unknown()),
});
export type TrendRead = z.infer<typeof trendReadSchema>;

export type TrendCreateRequest = {
  source: TrendSource;
  topic: string;
  url?: string | null;
  score?: number;
  raw_payload?: Record<string, unknown>;
};
