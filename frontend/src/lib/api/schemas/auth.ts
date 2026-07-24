import { z } from "zod";

export const userReadSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  full_name: z.string(),
  is_active: z.boolean(),
  is_superuser: z.boolean(),
});
export type UserRead = z.infer<typeof userReadSchema>;

export const accessTokenResponseSchema = z.object({
  access_token: z.string(),
  token_type: z.string(),
  user: userReadSchema,
});
export type AccessTokenResponse = z.infer<typeof accessTokenResponseSchema>;

export type RegisterRequest = {
  email: string;
  password: string;
  full_name: string;
};
