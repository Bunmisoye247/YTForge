import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Table, TablePagination } from "@/components/ui/Table";

describe("Table", () => {
  it("renders rows via the column cell renderers", () => {
    render(
      <Table
        columns={[{ header: "Name", cell: (row: { name: string }) => row.name }]}
        rows={[{ name: "Alpha" }, { name: "Beta" }]}
        rowKey={(row) => row.name}
      />,
    );
    expect(screen.getByText("Alpha")).toBeInTheDocument();
    expect(screen.getByText("Beta")).toBeInTheDocument();
  });

  it("shows the empty label when there are no rows", () => {
    render(<Table columns={[{ header: "Name", cell: () => null }]} rows={[]} rowKey={() => "x"} emptyLabel="Nothing" />);
    expect(screen.getByText("Nothing")).toBeInTheDocument();
  });
});

describe("TablePagination", () => {
  it("hides itself when everything fits on one page", () => {
    const { container } = render(
      <TablePagination page={{ items: [], total: 5, limit: 50, offset: 0 }} onOffsetChange={vi.fn()} />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("advances the offset by the page limit on Next", () => {
    const onOffsetChange = vi.fn();
    render(<TablePagination page={{ items: [], total: 100, limit: 20, offset: 0 }} onOffsetChange={onOffsetChange} />);
    fireEvent.click(screen.getByText("Next"));
    expect(onOffsetChange).toHaveBeenCalledWith(20);
  });

  it("disables Previous on the first page", () => {
    render(<TablePagination page={{ items: [], total: 100, limit: 20, offset: 0 }} onOffsetChange={vi.fn()} />);
    expect(screen.getByText("Previous")).toBeDisabled();
  });
});
