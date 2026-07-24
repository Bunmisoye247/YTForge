import { describe, expect, it } from "vitest";
import { projectReadSchema } from "@/lib/api/schemas/projects";

describe("project schema", () => {
  it("parses budget_usd as a string (Pydantic Decimal serializes to string)", () => {
    const result = projectReadSchema.parse({
      id: "018f1b1e-0000-7000-8000-000000000000",
      channel_id: "018f1b1e-0000-7000-8000-000000000001",
      trend_id: null,
      created_by_user_id: null,
      title: "Test project",
      status: "idea",
      budget_usd: "150.00",
    });
    expect(result.budget_usd).toBe("150.00");
  });

  it("accepts a null budget", () => {
    const result = projectReadSchema.parse({
      id: "018f1b1e-0000-7000-8000-000000000000",
      channel_id: "018f1b1e-0000-7000-8000-000000000001",
      trend_id: null,
      created_by_user_id: null,
      title: "Test project",
      status: "idea",
      budget_usd: null,
    });
    expect(result.budget_usd).toBeNull();
  });

  it("rejects an unknown status", () => {
    expect(() =>
      projectReadSchema.parse({
        id: "018f1b1e-0000-7000-8000-000000000000",
        channel_id: "018f1b1e-0000-7000-8000-000000000001",
        trend_id: null,
        created_by_user_id: null,
        title: "Test project",
        status: "not_a_real_status",
        budget_usd: null,
      }),
    ).toThrow();
  });
});
