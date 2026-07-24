"use client";

import type { ReactNode } from "react";
import type { PageResponse } from "@/lib/api/schemas/pagination";
import { Button } from "@/components/ui/Button";

export type Column<T> = {
  header: string;
  cell: (row: T) => ReactNode;
  className?: string;
};

type TableProps<T> = {
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T) => string;
  emptyLabel?: string;
  isLoading?: boolean;
};

export function Table<T>({ columns, rows, rowKey, emptyLabel = "Nothing here yet.", isLoading }: TableProps<T>) {
  return (
    <div className="overflow-x-auto rounded-lg border border-[--color-border] dark:border-[--color-border-dark]">
      <table className="w-full min-w-max text-left text-sm">
        <thead className="border-b border-[--color-border] bg-[--color-surface] dark:border-[--color-border-dark] dark:bg-[--color-surface-dark]">
          <tr>
            {columns.map((col) => (
              <th key={col.header} className={`px-3 py-2 font-medium text-[--color-text-muted] dark:text-[--color-text-muted-dark] ${col.className ?? ""}`}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {isLoading ? (
            <tr>
              <td colSpan={columns.length} className="px-3 py-6 text-center text-[--color-text-muted] dark:text-[--color-text-muted-dark]">
                Loading…
              </td>
            </tr>
          ) : rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-3 py-6 text-center text-[--color-text-muted] dark:text-[--color-text-muted-dark]">
                {emptyLabel}
              </td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr key={rowKey(row)} className="border-b border-[--color-border] last:border-0 dark:border-[--color-border-dark]">
                {columns.map((col) => (
                  <td key={col.header} className={`px-3 py-2 ${col.className ?? ""}`}>
                    {col.cell(row)}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

type PaginationProps = {
  page: PageResponse<unknown> | undefined;
  onOffsetChange: (offset: number) => void;
};

export function TablePagination({ page, onOffsetChange }: PaginationProps) {
  if (!page || page.total <= page.limit) return null;

  const start = page.offset + 1;
  const end = Math.min(page.offset + page.limit, page.total);

  return (
    <div className="mt-3 flex items-center justify-between text-sm text-[--color-text-muted] dark:text-[--color-text-muted-dark]">
      <span>
        {start}–{end} of {page.total}
      </span>
      <div className="flex gap-2">
        <Button
          variant="secondary"
          size="sm"
          disabled={page.offset === 0}
          onClick={() => onOffsetChange(Math.max(0, page.offset - page.limit))}
        >
          Previous
        </Button>
        <Button
          variant="secondary"
          size="sm"
          disabled={end >= page.total}
          onClick={() => onOffsetChange(page.offset + page.limit)}
        >
          Next
        </Button>
      </div>
    </div>
  );
}
