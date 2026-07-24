// Mirrors the RFC 7807 problem+json shape produced by
// backend/src/ytforge/interfaces/api/middleware/errors.py.
export class ApiError extends Error {
  readonly status: number;
  readonly title: string;

  constructor(status: number, title: string, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.title = title;
  }
}

export type ProblemDetail = {
  type: string;
  title: string;
  status: number;
  detail: string;
};

export function isProblemDetail(value: unknown): value is ProblemDetail {
  return (
    typeof value === "object" &&
    value !== null &&
    "status" in value &&
    "title" in value &&
    "detail" in value
  );
}
