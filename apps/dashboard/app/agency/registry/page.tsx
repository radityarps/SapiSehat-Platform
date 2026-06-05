"use client";

import { useMemo, useState } from "react";
import { useReactTable, getCoreRowModel, getFilteredRowModel, flexRender, createColumnHelper } from "@tanstack/react-table";

type Farmer = { id: string; name: string; jurisdiction_id: string; consent_tier: string };
type Cattle = { id: string; farmer_id: string; tag: string; sex: string; breed: string; jurisdiction_id: string; status: string };
type Registry = { agency_user_id: string; farmers: Farmer[]; cattle: Cattle[]; filters: Record<string, unknown> };

const farmerColumn = createColumnHelper<Farmer>();
const cattleColumn = createColumnHelper<Cattle>();

export async function fetchAgencyRegistry(agencyUserId: string): Promise<Registry> {
  const response = await fetch("/api/agency/registry", { headers: { "X-Agency-User-Id": agencyUserId } });
  if (!response.ok) throw new Error("Failed to load agency registry");
  return response.json();
}

export function AgencyRegistryTables({ registry }: { registry: Registry }) {
  const [filter, setFilter] = useState("");
  const farmerColumns = useMemo(() => [
    farmerColumn.accessor("name", { header: "Farmer" }),
    farmerColumn.accessor("jurisdiction_id", { header: "Jurisdiction" }),
    farmerColumn.accessor("consent_tier", { header: "Consent" }),
  ], []);
  const cattleColumns = useMemo(() => [
    cattleColumn.accessor("tag", { header: "Cattle tag" }),
    cattleColumn.accessor("breed", { header: "Breed" }),
    cattleColumn.accessor("jurisdiction_id", { header: "Jurisdiction" }),
    cattleColumn.accessor("status", { header: "Status" }),
  ], []);
  const farmerTable = useReactTable({ data: registry.farmers, columns: farmerColumns, state: { globalFilter: filter }, onGlobalFilterChange: setFilter, getCoreRowModel: getCoreRowModel(), getFilteredRowModel: getFilteredRowModel() });
  const cattleTable = useReactTable({ data: registry.cattle, columns: cattleColumns, state: { globalFilter: filter }, onGlobalFilterChange: setFilter, getCoreRowModel: getCoreRowModel(), getFilteredRowModel: getFilteredRowModel() });
  return (
    <main>
      <h1>Agency Registry</h1>
      <label>Filter registry<input aria-label="Filter registry" value={filter} onChange={(event) => setFilter(event.target.value)} /></label>
      <section aria-label="Permitted farmers"><h2>Permitted farmers</h2><RegistryTable table={farmerTable} /></section>
      <section aria-label="Permitted cattle"><h2>Permitted cattle</h2><RegistryTable table={cattleTable} /></section>
    </main>
  );
}

function RegistryTable({ table }: { table: ReturnType<typeof useReactTable<any>> }) {
  return <table><thead>{table.getHeaderGroups().map(group => <tr key={group.id}>{group.headers.map(header => <th key={header.id}>{flexRender(header.column.columnDef.header, header.getContext())}</th>)}</tr>)}</thead><tbody>{table.getRowModel().rows.map(row => <tr key={row.id}>{row.getVisibleCells().map(cell => <td key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>)}</tr>)}</tbody></table>;
}

export default function AgencyRegistryPage() {
  return <AgencyRegistryTables registry={{ agency_user_id: "semarang-officer", farmers: [], cattle: [], filters: {} }} />;
}
