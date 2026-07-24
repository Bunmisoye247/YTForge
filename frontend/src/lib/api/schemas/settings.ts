import { z } from "zod";

export const effectiveSettingsReadSchema = z.object({
  app: z.object({
    name: z.string(),
    env: z.string(),
    debug: z.boolean(),
    cors_origins: z.array(z.string()),
  }),
  database: z.object({
    host: z.string(),
    port: z.number(),
    name: z.string(),
    pool_size: z.number(),
    echo: z.boolean(),
  }),
  security: z.object({
    access_token_ttl_minutes: z.number(),
    refresh_token_ttl_days: z.number(),
  }),
});
export type EffectiveSettingsRead = z.infer<typeof effectiveSettingsReadSchema>;
