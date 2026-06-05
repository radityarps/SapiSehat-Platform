"use client";

import { useMemo } from "react";
import { createColumnHelper, flexRender, getCoreRowModel, useReactTable } from "@tanstack/react-table";

type RiskSignal = { jurisdiction_id: string; disease_class: string; signal_count: number; risk_level: string; priority: string; summary_label: string };
type RiskSummary = { agency_user_id: string; rule: Record<string, unknown>; signals: RiskSignal[]; safe_language: Record<string, string> };

const column = createColumnHelper<RiskSignal>();

export async function fetchAgencyRiskSignals(agencyUserId: string): Promise<RiskSummary> {
  const response = await fetch("/api/agency/risk-signals", { headers: { "X-Agency-User-Id": agencyUserId } });
  if (!response.ok) throw new Error("Failed to load risk signals");
  return response.json();
}

export function AgencyRiskSignals({ summary }: { summary: RiskSummary }) {
  const columns = useMemo(() => [
    column.accessor("jurisdiction_id", { header: "Jurisdiction" }),
    column.accessor("disease_class", { header: "Disease risk signal" }),
    column.accessor("signal_count", { header: "Signal count" }),
    column.accessor("risk_level", { header: "Risk level" }),
    column.accessor("priority", { header: "Follow-up priority" }),
    column.accessor("summary_label", { header: "Summary" }),
  ], []);
  const table = useReactTable({ data: summary.signals, columns, getCoreRowModel: getCoreRowModel() });
  return (
    <main>
      <h1>Disease risk signal summary</h1>
      <p>{summary.safe_language.description}</p>
      <p>Rule: 2+ non-healthy reliable or needs-review signals within 7 days.</p>
      <table><thead>{table.getHeaderGroups().map(group => <tr key={group.id}>{group.headers.map(header => <th key={header.id}>{flexRender(header.column.columnDef.header, header.getContext())}</th>)}</tr>)}</thead><tbody>{table.getRowModel().rows.map(row => <tr key={row.id}>{row.getVisibleCells().map(cell => <td key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>)}</tr>)}</tbody></table>
    </main>
  );
}

export default function AgencyRiskSignalsPage() {
  return <AgencyRiskSignals summary={{ agency_user_id: "semarang-officer", rule: {}, signals: [], safe_language: { description: "Possible increased risk signals for follow-up prioritization. Not confirmed outbreak. Not veterinary diagnosis." } }} />;
}
