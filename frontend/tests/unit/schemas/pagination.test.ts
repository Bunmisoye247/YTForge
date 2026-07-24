import { describe, expect, it } from "vitest";
import { z } from "zod";
import { pageParamsToSearch, pageResponseSchema } from "@/lib/api/schemas/pagination";

describe("pagination", () => {
  it("parses a PageResponse for an arbitrary item schema", () => {
    const schema = pageResponseSchema(z.object({ id: z.string() }));
    const result = schema.parse({
      items: [{ id: "a" }, { id: "b" }],
      total: 2,
      limit: 50,
      offset: 0,
    });
    expect(result.items).toHaveLength(2);
    expect(result.total).toBe(2);
  });

  it("builds search params only for provided fields", () => {
    expect(pageParamsToSearch(undefined).toString()).toBe("");
    expect(pageParamsToSearch({ limit: 20 }).toString()).toBe("limit=20");
    expect(pageParamsToSearch({ limit: 20, offset: 40 }).toString()).toBe("limit=20&offset=40");
  });
});
