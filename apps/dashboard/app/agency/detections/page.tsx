"use client";

import { useMemo, useState } from "react";
import { createColumnHelper, flexRender, getCoreRowModel, getFilteredRowModel, useReactTable } from "@tanstack/react-table";

type Detection = {
  id: string;
  disease_class: string;
  confidence: number;
  reliability: string;
  conflict_status: string;
  evidence_breakdown: { image?: unknown; nlp?: unknown };
};
type Monitoring = { agency_user_id: string; detections: Detection[]; safe_language: Record<string, string> };

const column = createColumnHelper<Detection>();

export async function fetchAgencyDetectionMonitoring(agencyUserId: string): Promise<Monitoring> {
  const response = await fetch("/api/agency/detection-monitoring", { headers: { "X-Agency-User-Id": agencyUserId } });
  if (!response.ok) throw new Error("Failed to load detection monitoring");
  return response.json();
}

export function AgencyDetectionMonitoring({ monitoring }: { monitoring: Monitoring }) {
  const [filter, setFilter] = useState("");
  const columns = useMemo(() => [
    column.accessor("disease_class", { header: "Risk signal" }),
    column.accessor("confidence", { header: "Confidence" }),
    column.accessor("reliability", { header: "Reliability" }),
    column.accessor("conflict_status", { header: "Conflict" }),
    column.display({ id: "evidence", header: "Evidence", cell: ({ row }) => <details><summary>Image/NLP breakdown</summary><pre>{JSON.stringify(row.original.evidence_breakdown, null, 2)}</pre></details> }),
  ], []);
  const table = useReactTable({ data: monitoring.detections, columns, state: { globalFilter: filter }, onGlobalFilterChange: setFilter, getCoreRowModel: getCoreRowModel(), getFilteredRowModel: getFilteredRowModel() });
  return (
    <main>
      <h1>Disease risk signals</h1>
      <p>{monitoring.safe_language.description}</p>
      <label>Filter detections<input aria-label="Filter detections" value={filter} onChange={(event) => setFilter(event.target.value)} /></label>
      <table><thead>{table.getHeaderGroups().map(group => <tr key={group.id}>{group.headers.map(header => <th key={header.id}>{flexRender(header.column.columnDef.header, header.getContext())}</th>)}</tr>)}</thead><tbody>{table.getRowModel().rows.map(row => <tr key={row.id}>{row.getVisibleCells().map(cell => <td key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>)}</tr>)}</tbody></table>
    </main>
  );
}

export default function AgencyDetectionsPage() {
  return <AgencyDetectionMonitoring monitoring={{ agency_user_id: "semarang-officer", detections: [], safe_language: { description: "Early detection signals for monitoring and follow-up, not confirmed diagnosis or outbreak declaration." } }} />;
}
