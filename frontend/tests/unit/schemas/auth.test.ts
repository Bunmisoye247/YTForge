import { describe, expect, it } from "vitest";
import { accessTokenResponseSchema, userReadSchema } from "@/lib/api/schemas/auth";

describe("auth schemas", () => {
  it("parses a UserRead matching the backend shape", () => {
    const result = userReadSchema.parse({
      id: "018f1b1e-0000-7000-8000-000000000000",
      email: "founder@ytforge.dev",
      full_name: "Founding Operator",
      is_active: true,
      is_superuser: true,
    });
    expect(result.email).toBe("founder@ytforge.dev");
  });

  it("parses an AccessTokenResponse with nested user", () => {
    const result = accessTokenResponseSchema.parse({
      access_token: "abc.def.ghi",
      token_type: "bearer",
      user: {
        id: "018f1b1e-0000-7000-8000-000000000000",
        email: "founder@ytforge.dev",
        full_name: "Founding Operator",
        is_active: true,
        is_superuser: false,
      },
    });
    expect(result.access_token).toBe("abc.def.ghi");
    expect(result.user.is_superuser).toBe(false);
  });

  it("rejects a malformed email", () => {
    expect(() =>
      userReadSchema.parse({
        id: "018f1b1e-0000-7000-8000-000000000000",
        email: "not-an-email",
        full_name: "X",
        is_active: true,
        is_superuser: false,
      }),
    ).toThrow();
  });
});
