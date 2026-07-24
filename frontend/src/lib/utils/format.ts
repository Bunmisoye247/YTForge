/** Backend Decimal fields arrive as JSON strings (Pydantic v2 preserves
 * precision this way) — these helpers format them for display. */

export function formatMoney(value: string | null | undefined): string {
  if (value === null || value === undefined) return "—";
  const n = Number(value);
  return Number.isFinite(n)
    ? n.toLocaleString(undefined, { style: "currency", currency: "USD" })
    : "—";
}

export function formatNumber(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  const n = typeof value === "string" ? Number(value) : value;
  return Number.isFinite(n) ? n.toLocaleString() : "—";
}

export function formatDuration(seconds: string | number | null | undefined): string {
  if (seconds === null || seconds === undefined) return "—";
  const n = typeof seconds === "string" ? Number(seconds) : seconds;
  if (!Number.isFinite(n)) return "—";
  const mins = Math.floor(n / 60);
  const secs = Math.round(n % 60);
  return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleString();
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleDateString();
}

export function titleCase(value: string): string {
  return value
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}
