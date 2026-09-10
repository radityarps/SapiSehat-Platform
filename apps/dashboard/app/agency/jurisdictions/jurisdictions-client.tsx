"use client";

import { useAgencySession } from "@/src/features/auth/session-context";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/src/shared/ui/alert-dialog";
import { Badge } from "@/src/shared/ui/badge";
import { Button } from "@/src/shared/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/src/shared/ui/dialog";
import { Input } from "@/src/shared/ui/input";
import { Label } from "@/src/shared/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/src/shared/ui/select";
import { Skeleton } from "@/src/shared/ui/skeleton";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Map, Pencil, Plus, Search, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { useDebouncedValue } from "@/src/shared/hooks/use-debounced-value";

const LEVELS = [
  { value: "province", label: "Province" },
  { value: "regency_city", label: "Regency / City" },
  { value: "district_subdistrict", label: "District / Subdistrict" },
  { value: "village", label: "Village" },
];

const PARENT_LEVELS: Record<string, string | null> = {
  province: null,
  regency_city: "province",
  district_subdistrict: "regency_city",
  village: "district_subdistrict",
};

type Jurisdiction = {
  id: string;
  name: string;
  level: string;
  parent_id: string | null;
  latitude: number | null;
  longitude: number | null;
};

async function request<T>(
  token: string,
  agencyUserId: string,
  path: string,
  init?: RequestInit,
) {
  const response = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      "X-Agency-User-Id": agencyUserId,
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    throw new Error(body?.detail ?? `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export function JurisdictionsClient() {
  const { token, agencyUserId } = useAgencySession();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebouncedValue(search);
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Jurisdiction | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Jurisdiction | null>(null);

  const jurisdictionsQuery = useQuery({
    queryKey: ["jurisdictions-management"],
    queryFn: () =>
      request<{ jurisdictions: Jurisdiction[] }>(
        token,
        agencyUserId,
        "/api/agency/jurisdictions",
      ),
    enabled: Boolean(token && agencyUserId),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) =>
      request<{ deleted: boolean }>(
        token,
        agencyUserId,
        `/api/agency/jurisdictions/${id}`,
        { method: "DELETE" },
      ),
    onSuccess: () => {
      toast.success("Jurisdiction deleted.");
      queryClient.invalidateQueries({ queryKey: ["jurisdictions-management"] });
      setDeleteTarget(null);
    },
    onError: (error) =>
      toast.error(
        error instanceof Error
          ? error.message
          : "Failed to delete jurisdiction.",
      ),
  });

  const jurisdictions = useMemo(() => {
    const items = jurisdictionsQuery.data?.jurisdictions ?? [];
    const needle = debouncedSearch.trim().toLowerCase();
    return needle
      ? items.filter((item) =>
          [item.id, item.name, item.level, item.parent_id].some((value) =>
            value?.toLowerCase().includes(needle),
          ),
        )
      : items;
  }, [debouncedSearch, jurisdictionsQuery.data?.jurisdictions]);

  if (jurisdictionsQuery.isPending) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-9 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }
  if (jurisdictionsQuery.isError) {
    return (
      <div className="rounded-md border border-destructive/50 bg-destructive/5 p-4 text-sm text-destructive">
        Could not load jurisdictions:{" "}
        {(jurisdictionsQuery.error as Error).message}
      </div>
    );
  }

  return (
    <>
      <div className="space-y-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="relative flex-1 sm:max-w-xs">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search jurisdictions..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              className="pl-9"
            />
          </div>
          <Button
            size="sm"
            className="gap-1.5 sm:ml-auto"
            onClick={() => {
              setEditing(null);
              setFormOpen(true);
            }}
          >
            <Plus className="h-3.5 w-3.5" /> Add jurisdiction
          </Button>
        </div>
        <div className="rounded-md border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/40 text-left text-xs font-medium text-muted-foreground">
                <th className="px-4 py-2.5">Jurisdiction</th>
                <th className="px-4 py-2.5">Level</th>
                <th className="px-4 py-2.5">Parent</th>
                <th className="px-4 py-2.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {jurisdictions.length === 0 ? (
                <tr>
                  <td
                    colSpan={4}
                    className="px-4 py-8 text-center text-muted-foreground"
                  >
                    No jurisdictions found.
                  </td>
                </tr>
              ) : (
                jurisdictions.map((item, index) => (
                  <tr
                    key={item.id}
                    className={`border-b last:border-0 transition-colors hover:bg-muted/20 ${index % 2 === 1 ? "bg-muted/5" : ""}`}
                  >
                    <td className="px-4 py-2.5">
                      <div className="flex items-center gap-2">
                        <Map className="h-4 w-4 text-muted-foreground" />
                        <div>
                          <div className="font-medium">{item.name}</div>
                          <div className="font-mono text-xs text-muted-foreground">
                            {item.id}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-2.5">
                      <Badge variant="secondary">
                        {LEVELS.find((level) => level.value === item.level)
                          ?.label ?? item.level}
                      </Badge>
                    </td>
                    <td className="px-4 py-2.5 font-mono text-xs">
                      {item.parent_id ?? "—"}
                    </td>
                    <td className="px-4 py-2.5">
                      <div className="flex justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7"
                          aria-label={`Edit ${item.name}`}
                          onClick={() => {
                            setEditing(item);
                            setFormOpen(true);
                          }}
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 text-destructive hover:text-destructive"
                          aria-label={`Delete ${item.name}`}
                          onClick={() => setDeleteTarget(item)}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
      <JurisdictionFormDialog
        open={formOpen}
        editing={editing}
        jurisdictions={jurisdictionsQuery.data?.jurisdictions ?? []}
        token={token}
        agencyUserId={agencyUserId}
        onClose={() => {
          setFormOpen(false);
          setEditing(null);
        }}
        onSaved={() => {
          setFormOpen(false);
          setEditing(null);
          queryClient.invalidateQueries({
            queryKey: ["jurisdictions-management"],
          });
        }}
      />
      <AlertDialog
        open={Boolean(deleteTarget)}
        onOpenChange={(open) => {
          if (!open) setDeleteTarget(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete jurisdiction?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. Child jurisdictions, users, or
              accounts must be moved first.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={() =>
                deleteTarget && deleteMutation.mutate(deleteTarget.id)
              }
            >
              {deleteMutation.isPending ? "Deleting..." : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

function JurisdictionFormDialog({
  open,
  editing,
  jurisdictions,
  token,
  agencyUserId,
  onClose,
  onSaved,
}: {
  open: boolean;
  editing: Jurisdiction | null;
  jurisdictions: Jurisdiction[];
  token: string;
  agencyUserId: string;
  onClose: () => void;
  onSaved: () => void;
}) {
  const isEdit = Boolean(editing);
  const [id, setId] = useState("");
  const [name, setName] = useState("");
  const [level, setLevel] = useState("province");
  const [parentId, setParentId] = useState("none");
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");

  useEffect(() => {
    if (editing) {
      setId(editing.id);
      setName(editing.name);
      setLevel(editing.level);
      setParentId(editing.parent_id ?? "none");
      setLatitude(editing.latitude?.toString() ?? "");
      setLongitude(editing.longitude?.toString() ?? "");
    } else {
      setId("");
      setName("");
      setLevel("province");
      setParentId("none");
      setLatitude("");
      setLongitude("");
    }
  }, [editing, open]);
  const mutation = useMutation({
    mutationFn: () =>
      request<Jurisdiction>(
        token,
        agencyUserId,
        isEdit
          ? `/api/agency/jurisdictions/${editing?.id}`
          : "/api/agency/jurisdictions",
        {
          method: isEdit ? "PUT" : "POST",
          body: JSON.stringify({
            id,
            name,
            level,
            parent_id: parentId === "none" ? null : parentId,
            latitude: latitude ? Number(latitude) : null,
            longitude: longitude ? Number(longitude) : null,
          }),
        },
      ),
    onSuccess: () => {
      toast.success(isEdit ? "Jurisdiction updated." : "Jurisdiction added.");
      onSaved();
    },
    onError: (error) =>
      toast.error(
        error instanceof Error ? error.message : "Failed to save jurisdiction.",
      ),
  });
  const parentOptions = jurisdictions.filter(
    (item) => item.id !== editing?.id && item.level === PARENT_LEVELS[level],
  );

  return (
    <Dialog
      open={open}
      onOpenChange={(value) => {
        if (!value) onClose();
      }}
    >
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            {isEdit ? `Edit ${editing?.name}` : "New jurisdiction"}
          </DialogTitle>
          <DialogDescription>
            Define an administrative area and its hierarchy.
          </DialogDescription>
        </DialogHeader>
        <form
          className="space-y-3"
          onSubmit={(event) => {
            event.preventDefault();
            mutation.mutate();
          }}
        >
          {!isEdit && (
            <div className="space-y-1.5">
              <Label htmlFor="jurisdiction-id">ID</Label>
              <Input
                id="jurisdiction-id"
                value={id}
                onChange={(event) => setId(event.target.value)}
                placeholder="e.g. east-java"
                required
              />
            </div>
          )}
          <div className="space-y-1.5">
            <Label htmlFor="jurisdiction-name">Name</Label>
            <Input
              id="jurisdiction-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              required
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="jurisdiction-level">Level</Label>
            <Select value={level} onValueChange={setLevel}>
              <SelectTrigger id="jurisdiction-level">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {LEVELS.map((item) => (
                  <SelectItem key={item.value} value={item.value}>
                    {item.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="jurisdiction-parent">Parent</Label>
            <Select value={parentId} onValueChange={setParentId}>
              <SelectTrigger id="jurisdiction-parent">
                <SelectValue placeholder="No parent" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">No parent</SelectItem>
                {parentOptions.map((item) => (
                  <SelectItem key={item.id} value={item.id}>
                    {item.name} ({item.level})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="latitude">Latitude</Label>
              <Input
                id="latitude"
                type="number"
                step="any"
                value={latitude}
                onChange={(event) => setLatitude(event.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="longitude">Longitude</Label>
              <Input
                id="longitude"
                type="number"
                step="any"
                value={longitude}
                onChange={(event) => setLongitude(event.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={mutation.isPending || !name || (!isEdit && !id)}
            >
              {mutation.isPending
                ? "Saving..."
                : isEdit
                  ? "Save changes"
                  : "Create"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
